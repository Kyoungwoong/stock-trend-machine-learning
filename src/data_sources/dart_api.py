from __future__ import annotations

"""OpenDART API skeleton.

재무제표 데이터는 결산 기준일이 아니라 공시 제출일 이후부터 feature로 사용할 수 있다.
이 모듈은 Phase 4에서 point-in-time merge를 구현할 때 확장한다.
"""

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class DartApiClient:
    api_key: str

    def fetch_single_company_financials(self, corp_code: str, business_year: str, report_code: str) -> pd.DataFrame:
        raise NotImplementedError("Phase 4에서 OpenDART 정기보고서 재무정보 API 기준으로 구현하세요.")
