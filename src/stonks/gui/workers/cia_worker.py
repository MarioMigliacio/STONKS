# =============================================================================
# File: cia_worker.py
# Purpose: Runs CIA analysis in a Qt worker and emits its outcome.
# =============================================================================

import logging

from PySide6.QtCore import QObject, Signal, Slot

from stonks.cia.cia_analysis_service import CiaAnalysisService

logger = logging.getLogger(__name__)


class CiaWorker(QObject):
    """Execute one CIA analysis outside the GUI thread.

    Attributes:
        m_service:
            Provider-independent CIA analysis service.

        m_ticker:
            Ticker symbol to analyze.

        m_limit:
            Maximum requested article count.

    Signals:
        completed:
            Emitted with the CiaAnalysisResult on success.

        failed:
            Emitted with a readable error message on failure.

        finished:
            Emitted exactly once after either outcome.
    """

    completed = Signal(object)
    failed = Signal(str)
    finished = Signal()

    def __init__(self, service: CiaAnalysisService, ticker: str, limit: int = 50) -> None:
        """Store analysis dependencies without performing network work."""
        super().__init__()
        self.m_service = service
        self.m_ticker = ticker
        self.m_limit = limit

    @Slot()
    def run(self) -> None:
        """Perform analysis and emit one outcome followed by finished."""
        try:
            result = self.m_service.analyze(self.m_ticker, limit=self.m_limit)
            self.completed.emit(result)
        except Exception as exc:
            logger.exception("CIA analysis failed for %s", self.m_ticker)
            self.failed.emit(str(exc))
        finally:
            self.finished.emit()
