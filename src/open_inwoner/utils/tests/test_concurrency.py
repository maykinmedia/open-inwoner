import concurrent.futures
import threading
import time
from unittest.mock import call, patch

from django.test import SimpleTestCase

from open_inwoner.utils.concurrency import TimedParallel

# Deadline given to as_completed() in tests that exercise the timeout path.
_TINY_TIMEOUT = 0.01
# Delay before a background timer releases blocked tasks again, comfortably
# after `_TINY_TIMEOUT` has elapsed, so `shutdown(wait=True)` on exiting the
# `with` block doesn't hang for the tasks' full (much larger) safety timeout.
_RELEASE_DELAY = 0.1
# `name` is required so every metric/log event can be attributed to its call
# site; the value itself is irrelevant to most tests below.
_NAME = "test"


class TimedParallelTests(SimpleTestCase):
    def test_as_completed_yields_results_when_nothing_times_out(self):
        with TimedParallel(max_workers=2, name=_NAME) as executor:
            futures = [executor.submit(lambda x: x * 2, i) for i in range(3)]
            result = executor.as_completed(futures, cancel_after=5)
            results = sorted(f.result() for f in result)

        self.assertEqual(results, [0, 2, 4])
        self.assertEqual(result.completed_futures, set(futures))
        self.assertFalse(result.timed_out)
        self.assertEqual(result.timed_out_futures, set())
        self.assertFalse(result.completed_late)
        self.assertEqual(result.completed_late_futures, set())

    def test_completed_and_completed_late_are_tracked_separately(self):
        """
        A single as_completed() call can produce both fates at once: a task
        that's already running when the deadline passes isn't abandoned
        like a not-yet-started one is - it's still awaited and yielded, just
        after the nominal deadline instead of within it.
        """
        started = threading.Event()
        release = threading.Event()
        timer = threading.Timer(_RELEASE_DELAY, release.set)

        def fast_task():
            return "fast"

        def running_task():
            started.set()
            release.wait(timeout=5)
            return "late"

        timer.start()
        try:
            with TimedParallel(max_workers=2, name=_NAME) as executor:
                running = executor.submit(running_task)
                # Guarantee `running_task` already occupies a worker before
                # `fast_task` is submitted to the other one.
                self.assertTrue(started.wait(timeout=5))
                fast = executor.submit(fast_task)

                result = executor.as_completed(
                    [running, fast], cancel_after=_TINY_TIMEOUT
                )
                list(result)
        finally:
            release.set()
            timer.cancel()

        self.assertEqual(result.completed_futures, {fast})
        self.assertEqual(result.completed_late_futures, {running})
        self.assertTrue(result.completed_late)
        self.assertEqual(result.timed_out_futures, set())
        self.assertFalse(result.timed_out)

    def test_queued_futures_are_cancelled_while_running_ones_are_still_yielded(self):
        """
        With a single worker occupied by a still-running task, futures still
        queued behind it must be cancelled - and never actually invoked -
        once the timeout elapses, instead of running one-by-one afterwards.

        The already-running task itself is a different story: it can't be
        cancelled, and ``__exit__``'s ``shutdown(wait=True)`` is going to
        block for it regardless - so ``as_completed()`` should still yield
        it (here, once ``release`` fires) instead of discarding its result,
        and it should *not* end up in ``timed_out_futures``.
        """
        started = threading.Event()
        release = threading.Event()
        timer = threading.Timer(_RELEASE_DELAY, release.set)
        calls: list[str | int] = []

        def first_task():
            calls.append("first")
            started.set()
            release.wait(timeout=5)
            return "first"

        def queued_task(n):
            calls.append(n)
            return n

        timer.start()
        try:
            with TimedParallel(max_workers=1, name=_NAME) as executor:
                first = executor.submit(first_task)
                # Guarantee `first_task` already occupies the only worker
                # before the other two are submitted, so those two are
                # certain to still be queued (not started) once the timeout
                # elapses below.
                self.assertTrue(started.wait(timeout=5))
                queued = [executor.submit(queued_task, i) for i in range(2)]

                # `first` is already running (can't be cancelled) so it's
                # still awaited and yielded; `queued` is cancelled outright,
                # so it should be the only thing that comes out here.
                result = executor.as_completed(
                    [first, *queued], cancel_after=_TINY_TIMEOUT
                )
                (completed,) = list(result)
        finally:
            release.set()
            timer.cancel()

        self.assertIs(completed, first)
        self.assertEqual(completed.result(), "first")
        self.assertEqual(calls, ["first"])
        self.assertFalse(first.cancelled())
        self.assertTrue(all(f.cancelled() for f in queued))
        self.assertEqual(result.completed_futures, set())
        self.assertEqual(result.completed_late_futures, {first})
        self.assertEqual(result.timed_out_futures, set(queued))
        self.assertTrue(result.timed_out)

    def test_future_done_before_the_deadline_check_is_not_dropped(self):
        """
        concurrent.futures.as_completed() checks its deadline before
        draining newly-finished futures on each pass (see its source): a
        future that finished during the previous drain/yield - e.g. because
        a caller's loop body was slow - can be fully done here without
        as_completed() ever having yielded it. That's a completed future,
        not an abandoned one, and must still be collected rather than
        silently dropped by the `future.done(): continue` check.

        Reproduced deterministically by making the *outer* as_completed()
        call (the one given a timeout) raise immediately regardless of
        actual future state, while leaving the *inner* one (awaiting
        already-running futures, called without a timeout) working
        normally - real code tells these apart the same way, since only
        the outer call ever passes a timeout.
        """
        real_as_completed = concurrent.futures.as_completed

        def fake_as_completed(fs, timeout=None):
            if timeout is not None:
                raise concurrent.futures.TimeoutError()
            yield from real_as_completed(fs, timeout=timeout)

        with TimedParallel(max_workers=1, name=_NAME) as executor:
            fast = executor.submit(lambda: "fast")
            # Guarantee `fast` is genuinely done - not just started - before
            # as_completed() ever looks at it.
            self.assertEqual(fast.result(timeout=5), "fast")

            with patch(
                "open_inwoner.utils.concurrency.concurrent.futures.as_completed",
                side_effect=fake_as_completed,
            ):
                result = executor.as_completed([fast], cancel_after=_TINY_TIMEOUT)
                (completed,) = list(result)

        self.assertIs(completed, fast)
        self.assertEqual(completed.result(), "fast")
        self.assertEqual(result.completed_futures, {fast})
        self.assertEqual(result.completed_late_futures, set())
        self.assertEqual(result.timed_out_futures, set())

    def test_future_already_yielded_before_the_deadline_is_not_yielded_again(self):
        """
        `fs` is the full original list passed to as_completed(), not just
        whatever's still outstanding when the deadline hits. A future the
        happy-path loop already yielded stays `.done()` forever afterward,
        so the timeout-handling branch must exclude it explicitly - or it
        gets reclassified as "completed but undrained" and yielded a
        second time, double-processing it at the call site.

        Reproduced deterministically by making the outer as_completed()
        call yield `fast` once (simulating a real happy-path drain) before
        raising TimeoutError, regardless of real timing.
        """
        real_as_completed = concurrent.futures.as_completed

        def fake_as_completed(fs, timeout=None):
            if timeout is not None:
                yield fast
                raise concurrent.futures.TimeoutError()
            yield from real_as_completed(fs, timeout=timeout)

        with TimedParallel(max_workers=1, name=_NAME) as executor:
            fast = executor.submit(lambda: "fast")
            self.assertEqual(fast.result(timeout=5), "fast")

            with patch(
                "open_inwoner.utils.concurrency.concurrent.futures.as_completed",
                side_effect=fake_as_completed,
            ):
                results = list(
                    executor.as_completed([fast], cancel_after=_TINY_TIMEOUT)
                )

        self.assertEqual(results, [fast])

    def test_duplicate_futures_in_fs_are_only_yielded_once(self):
        """
        concurrent.futures.as_completed() deduplicates its input and
        documents that duplicated futures are returned once. The
        classification loop for the timeout path re-scans the original
        `fs`, so it needs the same guarantee - otherwise a future appearing
        twice in `fs` gets classified (and yielded) twice when it's
        discovered as completed-but-undrained.

        Reproduced deterministically: the outer as_completed() call is
        forced to raise TimeoutError without draining anything, so `fast` -
        already done - is discovered only via the classification loop,
        which is given `fs` with `fast` listed twice.
        """

        def fake_as_completed(fs, timeout=None):
            if timeout is not None:
                raise concurrent.futures.TimeoutError()
            return iter(())

        with TimedParallel(max_workers=1, name=_NAME) as executor:
            fast = executor.submit(lambda: "fast")
            self.assertEqual(fast.result(timeout=5), "fast")

            with patch(
                "open_inwoner.utils.concurrency.concurrent.futures.as_completed",
                side_effect=fake_as_completed,
            ):
                results = list(
                    executor.as_completed([fast, fast], cancel_after=_TINY_TIMEOUT)
                )

        self.assertEqual(results, [fast])

    def test_records_completed_metric_for_every_future_when_nothing_times_out(self):
        """
        The metric is recorded on every call, not just ones that hit the
        deadline, so a timeout rate can be computed against a real
        denominator later.
        """
        with patch(
            "open_inwoner.utils.concurrency.timed_parallel_futures"
        ) as mock_counter:
            with TimedParallel(max_workers=2, name=_NAME) as executor:
                futures = [executor.submit(lambda: None) for _ in range(3)]
                list(executor.as_completed(futures, cancel_after=5))

        self.assertEqual(
            mock_counter.add.call_args_list,
            [call(1, {"outcome": "completed", "name": _NAME})] * 3,
        )

    def test_records_cancelled_and_completed_late_metrics_on_timeout(self):
        """
        Hitting the deadline records the cancelled batch (never started) and
        one completed_late event per already-running future as it's awaited,
        each tagged with its own outcome rather than baking counts into
        attribute values.
        """
        started = threading.Event()
        release = threading.Event()
        timer = threading.Timer(_RELEASE_DELAY, release.set)

        def first_task():
            started.set()
            release.wait(timeout=5)
            return "first"

        def queued_task(n):
            return n

        timer.start()
        try:
            with patch(
                "open_inwoner.utils.concurrency.timed_parallel_futures"
            ) as mock_counter:
                with TimedParallel(max_workers=1, name=_NAME) as executor:
                    first = executor.submit(first_task)
                    self.assertTrue(started.wait(timeout=5))
                    queued = [executor.submit(queued_task, i) for i in range(2)]

                    list(
                        executor.as_completed(
                            [first, *queued], cancel_after=_TINY_TIMEOUT
                        )
                    )
        finally:
            release.set()
            timer.cancel()

        self.assertEqual(
            mock_counter.add.call_args_list,
            [
                call(2, {"outcome": "cancelled", "name": _NAME}),
                call(1, {"outcome": "completed_late", "name": _NAME}),
            ],
        )

    def test_records_one_completed_call_metric_when_nothing_times_out(self):
        """
        timed_parallel_futures can't tell you how often a whole call
        finishes clean - a call with 1 of 10 futures cancelled and a call
        with 1 of 1 cancelled contribute identically to the per-future
        counts in aggregate. timed_parallel_calls records one event per
        as_completed() call instead of per future, so that rate can be
        computed directly.
        """
        with patch(
            "open_inwoner.utils.concurrency.timed_parallel_calls"
        ) as mock_counter:
            with TimedParallel(max_workers=2, name=_NAME) as executor:
                futures = [executor.submit(lambda: None) for _ in range(3)]
                list(executor.as_completed(futures, cancel_after=5))

        mock_counter.add.assert_called_once_with(
            1, {"outcome": "completed", "name": _NAME}
        )

    def test_records_one_timed_out_call_metric_on_timeout(self):
        """
        Unlike timed_parallel_futures, this fires exactly once per call
        regardless of how many individual futures were cancelled or
        completed late - it's answering "did this call finish clean",
        not "what happened to each future".
        """
        started = threading.Event()
        release = threading.Event()
        timer = threading.Timer(_RELEASE_DELAY, release.set)

        def first_task():
            started.set()
            release.wait(timeout=5)
            return "first"

        def queued_task(n):
            return n

        timer.start()
        try:
            with patch(
                "open_inwoner.utils.concurrency.timed_parallel_calls"
            ) as mock_counter:
                with TimedParallel(max_workers=1, name=_NAME) as executor:
                    first = executor.submit(first_task)
                    self.assertTrue(started.wait(timeout=5))
                    queued = [executor.submit(queued_task, i) for i in range(2)]

                    list(
                        executor.as_completed(
                            [first, *queued], cancel_after=_TINY_TIMEOUT
                        )
                    )
        finally:
            release.set()
            timer.cancel()

        mock_counter.add.assert_called_once_with(
            1, {"outcome": "timed_out", "name": _NAME}
        )

    def test_result_raises_if_read_before_being_iterated_at_all(self):
        """
        Fate-tracking attributes reflect a specific as_completed() call and
        are only meaningful once that call has actually been iterated to
        completion. Reading them before that - most importantly, before
        iterating at all, e.g. because a caller forgot to consume the
        result - must raise rather than silently returning empty sets that
        are indistinguishable from "nothing timed out".
        """
        with TimedParallel(max_workers=1, name=_NAME) as executor:
            future = executor.submit(lambda: "done")
            result = executor.as_completed([future], cancel_after=5)

            for attr in (
                "completed_futures",
                "completed_late_futures",
                "timed_out_futures",
                "timed_out",
                "completed_late",
            ):
                with self.subTest(attr=attr):
                    with self.assertRaises(RuntimeError):
                        getattr(result, attr)

            list(result)  # exercise the normal, correct usage too

    def test_result_raises_if_read_after_only_partial_iteration(self):
        with TimedParallel(max_workers=3, name=_NAME) as executor:
            futures = [executor.submit(lambda x: x, i) for i in range(3)]
            result = executor.as_completed(futures, cancel_after=5)

            iterator = iter(result)
            next(iterator)  # consume only one of the three

            with self.assertRaises(RuntimeError):
                result.completed_futures

            list(iterator)  # finish the iteration we started above

    def test_result_cannot_be_iterated_twice(self):
        with TimedParallel(max_workers=1, name=_NAME) as executor:
            future = executor.submit(lambda: "done")
            result = executor.as_completed([future], cancel_after=5)
            list(result)

            with self.assertRaises(RuntimeError):
                list(result)

    def test_incomplete_accounting_raises_instead_of_returning_bad_data(self):
        """
        Regression guard for the invariant check itself: if the three
        fate-tracking sets ever failed to cover every future passed to
        as_completed() - exactly the shape of bug this class has already
        had twice (a future silently dropped, then one yielded twice) -
        this must raise loudly instead of quietly exposing an incomplete
        picture as if it were trustworthy.

        `set` instances don't allow monkeypatching individual bound
        methods, so the bug is simulated by swapping in a set subclass
        whose `update()` is a no-op - which is exactly what a version of
        this class missing `self._timed_out.update(not_yet_started)` would
        look like from the outside.
        """

        class NoOpUpdateSet(set):
            def update(self, *args, **kwargs):
                pass

        started = threading.Event()
        release = threading.Event()
        timer = threading.Timer(_RELEASE_DELAY, release.set)

        def running_task():
            started.set()
            release.wait(timeout=5)

        def queued_task():
            return None

        timer.start()
        try:
            with TimedParallel(max_workers=1, name=_NAME) as executor:
                running = executor.submit(running_task)
                self.assertTrue(started.wait(timeout=5))
                queued = executor.submit(queued_task)

                result = executor.as_completed(
                    [running, queued], cancel_after=_TINY_TIMEOUT
                )
                result._timed_out = NoOpUpdateSet()

                with self.assertRaises(RuntimeError):
                    list(result)
        finally:
            release.set()
            timer.cancel()

    def test_exception_from_task_is_raised_via_future_result(self):
        def failing():
            raise ValueError("boom")

        with TimedParallel(max_workers=1, name=_NAME) as executor:
            future = executor.submit(failing)
            (completed,) = list(executor.as_completed([future], cancel_after=5))

        with self.assertRaises(ValueError):
            completed.result()

    def test_exit_does_not_suppress_exceptions_from_the_with_block(self):
        with self.assertRaises(ValueError):
            with TimedParallel(max_workers=1, name=_NAME):
                raise ValueError("boom")

    def test_exit_cancels_futures_never_passed_to_as_completed(self):
        """
        ``as_completed()`` is what populates ``timed_out_futures``, but the
        ``cancel_futures=True`` shutdown in ``__exit__`` is a backstop that
        applies even to futures a caller never awaited at all.
        """
        started = threading.Event()
        release = threading.Event()
        timer = threading.Timer(_RELEASE_DELAY, release.set)

        def blocker():
            started.set()
            release.wait(timeout=5)

        def never_should_run():
            raise AssertionError("must not run: should be cancelled on exit")

        timer.start()
        try:
            with TimedParallel(max_workers=1, name=_NAME) as executor:
                executor.submit(blocker)
                self.assertTrue(started.wait(timeout=5))
                # The sole worker is still stuck in `blocker`, so this stays
                # queued until the `with` block exits and shutdown() drains
                # (and cancels) whatever is still waiting.
                never_run_future = executor.submit(never_should_run)
        finally:
            release.set()
            timer.cancel()

        self.assertTrue(never_run_future.cancelled())

    def test_submit_closes_db_connections_after_task_completes(self):
        with patch(
            "open_inwoner.utils.concurrency.connections.close_all"
        ) as mock_close_all:
            with TimedParallel(max_workers=1, name=_NAME) as executor:
                future = executor.submit(lambda: "done")
                self.assertEqual(future.result(timeout=5), "done")

        mock_close_all.assert_called_once()

    def test_bounds_total_wait_to_already_running_work_not_queued_backlog(self):
        """
        Regression guard for the bug this class fixes: with the plain
        ``zgw_consumers.concurrent.parallel`` context manager, futures still
        queued when the timeout hit would run one after another during
        ``shutdown(wait=True)``, so the total time scaled with the number of
        tasks instead of being bounded by the timeout / already-running work.
        """
        started = threading.Event()
        release = threading.Event()
        timer = threading.Timer(_RELEASE_DELAY, release.set)

        def running_task():
            started.set()
            release.wait(timeout=5)

        def queued_task(n):
            return n

        timer.start()
        start = time.monotonic()
        try:
            with TimedParallel(max_workers=1, name=_NAME) as executor:
                running = executor.submit(running_task)
                # Guarantee the sole worker is occupied by `running_task`
                # before the rest are submitted, so those are certain to
                # still be queued (not started) once the timeout elapses.
                self.assertTrue(started.wait(timeout=5))
                queued = [executor.submit(queued_task, i) for i in range(4)]

                list(
                    executor.as_completed(
                        [running, *queued], cancel_after=_TINY_TIMEOUT
                    )
                )
        finally:
            release.set()
            timer.cancel()
        elapsed = time.monotonic() - start

        # Bounded by the single already-running task's release, not by 4
        # queued tasks running one after another during shutdown.
        self.assertLess(elapsed, 1)
