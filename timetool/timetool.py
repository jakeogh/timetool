#!/usr/bin/env python3
# -*- coding: utf8 -*-

from __future__ import annotations

import errno
import os
import time
from collections.abc import Callable
from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal
from functools import wraps
from pathlib import Path
from signal import SIG_DFL
from signal import SIGPIPE
from signal import signal
from typing import Any
from typing import TypeVar

import click
import dateparser
from asserttool import ic
from click_auto_help import AHGroup
from eprint import eprint
from humanize import naturaltime
from humanize import precisedelta
from mptool import output
from timestamptool import get_int_timestamp
from unmp import unmp

# from humanize import naturaldelta

# from unitcalc import convert

signal(SIGPIPE, SIG_DFL)

F = TypeVar("F", bound=Callable[..., Any])


def timeout(
    seconds: int, error_message: str = os.strerror(errno.ETIME)
) -> Callable[[F], F]:
    def decorator(func: F) -> F:
        def _handle_timeout(signum: int, frame: Any) -> None:
            raise TimeoutError(error_message)

        def wrapper(*args: Any, **kwargs: Any) -> Any:
            signal.signal(signal.SIGALRM, _handle_timeout)
            signal.alarm(seconds)
            try:
                result = func(*args, **kwargs)
            finally:
                signal.alarm(0)
            return result

        return wraps(func)(wrapper)  # type: ignore

    return decorator  # type: ignore


def timestamp_to_epoch(date_time: str) -> int:
    date_time = date_time.split(".")[0]
    pattern = "%Y-%m-%dT%H:%M:%S"
    epoch = int(time.mktime(time.strptime(date_time, pattern)))
    return epoch


def get_year_month_day(timestamp: int | float | None = None) -> str:
    if not timestamp:
        timestamp = get_int_timestamp()
    timestamp = int(timestamp)
    ymd = datetime.fromtimestamp(timestamp).strftime("%Y_%m_%d")
    return ymd


def timeit(f: F) -> F:
    def timed(*args: Any, **kw: Any) -> Any:
        ts = time.time()
        result = f(*args, **kw)
        te = time.time()
        # eprint(
        #    "func:%r args:[%r, %r] took: %2.4f sec" % (f.__name__, args, kw, te - ts)
        # )
        eprint(f"func:{f.__name__} took: {te-ts: .3f} sec")
        return result

    return timed  # type: ignore


def get_mtime(infile: str | Path) -> float:
    mtime = os.lstat(infile).st_mtime  # does not follow symlinks
    return mtime


def get_amtime(infile: str | Path | int) -> tuple[int, int]:
    try:
        infile_stat = os.lstat(infile)  # type: ignore
    except TypeError:
        infile_stat = os.lstat(infile.fileno())  # type: ignore
    amtime = (infile_stat.st_atime_ns, infile_stat.st_mtime_ns)
    return amtime


def update_mtime_if_older(
    *,
    path: Path,
    mtime: tuple[int, int],
    verbose: bool = False,
) -> None:
    assert isinstance(mtime, tuple)
    assert isinstance(mtime[0], int)
    assert isinstance(mtime[1], int)
    current_mtime = get_amtime(path)
    if current_mtime[1] > mtime[1]:
        if verbose:
            eprint(f"{path.as_posix()} old: {current_mtime[1]} new: {mtime[1]}")
        os.utime(path, ns=mtime, follow_symlinks=False)


def seconds_duration_to_human_readable(
    seconds: int | float | None,
    *,
    ago: bool,
    short: bool = True,
) -> str | None:
    if seconds is None:
        return None
    seconds = float(seconds)
    if ago:
        result = naturaltime(seconds)
    else:
        # result = naturaldelta(seconds)
        result = precisedelta(seconds, minimum_unit="minutes")

    if short:
        result = result.replace(" seconds", "s")
        result = result.replace("a second", "1s")

        result = result.replace(" minutes", "min")
        result = result.replace("a minute", "1min")

        result = result.replace(" hours", "hr")
        result = result.replace("an hour", "1hr")

        result = result.replace(" days", "days")
        result = result.replace("a day", "1day")

        result = result.replace(" months", "mo")
        result = result.replace("a month", "1mo")

        result = result.replace(" years", "yrs")
        result = result.replace("a year", "1yr")
        result = result.replace("1 year", "1yr")

        result = result.replace(" ago", "_ago")
        result = result.replace(", ", ",")
    return result


def human_date_to_datetime(date: str) -> datetime | None:
    dt = dateparser.parse(date)
    return dt


def human_date_to_timestamp(date: str) -> Decimal:
    dt = human_date_to_datetime(date)
    if dt is None:
        raise ValueError(f"Could not parse date: {date}")
    timestamp = dt.timestamp()
    return Decimal(str(timestamp))


def timestamp_to_human_date(timestamp: str | int | float) -> str:
    # timestamp = Decimal(str(timestamp))
    human_date = datetime.fromtimestamp(float(timestamp)).strftime(
        "%Y-%m-%d %H:%M:%S %Z"
    )
    return human_date.strip()


def day_month_year_to_datetime(
    *,
    day: int,
    month: int,
    year: int,
) -> datetime:
    return datetime(year=year, month=month, day=day)


