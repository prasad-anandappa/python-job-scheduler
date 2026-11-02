
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable
from .cron import CronExpression

@dataclass
class Job:
    name: str
    cron: CronExpression
    func: Callable[[], object]
    enabled: bool = True
    last_run: datetime | None = None
    run_count: int = 0
    last_error: str | None = None
    def next_run(self, after: datetime) -> datetime: return self.cron.next_run(after)

class Scheduler:
    """In-process scheduler engine. The host loop calls run_pending(now);
    job exceptions are captured on the job, never propagated to the loop."""
    def __init__(self): self._jobs: dict[str, Job] = {}
    def add_job(self, name: str, cron: str | CronExpression, func: Callable[[], object]) -> Job:
        if name in self._jobs: raise ValueError(f"duplicate job name {name!r}")
        expr=cron if isinstance(cron, CronExpression) else CronExpression(cron)
        job=Job(name=name, cron=expr, func=func); self._jobs[name]=job; return job
    def remove_job(self, name: str) -> bool: return self._jobs.pop(name, None) is not None
    def get_job(self, name: str) -> Job | None: return self._jobs.get(name)
    @property
    def jobs(self) -> list[Job]: return list(self._jobs.values())
    def due_jobs(self, now: datetime) -> list[Job]:
        minute=now.replace(second=0,microsecond=0)
        return [j for j in self._jobs.values() if j.enabled and j.cron.matches(minute) and j.last_run != minute]
    def run_pending(self, now: datetime) -> list[Job]:
        ran=[]
        for job in self.due_jobs(now):
            try: job.func(); job.last_error=None
            except Exception as exc: job.last_error=repr(exc)
            job.last_run=now.replace(second=0,microsecond=0); job.run_count+=1; ran.append(job)
        return ran
    def next_runs(self, after: datetime) -> dict[str, datetime]:
        return {j.name: j.next_run(after) for j in self._jobs.values() if j.enabled}
