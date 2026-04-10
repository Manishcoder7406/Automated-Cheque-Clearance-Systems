from __future__ import annotations

import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from server.ui_app import main

if __name__ == "__main__":
    main()
