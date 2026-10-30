# =============================================================================
# File: cia_thread_controller.py
# Purpose: Owns CIA worker threads and manages safe execution cleanup.
# =============================================================================

from typing import Callable, Optional

from PySide6.QtCore import QObject, QThread, Signal, Slot

from stonks.cia.cia_analysis_service import CiaAnalysisService
from stonks.gui.workers.cia_worker import CiaWorker

CiaServiceFactory = Callable[[], CiaAnalysisService]


class CiaThreadController(QObject):
    """Manage at most one active CIA analysis thread.

    A blocking provider request cannot be interrupted. The application must
    defer window destruction until the idle signal is emitted.

    Attributes:
        m_service_factory:
            Creates the service for each analysis request.

        m_thread:
            Active QThread, or None when idle.

        m_worker:
            Active CiaWorker, or None when idle.

    Signals:
        completed:
            Emitted with the completed CiaAnalysisResult.

        failed:
            Emitted with a readable error message.

        running_changed:
            Emitted when analysis starts or becomes idle.

        idle:
            Emitted after the worker thread has exited.
    """

    completed = Signal(object)
    failed = Signal(str)
    running_changed = Signal(bool)
    idle = Signal()

    def __init__(
        self,
        service_factory: CiaServiceFactory,
        parent: Optional[QObject] = None,
    ) -> None:
        """Initialize the controller with a deferred service factory."""
        super().__init__(parent)
        self.m_service_factory = service_factory
        self.m_thread: Optional[QThread] = None
        self.m_worker: Optional[CiaWorker] = None

    def is_running(self) -> bool:
        """Return True until the thread-finished cleanup slot completes."""
        return self.m_thread is not None

    def start_analysis(self, ticker: str, limit: int = 50) -> bool:
        """Start a background CIA request; return False if already active.

        Validation and service construction occur before creating a QThread.
        Service exceptions from the worker are reported via failed.
        """
        if self.is_running():
            return False

        symbol = ticker.strip().upper()

        if not symbol:
            raise ValueError("Ticker cannot be empty.")
        if limit < 1:
            raise ValueError("News article limit must be positive.")

        service = self.m_service_factory()
        thread = QThread(self)
        worker = CiaWorker(service, symbol, limit)
        worker.moveToThread(thread)

        thread.started.connect(worker.run)
        worker.completed.connect(self.completed)
        worker.failed.connect(self.failed)
        worker.finished.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(self._on_thread_finished)

        self.m_thread = thread
        self.m_worker = worker
        thread.start()
        self.running_changed.emit(True)
        return True

    @Slot()
    def _on_thread_finished(self) -> None:
        """Release ownership only after the underlying thread exits."""
        thread = self.m_thread

        if thread is None:
            return

        thread.wait()
        self.m_thread = None
        self.m_worker = None
        thread.deleteLater()
        self.running_changed.emit(False)
        self.idle.emit()
