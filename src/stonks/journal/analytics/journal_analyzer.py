# =============================================================================
# File: journal_analyzer.py
# Purpose: Orchestrates trading journal analytics and reporting.
# =============================================================================

from collections import defaultdict
from typing import List, Optional

from stonks.journal.analytics.account_analytics import calculate_account_metrics
from stonks.journal.analytics.account_metrics import AccountMetrics
from stonks.journal.analytics.portfolio_analytics import calculate_portfolio_metrics
from stonks.journal.analytics.portfolio_metrics import PortfolioMetrics
from stonks.journal.analytics.position_analytics import calculate_position_metrics
from stonks.journal.journal_repository import JournalRepository


def analyze_account(
    repository: JournalRepository,
    account_id: int,
) -> AccountMetrics:
    """
    Calculate financial metrics for a single trading account.

    Retrieves account-owned journal records and delegates
    calculations to the existing analytics modules.

    Archived accounts remain eligible for historical analysis.

    Args:
        repository:
            Journal repository providing persisted trading records.

        account_id:
            Identifier of the trading account to analyze.

    Returns:
        AccountMetrics:
            Calculated financial metrics for the requested account.

    Raises:
        ValueError:
            If the trading account does not exist.
    """
    account = repository.get_trading_account(account_id)

    if account is None:
        raise ValueError(f"Trading account {account_id} does not exist.")

    positions = repository.get_positions(account_id=account_id)
    executions = repository.get_executions(account_id=account_id)
    transactions = repository.get_account_transactions(account_id=account_id)

    # Group account executions by position to avoid repeated database queries.
    executions_by_position = defaultdict(list)

    for execution in executions:
        executions_by_position[execution.position_id].append(execution)

    position_metrics = [
        calculate_position_metrics(
            position_id=position.position_id,
            executions=executions_by_position[position.position_id],
        )
        for position in positions
    ]

    return calculate_account_metrics(
        transactions=transactions,
        executions=executions,
        positions=position_metrics,
    )


def analyze_portfolio(
    repository: JournalRepository,
    account_ids: Optional[List[int]] = None,
) -> PortfolioMetrics:
    """
    Calculate combined financial metrics across trading accounts.

    By default, includes all trading accounts, including archived
    accounts. Explicit selections are validated and deduplicated.

    Args:
        repository:
            Journal repository providing persisted trading records.

        account_ids:
            Optional trading account identifiers to include.
            None selects every account; an empty list selects none.

    Returns:
        PortfolioMetrics:
            Aggregated financial metrics for the selected accounts.

    Raises:
        ValueError:
            If a selected trading account does not exist.
    """
    if account_ids is None:
        selected_account_ids = [account.account_id for account in repository.get_trading_accounts()]
    else:
        selected_account_ids = list(dict.fromkeys(account_ids))

    account_metrics = [analyze_account(repository, account_id) for account_id in selected_account_ids]

    return calculate_portfolio_metrics(account_metrics)
