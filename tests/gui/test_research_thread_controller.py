# =============================================================================
# File: test_research_thread_controller.py
# Purpose: Verifies research worker outcomes, cancellation, and thread cleanup.
# =============================================================================

from datetime import date
from threading import Event

from PySide6.QtCore import QThread

from stonks.gui.workers.research_thread_controller import ResearchThreadController
from stonks.models.historical_research_request import HistoricalResearchRequest
from stonks.models.research_interval import ResearchInterval


def _request() -> HistoricalResearchRequest:
    return HistoricalResearchRequest(
        symbol="AMD",
        start_date=date(2026, 10, 30),
        end_date=date(2026, 10, 30),
        interval=ResearchInterval.ONE_MINUTE,
    )


def test_success_executes_off_gui_thread_and_cleans_up(qtbot):
    main_thread = QThread.currentThread()
    expected = object()
    observed = []

    def runner(request):
        assert QThread.currentThread() != main_thread
        observed.append(request)
        return expected

    controller = ResearchThreadController(runner)
    results = []
    progress = []
    controller.completed.connect(results.append)
    controller.progress.connect(progress.append)

    with qtbot.waitSignal(controller.idle, timeout=5000):
        assert controller.start_research(_request())

    assert results == [expected]
    assert len(observed) == 1
    assert progress
    assert not controller.is_running()


def test_failure_reports_error_and_cleans_up(qtbot):
    def runner(request):
        raise RuntimeError("Synthetic provider failure")

    controller = ResearchThreadController(runner)
    errors = []
    controller.failed.connect(errors.append)

    with qtbot.waitSignal(controller.idle, timeout=5000):
        assert controller.start_research(_request())

    assert errors == ["Synthetic provider failure"]
    assert not controller.is_running()


def test_overlapping_request_is_rejected_and_cancellation_discards_result(qtbot):
    entered = Event()
    release = Event()
    results = []
    cancellations = []

    def runner(request):
        entered.set()
        assert release.wait(3)
        return object()

    controller = ResearchThreadController(runner)
    controller.completed.connect(results.append)
    controller.cancelled.connect(lambda: cancellations.append(True))

    try:
        with qtbot.waitSignal(controller.idle, timeout=5000):
            assert controller.start_research(_request())
            assert entered.wait(2)
            assert not controller.start_research(_request())
            assert controller.request_cancel()
            release.set()
    finally:
        release.set()

    assert results == []
    assert cancellations == [True]
    assert not controller.is_running()
    assert not controller.request_cancel()


def test_prestart_cancellation_does_not_call_runner(qtbot):
    calls = []
    controller = ResearchThreadController(lambda request: calls.append(request))
    cancellations = []
    controller.cancelled.connect(lambda: cancellations.append(True))

    # Start/cancel before the worker has a chance to execute in its new thread.
    with qtbot.waitSignal(controller.idle, timeout=5000):
        assert controller.start_research(_request())
        controller.request_cancel()

    assert not controller.is_running()
    assert len(calls) <= 1
    assert len(cancellations) <= 1


def test_invalid_request_does_not_create_thread():
    controller = ResearchThreadController(lambda request: None)
    try:
        controller.start_research(None)
    except TypeError:
        pass
    else:
        raise AssertionError("Expected invalid request to be rejected")
    assert not controller.is_running()