def humanize_history_dict(history: dict[str, int | float]) -> dict[str, str | None]:
    human_history: dict[str, str | None] = {}
    human_history["time_unchanged"] = seconds_duration_to_human_readable(
        history["time_unchanged"], ago=False
    )
    human_history["age"] = seconds_duration_to_human_readable(history["age"], ago=True)
    return human_history


def timestamp_to_human_duration(
    timestamp: int | str | float,
    short: bool = False,
    verbose: bool = False,
) -> str:
    """Convert a single timestamp (in seconds) to human-readable duration.

    Args:
        timestamp: Timestamp in seconds
        short: Use short format for duration
        verbose: Enable verbose output

    Returns:
        Human-readable duration string
    """
    ic(timestamp)

    timestamp_int = int(timestamp)
    human_duration = seconds_duration_to_human_readable(
        timestamp_int, ago=False, short=short
    )
    ic(human_duration)

    if human_duration is None:
        return ""

    return human_duration


def timestamps_to_human_durations(
    timestamps: Sequence[int | str | float],
    short: bool = False,
) -> list[str]:
    """Convert timestamps (in seconds) to human-readable durations.

    Args:
        timestamps: Sequence of timestamps in seconds
        short: Use short format for durations

    Returns:
        List of human-readable duration strings
    """
    results: list[str] = []
    for timestamp in timestamps:
        human_duration = timestamp_to_human_duration(
            timestamp,
            short=short,
        )
        results.append(human_duration)

    return results


def timestamps_to_human_dates(
    timestamps: Sequence[int | str | float],
) -> list[str]:
    """Convert Unix timestamps to human-readable dates.

    Args:
        timestamps: Sequence of Unix timestamps

    Returns:
        List of human-readable date strings
    """
    results: list[str] = []
    for index, timestamp in enumerate(timestamps):
        ic(index, timestamp)

        human_timestamp = timestamp_to_human_date(timestamp)
        results.append(human_timestamp)

    return results


def human_dates_to_timestamps(
    human_dates: Sequence[str],
) -> list[Decimal]:
    """Convert human-readable dates to Unix timestamps.

    Args:
        human_dates: Sequence of human-readable date strings

    Returns:
        List of Unix timestamps as Decimal objects
    """
    results: list[Decimal] = []
    for index, date in enumerate(human_dates):
        ic(index, date)

        timestamp = human_date_to_timestamp(date)
        results.append(timestamp)

    return results


@click.group(no_args_is_help=True, cls=AHGroup)
@click.pass_context
def cli(
    ctx: click.Context,
) -> None:
    ctx.ensure_object(dict)


@cli.command("amtime")
@click.argument(
    "paths",
    type=click.Path(
        exists=False,
        dir_okay=True,
        file_okay=False,
        allow_dash=False,
        path_type=Path,
    ),
    nargs=-1,
)
@click.pass_context
def _amtime(
    ctx: click.Context,
    paths: tuple[Path, ...],
) -> None:

    # if not verbose:
    #    ic.disable()

    iterator: Sequence[Any]
    if paths:
        iterator = paths
    else:
        iterator = unmp(
            valid_types=[
                bytes,
            ],
        )
    del paths

    index = 0
    for index, _mpobject in enumerate(iterator):
        ic(index, _mpobject)
        _path = Path(os.fsdecode(_mpobject)).resolve()

        _amtime = get_amtime(_path)
        ic(_amtime)

        output(
            _amtime,
            reason=None,
        )


@cli.command("timestamp-to-human-duration")
@click.argument("timestamps", type=str, nargs=-1)
@click.pass_context
def _timestamp_to_human_duration(
    ctx: click.Context,
    timestamps: tuple[str, ...],
) -> None:
    iterator: Sequence[Any]
    if timestamps:
        iterator = timestamps
    else:
        iterator = unmp(
            valid_types=[
                str,
                int,
            ],
        )
    del timestamps

    index = 0
    for index, _timestamp in enumerate(iterator):
        ic(index, _timestamp)

        _timestamp_int = int(_timestamp)
        human_duration = seconds_duration_to_human_readable(
            _timestamp_int,
            ago=False,
            short=False,
        )

        output(
            human_duration,
            reason=None,
        )


@cli.command("timestamp-to-human-date")
@click.argument("timestamps", type=str, nargs=-1)
@click.pass_context
def _timestamp_to_human_date(
    ctx: click.Context,
    timestamps: tuple[str, ...],
) -> None:
    iterator: Sequence[Any]
    if timestamps:
        iterator = timestamps
    else:
        iterator = unmp(
            valid_types=[
                str,
                int,
            ],
        )
    del timestamps

    index = 0
    for index, _timestamp in enumerate(iterator):
        ic(index, _timestamp)

        _timestamp_int = int(_timestamp)
        human_timestamp = timestamp_to_human_date(_timestamp_int)

        output(
            human_timestamp,
            reason=None,
        )


@cli.command("human-date-to-timestamp")
@click.argument("human_dates", type=str, nargs=-1)
@click.pass_context
def _human_date_to_timestamp(
    ctx: click.Context,
    human_dates: tuple[str, ...],
) -> None:

    iterator: Sequence[Any]
    if human_dates:
        iterator = human_dates
    else:
        iterator = unmp(
            valid_types=[
                str,
                int,
            ],
        )
    del human_dates

    index = 0
    for index, _date in enumerate(iterator):
        ic(index, _date)

        _timestamp = human_date_to_timestamp(_date)

        output(
            _timestamp,
            reason=_date,
        )
