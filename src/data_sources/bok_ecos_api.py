from __future__ import annotations

"""한국은행 ECOS API skeleton.

금리, 환율, 물가 등 거시경제 feature는 Phase 4에서 추가한다.
발표 주기와 발표 지연을 확인해 현재 시점에 알 수 있었던 값만 사용해야 한다.
"""

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class BokEcosApiClient:
    api_key: str

    def fetch_stat_series(self, stat_code: str, item_code: str, start: str, end: str) -> pd.DataFrame:
        raise NotImplementedError("Phase 4에서 한국은행 ECOS 통계코드 기준으로 구현하세요.")
