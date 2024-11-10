#!/usr/bin/env python3
# -*- coding: utf8 -*-

# pylint: disable=useless-suppression             # [I0021]
# pylint: disable=missing-docstring               # [C0111] docstrings are always outdated and wrong
# pylint: disable=missing-param-doc               # [W9015]
# pylint: disable=missing-module-docstring        # [C0114]
# pylint: disable=fixme                           # [W0511] todo encouraged
# pylint: disable=line-too-long                   # [C0301]
# pylint: disable=too-many-instance-attributes    # [R0902]
# pylint: disable=too-many-lines                  # [C0302] too many lines in module
# pylint: disable=invalid-name                    # [C0103] single letter var names, name too descriptive
# pylint: disable=too-many-return-statements      # [R0911]
# pylint: disable=too-many-branches               # [R0912]
# pylint: disable=too-many-statements             # [R0915]
# pylint: disable=too-many-arguments              # [R0913]
# pylint: disable=too-many-nested-blocks          # [R1702]
# pylint: disable=too-many-locals                 # [R0914]
# pylint: disable=too-many-public-methods         # [R0904]
# pylint: disable=too-few-public-methods          # [R0903]
# pylint: disable=no-member                       # [E1101] no member for base
# pylint: disable=attribute-defined-outside-init  # [W0201]
# pylint: disable=too-many-boolean-expressions    # [R0916] in if statement
from __future__ import annotations

import errno
import os
import time
from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal
from functools import wraps
from pathlib import Path
from signal import SIG_DFL
from signal import SIGPIPE
from signal import signal

import click
import dateparser
from asserttool import ic
from click_auto_help import AHGroup
from clicktool import click_add_options
from clicktool import click_global_options
from clicktool import tvicgvd
from eprint import eprint
from globalverbose import gvd
from humanize import naturaltime
from humanize import precisedelta
from mptool import output
from timestamptool import get_int_timestamp
from unmp import unmp

# from humanize import naturaldelta

# from unitcalc import convert

signal(SIGPIPE, SIG_DFL)


def timeout(seconds, error_message=os.strerror(errno.ETIME)):
    def decorator(func):
        def _handle_timeout(signum, frame):
            raise TimeoutError(error_message)

        def wrapper(*args, **kwargs):
            signal.signal(signal.SIGALRM, _handle_timeout)
            signal.alarm(seconds)
            try:
                result = func(*args, **kwargs)
            finally:
                signal.alarm(0)
            return result

        return wraps(func)(wrapper)

    return decorator


def timestamp_to_epoch(date_time: str):
    # date_time = '2016-03-14T18:54:56.1942132'.split('.')[0]
    date_time = date_time.split(".")[0]
    pattern = "%Y-%m-%dT%H:%M:%S"
    epoch = int(time.mktime(time.strptime(date_time, pattern)))
    return epoch


def get_year_month_day(timestamp=None):
    if not timestamp:
        timestamp = get_int_timestamp()
    timestamp = int(timestamp)
    ymd = datetime.fromtimestamp(timestamp).strftime("%Y_%m_%d")
    return ymd


def timeit(f):
    def timed(*args, **kw):
        ts = time.time()
        result = f(*args, **kw)
        te = time.time()
        # eprint(
        #    "func:%r args:[%r, %r] took: %2.4f sec" % (f.__name__, args, kw, te - ts)
        # )
        eprint(f"func:{f.__name__} took: {te-ts: .3f} sec")
        return result

    return timed


def get_mtime(infile):
    mtime = os.lstat(infile).st_mtime  # does not follow symlinks
    return mtime


def get_amtime(infile):
    try:
        infile_stat = os.lstat(infile)
    except TypeError:
        infile_stat = os.lstat(infile.fileno())
    amtime = (infile_stat.st_atime_ns, infile_stat.st_mtime_ns)
    return amtime


def update_mtime_if_older(
    *,
    path: Path,
    mtime: tuple[int, int],
    verbose: bool = False,
):
    assert isinstance(mtime, tuple)
    assert isinstance(mtime[0], int)
    assert isinstance(mtime[1], int)
    current_mtime = get_amtime(path)
    if current_mtime[1] > mtime[1]:
        if verbose:
            eprint(f"{path.as_posix()} old: {current_mtime[1]} new: {mtime[1]}")
        os.utime(path, ns=mtime, follow_symlinks=False)


def seconds_duration_to_human_readable(
    seconds,
    *,
    ago: bool,
    short: bool = True,
):
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


def human_date_to_timestamp(date):
    dt = dateparser.parse(date)
    timestamp = dt.timestamp()
    return Decimal(str(timestamp))


def timestamp_to_human_date(timestamp: str):
    # timestamp = Decimal(str(timestamp))
    human_date = datetime.fromtimestamp(float(timestamp)).strftime(
        "%Y-%m-%d %H:%M:%S %Z"
    )
    return human_date.strip()


