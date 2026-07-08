from __future__ import annotations

import sys
from pathlib import Path


if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.pipeline.train import build_models, main, split_by_date, train, validate_feature_columns


if __name__ == "__main__":
    main()
