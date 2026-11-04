# =============================================================================
# File: research_worker.py
# Purpose: Executes historical research off the GUI thread with cooperative cancellation.
# =============================================================================

import logging
from threading import Event
from typing import Callable

from PySide6.QtCore import QObject, Signal, Slot

from stonks.models.historical_research_request import HistoricalResearchRequest
from stonks.models.historical_research_result import HistoricalResearchResult

logger = logging.getLogger(__name__)
ResearchRunner = Callable[[HistoricalResearchRequest], HistoricalResearchResult]


class ResearchWorker(QObject):
    """Execute one historical research request on a worker thread.

    Attributes:
        m_runner:
            Injected research execution callable.

        m_request:
            Immutable validated research request.

        m_cancel_event:
            Thread-safe cooperative cancellation flag.

    Signals:
        progress:
            Emitted at safe execution checkpoints.

        completed:
            Emitted with the research result on success.

        failed:
            Emitted with a readable error message.

        cancelled:
            Emitted when cancellation is acknowledged.

        finished:
            Emitted once regardless of outcome.
    """

    progress = Signal(str)
    completed = Signal(object)
    failed = Signal(str)
    cancelled = Signal()
    finished = Signal()

    def __init__(
        self,
        runner: ResearchRunner,
        request: HistoricalResearchRequest,
        cancel_event: Event,
    ) -> None:
        super().__init__()
        self.m_runner = runner
        self.m_request = request
        self.m_cancel_event = cancel_event

    @Slot()
    def run(self) -> None:
        """Execute research; cancellation cannot interrupt a blocking provider call."""
        try:
            if self.m_cancel_event.is_set():
                self.cancelled.emit()
                return

            self.progress.emit("Retrieving historical research data…")
            result = self.m_runner(self.m_request)

            if self.m_cancel_event.is_set():
                self.cancelled.emit()
                return

            self.completed.emit(result)
        except Exception as error:
            logger.exception("Historical research execution failed")
            if self.m_cancel_event.is_set():
                self.cancelled.emit()
            else:
                self.failed.emit(str(error))
        finally:
            self.finished.emit()
