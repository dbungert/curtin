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

_LOG_PATH = "/var/log/installer/runtime-deps-curtin.ndjson"
_SOURCE = "curtin"


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
