
from datetime import datetime, timedelta
import pytest
from job_scheduler import CronError, CronExpression, Scheduler

def test_every_minute(): e=CronExpression("* * * * *"); assert e.next_run(datetime(2026,1,1,10,0,30))==datetime(2026,1,1,10,1)
def test_daily_at_9(): e=CronExpression("0 9 * * *"); assert e.next_run(datetime(2026,1,1,10,0))==datetime(2026,1,2,9,0); assert e.next_run(datetime(2026,1,1,8,0))==datetime(2026,1,1,9,0)
def test_step_minutes(): e=CronExpression("*/15 * * * *"); assert e.next_run(datetime(2026,1,1,10,7))==datetime(2026,1,1,10,15)
def test_list_and_range(): e=CronExpression("0 9-17 * * MON-FRI"); assert e.matches(datetime(2026,1,5,9,0))  # Monday
    # 2026-01-05 is a Monday
def test_weekday_excludes_weekend(): e=CronExpression("0 9 * * MON-FRI"); assert e.next_run(datetime(2026,1,3,10,0))==datetime(2026,1,5,9,0)  # Sat -> Mon
def test_month_names_and_lists(): e=CronExpression("0 0 1 JAN,APR *"); assert e.next_run(datetime(2026,2,1))==datetime(2026,4,1,0,0)
def test_leap_day(): e=CronExpression("0 0 29 2 *"); assert e.next_run(datetime(2023,3,1))==datetime(2024,2,29,0,0); assert e.next_run(datetime(2024,2,29,0,0))==datetime(2028,2,29,0,0)
def test_month_end_skips_short_months(): e=CronExpression("0 0 31 * *"); assert e.next_run(datetime(2026,2,1))==datetime(2026,3,31,0,0)  # Feb has no 31st
def test_jan31_to_mar31_via_feb(): e=CronExpression("30 12 31 * *"); assert e.next_run(datetime(2026,1,31,12,30))==datetime(2026,3,31,12,30)
def test_dom_dow_or_semantics(): e=CronExpression("0 0 15 * MON"); assert e.matches(datetime(2026,1,5,0,0)) or e.matches(datetime(2026,1,15,0,0)); assert e.matches(datetime(2026,1,15,0,0))
def test_sunday_zero_and_seven(): assert CronExpression("0 0 * * 0").matches(datetime(2026,1,4,0,0)); assert CronExpression("0 0 * * 7").matches(datetime(2026,1,4,0,0)); assert CronExpression("0 0 * * SUN").matches(datetime(2026,1,4,0,0))
def test_range_with_step(): e=CronExpression("0 9-17/2 * * *"); assert e.matches(datetime(2026,1,1,11,0)); assert not e.matches(datetime(2026,1,1,10,0))
def test_invalid_expressions():
    for bad in ["* * * *", "* * * * * *", "61 * * * *", "0 25 * * *", "0 0 32 * *", "0 0 * 13 *", "0 0 * * 8", "x * * * *", "*/0 * * * *"]:
        with pytest.raises(CronError): CronExpression(bad)
def test_scheduler_runs_due_once_per_minute():
    s=Scheduler(); calls=[]; s.add_job("j","* * * * *", lambda: calls.append(1)); now=datetime(2026,1,1,10,0,45); s.run_pending(now); s.run_pending(now); assert len(calls)==1; assert s.get_job("j").run_count==1
def test_scheduler_captures_job_errors():
    s=Scheduler()
    def bad(): raise RuntimeError("kaput")
    s.add_job("bad","* * * * *", bad); ran=s.run_pending(datetime(2026,1,1,10,0)); assert ran[0].last_error and "RuntimeError" in ran[0].last_error
def test_scheduler_next_runs_and_remove():
    s=Scheduler(); s.add_job("daily","0 9 * * *", lambda: None); assert s.next_runs(datetime(2026,1,1,10,0))=={"daily": datetime(2026,1,2,9,0)}; assert s.remove_job("daily"); assert not s.remove_job("daily")
def test_scheduler_disabled_job_not_due():
    s=Scheduler(); job=s.add_job("j","* * * * *", lambda: None); job.enabled=False; assert s.due_jobs(datetime(2026,1,1,10,0))==[]
def test_duplicate_name_rejected():
    s=Scheduler(); s.add_job("j","* * * * *", lambda: None)
    with pytest.raises(ValueError): s.add_job("j","* * * * *", lambda: None)
