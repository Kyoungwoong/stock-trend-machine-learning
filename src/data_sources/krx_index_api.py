from __future__ import annotations

"""KRX Open API skeleton.

2차 확장에서 사용한다.

현재 1차 프로젝트에서는 공공데이터포털 금융위원회_지수시세정보를 우선 사용한다.
KRX Open API를 직접 사용할 경우 Request Header의 AUTH_KEY, API ID, 응답 스키마를
개발 명세서 기준으로 확인한 뒤 구현한다.
"""

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class KrxIndexApiClient:
    auth_key: str

    def fetch_daily_index(self, start: str, end: str, index_name: str = "KOSPI") -> pd.DataFrame:
        raise NotImplementedError("Phase 2에서 KRX Open API 개발 명세서 기준으로 구현하세요.")
