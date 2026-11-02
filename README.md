# python-job-scheduler

I built this scheduler because I wanted a cron implementation I could actually read end to end — a correct 5-field parser and next-run engine with no daemon, no database, and no third-party dependencies, suitable for embedding in a small service or a test harness.

Components:

- **`CronExpression`** — parses standard 5-field cron (`minute hour day-of-month month day-of-week`) with `*`, lists (`1,15`), ranges (`9-17`), steps (`*/15`, `9-17/2`), and month/weekday names (`JAN`, `MON-FRI`). Day-of-week accepts both `0` and `7` for Sunday, and day-of-month/day-of-week follow classic cron OR semantics when both are restricted. Invalid expressions raise `CronError` with the offending field.
- **Next-run computation** — iterates day-by-day and orders the candidate times inside each matching day, so sparse schedules resolve immediately instead of scanning minute-by-minute. A Feb-29-only schedule correctly jumps 2024 → 2028, and a day-31 schedule correctly skips February.
- **`Scheduler`** — an in-process engine: register named jobs, ask what is due, and call `run_pending(now)`. Each job runs at most once per minute, job exceptions are captured on the job (`last_error`) rather than crashing the host loop, and jobs can be enabled/disabled and removed.

## Usage

```python
from datetime import datetime
from job_scheduler import Scheduler

scheduler = Scheduler()
scheduler.add_job("nightly-report", "0 2 * * *", generate_report)
scheduler.add_job("weekday-standup-ping", "30 9 * * MON-FRI", ping_team)

print(scheduler.next_runs(datetime.now()))
scheduler.run_pending(datetime.now())  # call this from your host loop
```

## Tests

```
python3 -m pytest
```

Last verified locally (Python 3.12, pytest 9.1.1): **18 passed**.

The suite covers every field syntax, name handling, Sunday 0/7 equivalence, DOM/DOW OR semantics, and the calendar edge cases that break naive implementations: leap day (including the 4-year jump), month ends, and 31st-of-the-month schedules crossing February — plus scheduler due/run-once/error-capture behaviour.

## License

MIT — see `LICENSE`.
