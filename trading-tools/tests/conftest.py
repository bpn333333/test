"""テストから monitor / distribution の両パッケージを読めるようにする。"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

for package_dir in (ROOT / "monitor", ROOT / "distribution"):
    if str(package_dir) not in sys.path:
        sys.path.insert(0, str(package_dir))
