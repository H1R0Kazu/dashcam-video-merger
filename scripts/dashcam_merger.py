#!/usr/bin/env python3
"""
Dashcam Video Merger - エントリーポイントスクリプト

このスクリプトは後方互換性のために提供されています。
新しい推奨方法: python -m dashcam_merger
"""

import sys
from pathlib import Path

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from dashcam_merger.cli.main import main

if __name__ == "__main__":
    main()