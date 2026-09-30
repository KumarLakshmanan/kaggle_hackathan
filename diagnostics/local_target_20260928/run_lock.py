"""Prevent two benchmark coordinators from appending the same checkpoint."""
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
import json
import os


@contextmanager
def exclusive_run(path):
    path = Path(path)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
    try:
        with os.fdopen(descriptor, 'w', encoding='utf-8') as handle:
            json.dump({'pid':os.getpid(),'started_at_utc':datetime.now(timezone.utc).isoformat()},handle)
        yield
    finally:
        # An interrupted coordinator intentionally leaves a lock for manual
        # process-identity verification before any exact-checkpoint resume.
        path.unlink()
