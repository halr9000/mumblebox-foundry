"""Launch pinned Hi3D with Windows-safe status writes, leaving upstream untouched."""
import json
import os
from pathlib import Path
import tempfile
import time


def atomic_json(path, value):
    """Retry transient reader locks; never replace atomic writes with partial writes."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(dir=path.parent, suffix='.tmp')
    try:
        with os.fdopen(descriptor, 'w', encoding='utf-8') as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        for attempt in range(11):
            try:
                os.replace(name, path)
                return
            except PermissionError as error:
                # Windows read handles and virus scanners may temporarily deny rename.
                if getattr(error, 'winerror', None) not in (5, 32, 33) or attempt == 10:
                    raise
                time.sleep(.1)
    finally:
        Path(name).unlink(missing_ok=True)


if __name__ == '__main__':
    import hi3d_workbench.common as common
    common.atomic_json = atomic_json
    # Set before importing server/models/jobs, which bind their writer on import.
    from hi3d_workbench.__main__ import main
    main()
