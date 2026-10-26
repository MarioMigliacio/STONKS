# Scanner Workspace — STONKS v2.3.0

[← Back to Main README](../README.md) · [Desktop GUI](gui.md)

## Usage

Launch the desktop with `python -m stonks` or `.\scripts\run.ps1`, open **Scanner**, check **Standard Market Scanner**, select **ANY** or **ALL**, and click **Run Scan**. **Cancel** requests cooperative cancellation. API-enabled runs may consume market-data quota.

At v2.3.0, there is only one production scanner strategy, so ANY and ALL yield the same result. Multiple-strategy coordination is implemented and tested for future expansion.

## Results and feedback

- Running: Run and configuration controls disabled; Cancel enabled.
- Completed: replace table with matched candidates and display match count.
- No matches: clear previous table and show an empty-result message.
- Failed: show error; retain previous successful results.
- Cancelled: show cancellation; retain previous successful results.

Results include ticker, price, volume, change %, gap %, RVOL, float and float turnover. Missing enrichment is displayed as unavailable, not zero.

## Architecture

```text
ScannerPage (presentation)
  -> MainWindow (factory selection, status and results)
  -> ScannerThreadController (QThread ownership and cancellation event)
  -> ScannerWorker
  -> ScannerCoordinator (ANY union / ALL intersection)
  -> ExistingScannerStrategy
  -> filters.scan_stocks()
```

The controller allows one scan at a time and emits `idle` only after the worker thread has exited. MainWindow defers closing while a scan is running, requests cancellation, and retries closing on `idle`. Cancellation is cooperative: a pending API request can delay shutdown. Do not forcibly terminate a Qt worker thread.