def day_month_year_to_datetime(*, day: int, month: int, year: int):
    return datetime(year=year, month=month, day=day)


def humanize_history_dict(history):
    human_history = {}
    human_history["time_unchanged"] = seconds_duration_to_human_readable(
        history["time_unchanged"], ago=False
    )
    human_history["age"] = seconds_duration_to_human_readable(history["age"], ago=True)
    return human_history


@click.group(no_args_is_help=True, cls=AHGroup)
@click_add_options(click_global_options)
@click.pass_context
def cli(
    ctx,
    verbose_inf: bool,
    dict_output: bool,
    verbose: bool = False,
):
    ctx.ensure_object(dict)
    tty, verbose = tvicgvd(
        ctx=ctx,
        verbose=verbose,
        verbose_inf=verbose_inf,
        ic=ic,
        gvd=gvd,
    )


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
@click_add_options(click_global_options)
@click.pass_context
def _amtime(
    ctx,
    paths: tuple[str, ...],
    verbose_inf: bool,
    dict_output: bool,
    verbose: bool = False,
) -> None:
    tty, verbose = tvicgvd(
        ctx=ctx,
        verbose=verbose,
        verbose_inf=verbose_inf,
        ic=ic,
        gvd=gvd,
    )

    if not verbose:
        ic.disable()

    if paths:
        iterator = paths
    else:
        iterator = unmp(
            valid_types=[
                bytes,
            ],
            verbose=verbose,
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
            dict_output=dict_output,
            tty=tty,
            verbose=verbose,
        )


@cli.command("timestamp-to-human-duration")
@click.argument("timestamps", type=str, nargs=-1)
@click_add_options(click_global_options)
@click.pass_context
def _timestamp_to_human_duration(
    ctx,
    timestamps: Sequence[str],
    verbose_inf: bool,
    dict_output: bool,
    verbose: bool = False,
) -> None:
    tty, verbose = tvicgvd(
        ctx=ctx,
        verbose=verbose,
        verbose_inf=verbose_inf,
        ic=ic,
        gvd=gvd,
    )

    if timestamps:
        iterator = timestamps
    else:
        iterator = unmp(
            valid_types=[
                str,
                int,
            ],
            verbose=verbose,
        )
    del timestamps

    index = 0
    for index, _timestamp in enumerate(iterator):
        if verbose:
            ic(index, _timestamp)

        _timestamp = int(_timestamp)
        human_duration = seconds_duration_to_human_readable(
            _timestamp, ago=False, short=False
        )
        ic(human_duration)

        output(
            human_duration,
            reason=None,
            dict_output=dict_output,
            tty=tty,
            verbose=verbose,
        )


@cli.command("timestamp-to-human-date")
@click.argument("timestamps", type=str, nargs=-1)
@click_add_options(click_global_options)
@click.pass_context
def _timestamp_to_human_date(
    ctx,
    timestamps: Sequence[str],
    verbose_inf: bool,
    dict_output: bool,
    verbose: bool = False,
) -> None:
    tty, verbose = tvicgvd(
        ctx=ctx,
        verbose=verbose,
        verbose_inf=verbose_inf,
        ic=ic,
        gvd=gvd,
    )

    if timestamps:
        iterator = timestamps
    else:
        iterator = unmp(
            valid_types=[
                str,
                int,
            ],
            verbose=verbose,
        )
    del timestamps

    index = 0
    for index, _timestamp in enumerate(iterator):
        if verbose:
            ic(index, _timestamp)

        _timestamp = int(_timestamp)
        human_timestamp = timestamp_to_human_date(_timestamp)

        output(
            human_timestamp,
            reason=None,
            dict_output=dict_output,
            tty=tty,
            verbose=verbose,
        )


@cli.command("human-date-to-timestamp")
@click.argument("human_dates", type=str, nargs=-1)
@click_add_options(click_global_options)
@click.pass_context
def _human_date_to_timestamp(
    ctx,
    human_dates: tuple[str, ...],
    verbose_inf: bool,
    dict_output: bool,
    verbose: bool = False,
) -> None:
    tty, verbose = tvicgvd(
        ctx=ctx,
        verbose=verbose,
        verbose_inf=verbose_inf,
        ic=ic,
        gvd=gvd,
    )

    if human_dates:
        iterator = human_dates
    else:
        iterator = unmp(
            valid_types=[
                str,
                int,
            ],
            verbose=verbose,
        )
    del human_dates

    index = 0
    for index, _date in enumerate(iterator):
        ic(index, _date)

        _timestamp = human_date_to_timestamp(_date)

        output(
            _timestamp,
            reason=_date,
            dict_output=dict_output,
            tty=tty,
            verbose=verbose,
        )
