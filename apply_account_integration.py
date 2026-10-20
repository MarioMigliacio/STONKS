"""Finish wiring Account Details into an existing STONKS checkout.

Run this script from the repository root after copying the new account modules.
Only updates three existing files; never overwrites the new dialogs or tests.
"""

import sys
from pathlib import Path

ROOT = Path.cwd()
ACCOUNTS = ROOT / "src/stonks/gui/pages/accounts_page.py"
SERVICE = ROOT / "src/stonks/journal/services/journal_service.py"
THEME = ROOT / "src/stonks/gui/styles/theme.py"
DETAILS = ROOT / "src/stonks/gui/pages/account_details_dialog.py"


def insert_once(text, anchor, replacement, already, label):
    """Insert a change exactly once, or retain an already-installed change."""
    if already in text:
        return text
    count = text.count(anchor)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one insertion point; found {count}")
    return text.replace(anchor, replacement, 1)


def build_updates():
    for path in (ACCOUNTS, SERVICE, THEME, DETAILS):
        if not path.is_file():
            raise RuntimeError(f"Missing required file: {path}")

    accounts = ACCOUNTS.read_text(encoding="utf-8")
    import_anchor = "from stonks.gui.pages.create_account_dialog import CreateAccountDialog\n"
    accounts = insert_once(
        accounts,
        import_anchor,
        "from stonks.gui.pages.account_details_dialog import AccountDetailsDialog\n" + import_anchor,
        "from stonks.gui.pages.account_details_dialog import AccountDetailsDialog\n",
        "AccountDetailsDialog import",
    )

    signal_anchor = "        self.m_table.itemSelectionChanged.connect(self._update_action_state)\n"
    accounts = insert_once(
        accounts,
        signal_anchor,
        signal_anchor + "        self.m_table.itemDoubleClicked.connect(self._open_account_details)\n",
        "self.m_table.itemDoubleClicked.connect(self._open_account_details)",
        "AccountsPage double-click signal",
    )

    if "def _open_account_details(" not in accounts:
        accounts = (
            accounts.rstrip()
            + """

    def _open_account_details(self, _item=None) -> None:
        \"\"\"Display details for the selected trading account.\"\"\"
        account_id = self.get_selected_account_id()
        if account_id is None:
            return

        if self.m_repository.get_trading_account(account_id) is None:
            self.refresh_accounts()
            return

        dialog = AccountDetailsDialog(
            account_id=account_id,
            repository=self.m_repository,
            service=self.m_service,
            parent=self,
        )
        dialog.exec()
        self.refresh_accounts()
"""
            + "\n"
        )

    service = SERVICE.read_text(encoding="utf-8")
    update_anchor = (
        "            if existing.account_id != normalized.account_id:\n"
        '                raise ValueError("Cannot move a transaction to another trading account.")\n\n'
        "            return self.m_repository.update_account_transaction(normalized)"
    )
    update_replacement = (
        "            if existing.account_id != normalized.account_id:\n"
        '                raise ValueError("Cannot move a transaction to another trading account.")\n\n'
        "            self._validate_account_ownership(existing.account_id)\n"
        "            return self.m_repository.update_account_transaction(normalized)"
    )
    service = insert_once(
        service,
        update_anchor,
        update_replacement,
        update_replacement,
        "Archived-account transaction update guard",
    )

    delete_anchor = (
        "        with self._transaction():\n"
        "            return self.m_repository.delete_account_transaction(transaction_id)"
    )
    delete_replacement = (
        "        with self._transaction():\n"
        "            existing = self.m_repository.get_account_transaction(transaction_id)\n"
        "            if existing is None:\n"
        "                return False\n"
        "            self._validate_account_ownership(existing.account_id)\n"
        "            return self.m_repository.delete_account_transaction(transaction_id)"
    )
    service = insert_once(
        service,
        delete_anchor,
        delete_replacement,
        delete_replacement,
        "Archived-account transaction delete guard",
    )

    theme = THEME.read_text(encoding="utf-8")
    if "QLabel#accountMetricsNote" not in theme:
        suffix = """
QLabel#accountMetricsNote {
    color: #8190A5;
    font-size: 11px;
    background: transparent;
}

"""
        if not theme.rstrip().endswith('"""'):
            raise RuntimeError("Could not locate final triple quote in theme.py")
        offset = theme.rfind('"""')
        theme = theme[:offset] + suffix + theme[offset:]

    return {ACCOUNTS: accounts, SERVICE: service, THEME: theme}


def main():
    try:
        changes = build_updates()  # validate every anchor before writing any file
        for filename, content in changes.items():
            existing = filename.read_text(encoding="utf-8")
            if existing == content:
                print("Already current:", filename.relative_to(ROOT))
                continue
            filename.write_text(content, encoding="utf-8")
            print("Updated:", filename.relative_to(ROOT))
    except (RuntimeError, OSError) as error:
        print("Integration failed:", error, file=sys.stderr)
        return 1
    print("Integration complete. Run the focused GUI tests and full regression suite.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
