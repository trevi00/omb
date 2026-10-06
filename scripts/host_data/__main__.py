"""`uv run python scripts/host_data <command>` (or `python -m host_data` with scripts/ on the path)."""
import sys
from pathlib import Path

if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from host_data.cli import main
else:
    from .cli import main

sys.exit(main())
