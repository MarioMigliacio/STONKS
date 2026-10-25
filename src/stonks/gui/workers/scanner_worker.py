# =============================================================================
# File: scanner_worker.py
# Purpose: Executes scanner coordination and reports outcomes through Qt signals.
# =============================================================================

import logging
from threading import Event
from typing import Optional

from PySide6.QtCore import QObject, Signal, Slot

from stonks.scanner.scanner_cancelled import ScannerCancelled
from stonks.scanner.scanner_coordinator import ScannerCoordinator

logger = logging.getLogger(__name__)


class ScannerWorker(QObject):
    """
    Execute scanner coordination and report outcomes through Qt signals.

    Attributes:
        m_coordinator:
            Configured scanner coordinator to execute.

        m_cancel_event:
            Shared event for cooperative cancellation.

    Signals:
        completed:
            Emitted with candidates after successful execution.

        failed:
            Emitted with an error message if execution fails.

        cancelled:
            Emitted if the scan is cancelled.

        finished:
            Emitted once after every outcome.
    """

    completed = Signal(list)
    failed = Signal(str)
    cancelled = Signal()
    finished = Signal()

    def __init__(
        self,
        coordinator: ScannerCoordinator,
        cancel_event: Optional[Event] = None,
    ) -> None:
        """
        Initialize the scanner worker.

        Args:
            coordinator: Scanner coordinator responsible for the scan.
            cancel_event: Shared cancellation event; created if not supplied.
        """
        super().__init__()
        self.m_coordinator = coordinator
        self.m_cancel_event = cancel_event if cancel_event is not None else Event()

    def request_cancel(self) -> None:
        """Request cancellation without modifying Qt state."""
        self.m_cancel_event.set()

    @Slot()
    def run(self) -> None:
        """
        Execute the scan and emit an outcome and a final lifecycle signal.

        A cancellation request can only interrupt work at cancellation
        checkpoints; it cannot interrupt an active network request.
        """
        try:
            if self.m_cancel_event.is_set():
                raise ScannerCancelled("Scanner execution cancelled.")

            logger.info("Background scanner execution started")
            candidates = self.m_coordinator.scan()

            if self.m_cancel_event.is_set():
                raise ScannerCancelled("Scanner execution cancelled.")

            self.completed.emit(candidates)
            logger.info(
                "Background scanner execution completed: %d candidate(s)",
                len(candidates),
            )

        except ScannerCancelled:
            logger.info("Background scanner execution cancelled")
            self.cancelled.emit()

        except Exception as exc:
            logger.exception("Background scanner execution failed")
            self.failed.emit(str(exc))

        finally:
            self.finished.emit()
