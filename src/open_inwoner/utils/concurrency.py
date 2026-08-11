from __future__ import annotations

import concurrent.futures
import functools
import threading
from collections.abc import Callable, Iterable, Iterator
from typing import ParamSpec, TypeVar

from django.db import connections

import structlog

from open_inwoner.utils.metrics import timed_parallel_calls, timed_parallel_futures

logger = structlog.stdlib.get_logger(__name__)

P = ParamSpec("P")
R = TypeVar("R")


def _wrap_fn(fn: Callable[P, R]) -> Callable[P, R]:
    """
    Close the Django db connections opened in the worker thread once ``fn``
    completes.

    Only closing *old* connections isn't enough when using the CONN_MAX_AGE
    setting: connections aren't old enough yet, but they stay attached to a
    thread-pool thread that other callers can't reuse. So we forcibly close
    everything once the thread's work item is done.

    Vendored from ``zgw_consumers.concurrent.wrap_fn`` to avoid depending on
    an external helper and to keep all the logic in plain-view.
    """

    @functools.wraps(fn)
    def wrapped(*args: P.args, **kwargs: P.kwargs) -> R:
        try:
            return fn(*args, **kwargs)
        finally:
            logger.debug(
                "Closing all database connections",
                thread_id=threading.get_ident(),
            )
            connections.close_all()

    return wrapped


class AsCompletedResult:
    """
    The outcome of one ``TimedParallel.as_completed()`` call.

    This object is iterable, yielding each future as it completes. Its outcome-tracking
    attributes (``.completed_futures``, ``.completed_late_futures``,
    ``.cancelled_futures``, and the ``.has_cancelled_futures``/
    ``.has_completed_late_futures`` booleans derived from them) are populated *while*
    iterating, and are only meaningful once iteration has run to completion.

    Reading them before the iterator has been exhausted - including never iterating this
    at all - raises, rather than silently returning an empty/incomplete picture that
    looks identical to "nothing was cancelled".

    The result can only be iterated once.

    Every future passed in ends up in exactly one of three end-states, accessible
    on the respective properties:

    - ``.completed_futures``: finished within the budget.
    - ``.completed_late_futures``: was already running when ``cancel_after``
      elapsed (so it couldn't be cancelled - Python threads can't be
      pre-empted) and finished after it. ``TimedParallel.__exit__``'s
      ``shutdown(wait=True)`` blocks for these regardless, so since that
      wait happens either way, this keeps yielding them as they complete
      rather than discarding results callers are already paying to wait for.
    - ``.cancelled_futures``: hadn't started yet when ``cancel_after``
      elapsed, and was cancelled outright. Bounding already-running work
      requires a hard timeout on the work itself (e.g. the HTTP client used
      inside the task) - this can only stop work that hasn't started yet.
    """

    def __init__(
        self,
        fs: Iterable[concurrent.futures.Future],
        cancel_after: float | None,
        name: str,
    ):
        # concurrent.futures.as_completed() deduplicates its input, we do the same, to
        # avoid yielding the same future more than once. dict.fromkeys() dedupes whilst
        # retaining order, unlike set(), which would also work here but scrambles it.
        self._fs = list(dict.fromkeys(fs))
        self._cancel_after = cancel_after
        self._name = name
        self._completed: set[concurrent.futures.Future] = set()
        self._completed_late: set[concurrent.futures.Future] = set()
        self._cancelled: set[concurrent.futures.Future] = set()
        self._started = False
        self._exhausted = False

    def __iter__(self) -> Iterator[concurrent.futures.Future]:
        if self._started:
            raise RuntimeError("This as_completed() result was already iterated once")
        self._started = True

        fs = self._fs
        log = logger.bind(
            name=self._name, cancel_after=self._cancel_after, total=len(fs)
        )
        log.debug("TimedParallel.as_completed starting")
        try:
            for future in concurrent.futures.as_completed(
                fs, timeout=self._cancel_after
            ):
                self._completed.add(future)
                timed_parallel_futures.add(
                    1, {"outcome": "completed", "name": self._name}
                )
                yield future
        except concurrent.futures.TimeoutError:
            not_yet_started = []
            already_running = []
            completed_but_undrained = []

            for future in fs:
                # Already yielded by the loop above before it hit the
                # deadline - `fs` is the full original list, not just
                # what's still outstanding, so this must be excluded or
                # it gets processed (and yielded) a second time below.
                if future in self._completed:
                    continue

                # as_completed() checks its deadline before draining
                # newly-finished futures on each pass, so this one can be
                # done here without it ever being yielded - it's completed,
                # not abandoned, so keep its result instead of discarding it.
                if future.done():
                    completed_but_undrained.append(future)
                elif future.cancel():
                    not_yet_started.append(future)
                else:
                    already_running.append(future)
            completed = len(completed_but_undrained)

            log.debug(
                "TimedParallel hit its deadline",
                completed=completed,
                cancelled=len(not_yet_started),
                completed_late=len(already_running),
            )
            timed_parallel_calls.add(1, {"outcome": "timed_out", "name": self._name})
            if not_yet_started:
                timed_parallel_futures.add(
                    len(not_yet_started),
                    {"outcome": "cancelled", "name": self._name},
                )

            self._cancelled.update(not_yet_started)
            for future in completed_but_undrained:
                self._completed.add(future)
                timed_parallel_futures.add(
                    1, {"outcome": "completed", "name": self._name}
                )
                yield future

            for future in concurrent.futures.as_completed(already_running):
                self._completed_late.add(future)
                timed_parallel_futures.add(
                    1, {"outcome": "completed_late", "name": self._name}
                )
                yield future
        else:
            log.debug("TimedParallel.as_completed finished within budget")
            timed_parallel_calls.add(1, {"outcome": "completed", "name": self._name})

        # Every future given to this call must land in exactly one of the
        # three public sets: this is the whole contract this class exists
        # to guarantee. Double-check that this invariant holds.
        accounted_for = self._completed | self._completed_late | self._cancelled
        if accounted_for != set(fs):
            raise RuntimeError(
                "TimedParallel.as_completed() did not account for every "
                f"future: missing={set(fs) - accounted_for!r}, "
                f"unexpected={accounted_for - set(fs)!r}"
            )
        self._exhausted = True

    def _check_exhausted(self) -> None:
        if not self._exhausted:
            raise RuntimeError(
                "as_completed() result accessed before being fully iterated - "
                "iterate it to completion first (e.g. with a plain `for` loop "
                "or `list(...)`)."
            )

    @property
    def completed_futures(self) -> set[concurrent.futures.Future]:
        self._check_exhausted()
        return self._completed

    @property
    def completed_late_futures(self) -> set[concurrent.futures.Future]:
        self._check_exhausted()
        return self._completed_late

    @property
    def cancelled_futures(self) -> set[concurrent.futures.Future]:
        self._check_exhausted()
        return self._cancelled

    @property
    def has_cancelled_futures(self) -> bool:
        return bool(self.cancelled_futures)

    @property
    def has_completed_late_futures(self) -> bool:
        return bool(self.completed_late_futures)


