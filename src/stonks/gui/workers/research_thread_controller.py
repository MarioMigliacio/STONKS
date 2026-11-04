# =============================================================================
# File: research_thread_controller.py
# Purpose: Owns historical research worker threads and safe shutdown lifecycle.
# =============================================================================

from threading import Event
from typing import Optional

from PySide6.QtCore import QObject, QThread, Signal, Slot

from stonks.gui.workers.research_worker import ResearchRunner, ResearchWorker
from stonks.models.historical_research_request import HistoricalResearchRequest
from stonks.price_action.research_runner import run_historical_research


class ResearchThreadController(QObject):
    """Manage at most one background historical research request.

    Attributes:
        m_runner:
            Research callable injected for deterministic tests.

        m_thread:
            Active QThread, or None when idle.

        m_worker:
            Active research worker, or None when idle.

        m_cancel_event:
            Shared cancellation flag, or None when idle.

    Signals:
        progress:
            Emitted with a progress description.

        completed:
            Emitted with a HistoricalResearchResult.

        failed:
            Emitted with a readable error message.

        cancelled:
            Emitted when cancellation is acknowledged.

        running_changed:
            Emitted on transition into or out of active execution.

        idle:
            Emitted after the underlying thread exits.
    """

    progress = Signal(str)
    completed = Signal(object)
    failed = Signal(str)
    cancelled = Signal()
    running_changed = Signal(bool)
    idle = Signal()

    def __init__(
        self,
        runner: ResearchRunner = run_historical_research,
        parent: Optional[QObject] = None,
    ) -> None:
        super().__init__(parent)
        self.m_runner = runner
        self.m_thread: Optional[QThread] = None
        self.m_worker: Optional[ResearchWorker] = None
        self.m_cancel_event: Optional[Event] = None

    def is_running(self) -> bool:
        """Return True until thread-finished cleanup has completed."""
        return self.m_thread is not None

    def start_research(self, request: HistoricalResearchRequest) -> bool:
        """Launch one request; reject overlapping requests without replacing them."""
        if self.is_running():
            return False
        if not isinstance(request, HistoricalResearchRequest):
            raise TypeError("Expected HistoricalResearchRequest.")

        cancel_event = Event()
        thread = QThread(self)
        worker = ResearchWorker(self.m_runner, request, cancel_event)
        worker.moveToThread(thread)

        thread.started.connect(worker.run)
        worker.progress.connect(self.progress)
        worker.completed.connect(self.completed)
        worker.failed.connect(self.failed)
        worker.cancelled.connect(self.cancelled)
        worker.finished.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(self._on_thread_finished)

        self.m_thread = thread
        self.m_worker = worker
        self.m_cancel_event = cancel_event
        thread.start()
        self.running_changed.emit(True)
        return True

    def request_cancel(self) -> bool:
        """Request cooperative cancellation without terminating a running thread."""
        if self.m_cancel_event is None:
            return False
        self.m_cancel_event.set()
        return True

    @Slot()
    def _on_thread_finished(self) -> None:
        """Release thread ownership only after the worker has stopped."""
        thread = self.m_thread
        if thread is None:
            return

        thread.wait()
        self.m_thread = None
        self.m_worker = None
        self.m_cancel_event = None
        thread.deleteLater()
        self.running_changed.emit(False)
        self.idle.emit()
