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

    Iterate this the same way you would a plain generator - it yields each
    future as it completes. Its fate-tracking attributes
    (``.completed_futures``, ``.completed_late_futures``,
    ``.timed_out_futures``, and the ``.timed_out``/``.completed_late``
    booleans derived from them) are populated *while* iterating, and are
    only meaningful once iteration has run to completion. Reading them
    before that - including never iterating this at all - raises, rather
    than silently returning an empty/incomplete picture that looks
    identical to "nothing timed out". This can only be iterated once.

    Every future passed in ends up in exactly one of three fates:

    - ``.completed_futures``: finished within the budget.
    - ``.completed_late_futures``: was already running when ``cancel_after``
      elapsed (so it couldn't be cancelled - Python threads can't be
      pre-empted) and finished after it. ``TimedParallel.__exit__``'s
      ``shutdown(wait=True)`` blocks for these regardless, so since that
      wait happens either way, this keeps yielding them as they complete
      rather than discarding results callers are already paying to wait for.
    - ``.timed_out_futures``: hadn't started yet when ``cancel_after``
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
        # concurrent.futures.as_completed() deduplicates its input
        # (`fs = set(fs)`, documented: duplicates are returned once). Our
        # own classification below re-scans the original `fs` on a timeout,
        # so it needs the same deduplication - otherwise a future appearing
        # twice could be classified (and yielded) twice.
        # dict.fromkeys() dedupes whilst retaining order, unlike set(),
        # which would also work here but scrambles it.
        self._fs = list(dict.fromkeys(fs))
        self._cancel_after = cancel_after
        self._name = name
        self._completed: set[concurrent.futures.Future] = set()
        self._completed_late: set[concurrent.futures.Future] = set()
        self._timed_out: set[concurrent.futures.Future] = set()
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
            # concurrent.futures.as_completed() checks its deadline before
            # draining newly-finished futures on each pass, so a future
            # that finished during the previous drain/yield (e.g. because
            # our caller's loop body was slow) can be fully done here
            # without as_completed() ever having yielded it - it just
            # hadn't gotten around to it yet. That's still a completed
            # future, not an abandoned one: collect it instead of
            # discarding its result.
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

            self._timed_out.update(not_yet_started)
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
        # three public sets - this is the whole contract this class exists
        # to guarantee. Checking it here, once, covers every code path
        # above at once, rather than trusting each branch got it right in
        # isolation - which is exactly the kind of thing that already went
        # wrong twice before (a future silently dropped, then one yielded
        # twice) despite each branch looking correct on its own.
        accounted_for = self._completed | self._completed_late | self._timed_out
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
    def timed_out_futures(self) -> set[concurrent.futures.Future]:
        self._check_exhausted()
        return self._timed_out

    @property
    def timed_out(self) -> bool:
        return bool(self.timed_out_futures)

    @property
    def completed_late(self) -> bool:
        return bool(self.completed_late_futures)


class TimedParallel:
    """
    Thread pool context manager that bounds the *whole* block to a wall-clock
    budget, not just the ``as_completed`` loop inside it.

    A plain ``concurrent.futures.ThreadPoolExecutor`` used as a context
    manager calls ``shutdown(wait=True)`` on exit, with ``cancel_futures``
    defaulting to ``False``. That means giving
    ``concurrent.futures.as_completed()`` a ``timeout`` only stops
    *iterating* early: once the ``with`` block exits, the executor still
    waits for every submitted task to finish, including ones that hadn't
    even started yet - they get pulled off the queue and run one after
    another, which defeats the point of the timeout.

    ``as_completed()`` here returns an ``AsCompletedResult`` (see its own
    docstring) that guarantees once ``cancel_after`` elapses that any task
    which has not started is cancelled instead of run afterwards, instead of
    running one after another during ``shutdown``. ``__exit__`` applies
    ``cancel_futures=True`` too, as a backstop for anything submitted but
    never passed to ``as_completed()`` at all.

    ``cancel_after`` is given to ``as_completed()``, not to this class: it's
    a property of one wait for one specific set of futures, not of the
    executor or its lifetime, and nothing else here uses it. It's not
    called ``timeout`` (even though it's passed straight through to
    ``concurrent.futures.as_completed(fs, timeout=...)`` internally)
    because it doesn't mean what a plain timeout usually means: work that's
    already running is *not* stopped when it elapses, only work that
    hasn't started yet is cancelled - ``cancel_after`` names that
    consequence directly instead of implying a hard stop this class
    doesn't actually provide. The clock only starts once ``as_completed()``
    is actually iterated, not when this block is entered:
    ``concurrent.futures.as_completed()`` computes its deadline
    (``end_time = timeout + time.monotonic()``) lazily, on the first
    ``next()`` of its generator, since it's a generator function itself. So
    time spent constructing this block or submitting work (before iteration
    starts pulling results) isn't counted against ``cancel_after`` at all -
    only time spent inside that iteration is. In practice this gap is
    usually small, since call sites typically submit everything right
    before iterating, but it isn't zero.

    ``name`` identifies the call site on every debug log line and metric
    event this instance and the results it produces emit. Without it, every
    use of this class anywhere in the app would blend into the same
    aggregate, and there'd be no way to tell "get_raw_zaken times out a lot"
    from "fully_resolve_zaken never does" - only a single blended rate
    across all of them. Unlike ``cancel_after``, ``name`` identifies the
    call site itself rather than one particular wait, so it belongs on this
    longer-lived object rather than on any one ``as_completed()`` call.

    Usage::

        with TimedParallel(max_workers=4, name="get_raw_zaken") as executor:
            futures = {executor.submit(fn, x): x for x in items}
            result = executor.as_completed(futures, cancel_after=5)
            for future in result:
                ...  # future.result()

        if result.timed_out:
            for future in result.timed_out_futures:
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
