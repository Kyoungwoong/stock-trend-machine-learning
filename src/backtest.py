from __future__ import annotations

import sys
from pathlib import Path


if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.pipeline.backtest import backtest, main, max_drawdown


if __name__ == "__main__":
    main()
