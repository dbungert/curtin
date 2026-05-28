# This file is part of curtin. See LICENSE file for copyright and license info.
"""Runtime dependency tracer.

Logs every external subprocess invocation to
/var/log/installer/runtime-deps-curtin.ndjson as a newline-delimited JSON
stream so that a real install can be compared against the static analysis
produced by scripts/find-external-commands.py.

The log directory is /var/log/installer, matching all other installer logs.
If that directory does not exist (e.g. in development environments) the
logging silently no-ops.

Write atomicity: we use O_APPEND + a single os.write() call.  On Linux,
writes smaller than PIPE_BUF (4096 bytes) to an O_APPEND file are atomic,
so concurrent curtin invocations will not interleave partial records.
"""

import datetime
import json
import os
import sys

_LOG_PATH = "/var/log/installer/runtime-deps-curtin.ndjson"
_SOURCE = "curtin"


def _capture_callers(skip: int, max_depth: int) -> list:
    """Return up to max_depth caller frames, skipping the innermost `skip` frames.

    skip=2 when called from log_call() so we discard both _capture_callers and
    log_call from the output, leaving the first entry as the code that called
    log_call() (i.e. _subp in util.py).
    """
    callers = []
    try:
        frame = sys._getframe(skip)
        while frame is not None and len(callers) < max_depth:
            callers.append({
                "file": frame.f_code.co_filename,
                "line": frame.f_lineno,
                "func": frame.f_code.co_name,
            })
            frame = frame.f_back
    except ValueError:
        pass
    return callers


def log_call(argv) -> None:
    """Log a subprocess invocation.  argv should be the command list."""
    if not argv:
        return
    log_dir = os.path.dirname(_LOG_PATH)
    if not os.path.isdir(log_dir):
        return
    record = {
        "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "source": _SOURCE,
        "argv": [str(a) for a in argv],
        "callers": _capture_callers(skip=2, max_depth=5),
    }
    line = (json.dumps(record, separators=(",", ":")) + "\n").encode()
    try:
        fd = os.open(_LOG_PATH, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
        try:
            os.write(fd, line)
        finally:
            os.close(fd)
    except OSError:
        pass
