# =============================================================================
# File: scanner_thread_controller.py
# Purpose: Owns scanner worker threads and coordinates safe execution cleanup.
# =============================================================================

import logging
from threading import Event
from typing import Callable, Optional

from PySide6.QtCore import QObject, QThread, Signal, Slot

from stonks.gui.workers.scanner_worker import ScannerWorker
from stonks.scanner.scanner_coordinator import ScannerCoordinator
from stonks.scanner.scanner_match_mode import ScannerMatchMode
from stonks.scanner.scanner_strategy import ScannerStrategy

logger = logging.getLogger(__name__)

StrategyFactory = Callable[[Event], ScannerStrategy]


class ScannerThreadController(QObject):
    """
    Own a scanner worker and QThread for one scan at a time.

    The controller must remain alive until its thread has stopped. Callers
    requesting application shutdown should defer window destruction until
    the idle signal is emitted.

    Attributes:
        m_thread:
            Active QThread, or None when idle.

        m_worker:
            Active scanner worker, or None when idle.

        m_cancel_event:
            Cancellation event for the active scan.

    Signals:
        completed:
            Emitted with candidates after a successful scan.

        failed:
            Emitted with a human-readable error message.

        cancelled:
            Emitted when cancellation is acknowledged by the worker.

        running_changed:
            Emitted when the controller enters or leaves a scan.

        idle:
            Emitted after the worker thread has fully stopped.
    """

    completed = Signal(list)
    failed = Signal(str)
    cancelled = Signal()
    running_changed = Signal(bool)
    idle = Signal()

    def __init__(self, parent: Optional[QObject] = None) -> None:
        """
        Initialize an idle controller.

        Args:
            parent: Optional QObject responsible for controller lifetime.
        """
        super().__init__(parent)
        self.m_thread = None  # type: Optional[QThread]
        self.m_worker = None  # type: Optional[ScannerWorker]
        self.m_cancel_event = None  # type: Optional[Event]

    def is_running(self) -> bool:
        """
        Report whether a scan thread is still owned by this controller.

        Returns:
            True until the thread-finished cleanup slot has run.
        """
        return self.m_thread is not None

    def start_scan(
        self,
        strategy_factories: list[StrategyFactory],
        match_mode: ScannerMatchMode = ScannerMatchMode.ANY,
    ) -> bool:
        """
        Start a scan on a dedicated Qt thread.

        Args:
            strategy_factories: Functions that build strategies using the
                same cancellation event as the worker and coordinator.
            match_mode: ANY or ALL combination rule.

        Returns:
            True if a new scan started; False if one is already active.

        Raises:
            ValueError: If no strategies are supplied, or coordinator
                validation fails.
        """
        if self.is_running():
            return False

        if not strategy_factories:
            raise ValueError("At least one scanner strategy is required.")

        event = Event()
        strategies = [factory(event) for factory in strategy_factories]
        coordinator = ScannerCoordinator(
            strategies=strategies,
            match_mode=match_mode,
            cancel_event=event,
        )
        thread = QThread(self)
        worker = ScannerWorker(coordinator, cancel_event=event)
        worker.moveToThread(thread)

        thread.started.connect(worker.run)
        worker.completed.connect(self.completed)
        worker.failed.connect(self.failed)
        worker.cancelled.connect(self.cancelled)
        worker.finished.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(self._on_thread_finished)

        self.m_cancel_event = event
        self.m_thread = thread
        self.m_worker = worker
        thread.start()
        self.running_changed.emit(True)
        return True

    def request_cancel(self) -> bool:
        """
        Signal the active scan to stop at its next cancellation checkpoint.

        Returns:
            True if a scan was active; False if already idle.
        """
        if self.m_cancel_event is None:
            return False
        self.m_cancel_event.set()
        return True

    @Slot()
    def _on_thread_finished(self) -> None:
        """Release worker ownership after the thread has fully exited."""
        thread = self.m_thread
        if thread is None:
            return

        # QThread.finished can precede final thread-local cleanup.
        # wait() ensures the underlying thread has fully exited.
        thread.wait()

        self.m_thread = None
        self.m_worker = None
        self.m_cancel_event = None

        thread.deleteLater()

        self.running_changed.emit(False)
        self.idle.emit()
