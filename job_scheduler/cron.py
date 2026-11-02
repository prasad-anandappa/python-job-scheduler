
from __future__ import annotations
from datetime import datetime, timedelta

class CronError(ValueError): pass

MONTH_NAMES={"JAN":1,"FEB":2,"MAR":3,"APR":4,"MAY":5,"JUN":6,"JUL":7,"AUG":8,"SEP":9,"OCT":10,"NOV":11,"DEC":12}
DOW_NAMES={"SUN":0,"MON":1,"TUE":2,"WED":3,"THU":4,"FRI":5,"SAT":6}

def _parse_field(spec: str, lo: int, hi: int, names: dict | None = None, *, dow: bool = False) -> frozenset[int]:
    def val(tok: str) -> int:
        tok=tok.strip().upper()
        if names and tok in names: return names[tok]
        try: return int(tok)
        except ValueError: raise CronError(f"invalid value {tok!r} in field {spec!r}")
    values:set[int]=set()
    for part in spec.split(","):
        part=part.strip()
        if not part: raise CronError(f"empty list item in {spec!r}")
        step=1
        if "/" in part:
            base, step_s = part.split("/",1)
            try: step=int(step_s)
            except ValueError: raise CronError(f"invalid step in {part!r}")
            if step<=0: raise CronError("step must be positive")
        else: base=part
        if base=="*": start,end=lo,hi
        elif "-" in base:
            a,b=base.split("-",1); start,end=val(a),val(b)
        else:
            start=val(base); end=hi if "/" in part else start
        if start<lo or end>hi or start>end: raise CronError(f"range {start}-{end} out of bounds {lo}-{hi} in {spec!r}")
        for v in range(start,end+1,step):
            values.add(0 if (dow and v==7) else v)
    return frozenset(values)

class CronExpression:
    """Standard 5-field cron: minute hour day-of-month month day-of-week.
    Day-of-week: 0 and 7 are both Sunday. DOM/DOW follow classic cron OR semantics
    when both are restricted."""
    def __init__(self, expression: str):
        fields=expression.strip().split()
        if len(fields)!=5: raise CronError(f"expected 5 fields, got {len(fields)}: {expression!r}")
        self.expression=expression.strip()
        self.minutes=_parse_field(fields[0],0,59)
        self.hours=_parse_field(fields[1],0,23)
        self.days_of_month=_parse_field(fields[2],1,31)
        self.months=_parse_field(fields[3],1,12,MONTH_NAMES)
        self.days_of_week=_parse_field(fields[4],0,7,DOW_NAMES,dow=True)
        self._dom_restricted = fields[2] != "*"
        self._dow_restricted = fields[4] != "*"
    @staticmethod
    def _cron_dow(dt: datetime) -> int: return (dt.weekday()+1)%7
    def _day_matches(self, dt: datetime) -> bool:
        dom_ok=dt.day in self.days_of_month; dow_ok=self._cron_dow(dt) in self.days_of_week
        if self._dom_restricted and self._dow_restricted: return dom_ok or dow_ok
        if self._dom_restricted: return dom_ok
        if self._dow_restricted: return dow_ok
        return True
    def matches(self, dt: datetime) -> bool:
        return dt.minute in self.minutes and dt.hour in self.hours and dt.month in self.months and self._day_matches(dt)
    def next_run(self, after: datetime) -> datetime:
        """Next matching minute strictly after `after` (seconds/microseconds zeroed).
        Iterates day-by-day, then sorts candidate times inside the day — so even a
        Feb-29-only schedule resolves fast instead of scanning millions of minutes."""
        start=(after.replace(second=0,microsecond=0)+timedelta(minutes=1))
        sorted_hours=sorted(self.hours); sorted_minutes=sorted(self.minutes)
        day=start.date()
        for _ in range(366*5+2):
            probe=datetime(day.year,day.month,day.day,tzinfo=after.tzinfo)
            if probe.month in self.months and self._day_matches(probe):
                for h in sorted_hours:
                    for m in sorted_minutes:
                        candidate=datetime(day.year,day.month,day.day,h,m,tzinfo=after.tzinfo)
                        if candidate>=start: return candidate
            day+=timedelta(days=1)
        raise CronError("no run found within 5 years")
    def __repr__(self): return f"CronExpression({self.expression!r})"