class TimedParallel:
    """
    Thread pool context manager that bounds a batch of parallel calls to a
    wall-clock budget: submit work, then await it via
    ``as_completed(fs, cancel_after=...)``. Once ``cancel_after`` elapses,
    work that hasn't started yet is cancelled outright, rather than run to
    completion during shutdown as a plain
    ``concurrent.futures.ThreadPoolExecutor`` would. Work already running
    when the deadline hits can't be pre-empted, so it's still awaited and
    yielded - see ``AsCompletedResult`` for how each future's outcome is
    tracked.

    ``name`` tags every log line and metric event this instance emits, so
    one call site's rate can be told apart from every other use of this
    class.

    Usage::

        with TimedParallel(max_workers=4, name="get_raw_zaken") as executor:
            futures = {executor.submit(fn, x): x for x in items}
            result = executor.as_completed(futures, cancel_after=5)
            for future in result:
                ...  # future.result()

        if result.has_cancelled_futures:
            for future in result.cancelled_futures:
                item = futures[future]
                ...  # report `item` as skipped/incomplete
    """

    def __init__(self, *, name: str, **kwargs):
        self.name = name
        self._executor = concurrent.futures.ThreadPoolExecutor(**kwargs)

    def submit(
        self, fn: Callable[P, R], /, *args: P.args, **kwargs: P.kwargs
    ) -> concurrent.futures.Future[R]:
        return self._executor.submit(_wrap_fn(fn), *args, **kwargs)

    def as_completed(
        self,
        fs: Iterable[concurrent.futures.Future],
        cancel_after: float | None = None,
    ) -> AsCompletedResult:
        return AsCompletedResult(fs, cancel_after, self.name)

    def __enter__(self) -> TimedParallel:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        logger.debug("Shutting down TimedParallel", name=self.name)
        self._executor.shutdown(wait=True, cancel_futures=True)
        return False
