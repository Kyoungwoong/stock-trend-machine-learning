from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    data_go_kr_service_key: str | None
    krx_auth_key: str | None
    dart_api_key: str | None
    bok_ecos_api_key: str | None
    data_dir: Path
    model_dir: Path
    report_dir: Path
    default_ticker: str
    default_market_index: str


def get_settings() -> Settings:
    return Settings(
        data_go_kr_service_key=os.getenv("DATA_GO_KR_SERVICE_KEY") or None,
        krx_auth_key=os.getenv("KRX_AUTH_KEY") or None,
        dart_api_key=os.getenv("DART_API_KEY") or None,
        bok_ecos_api_key=os.getenv("BOK_ECOS_API_KEY") or None,
        data_dir=Path(os.getenv("DATA_DIR", "data")),
        model_dir=Path(os.getenv("MODEL_DIR", "models")),
        report_dir=Path(os.getenv("REPORT_DIR", "reports")),
        default_ticker=os.getenv("DEFAULT_TICKER", "005930"),
        default_market_index=os.getenv("DEFAULT_MARKET_INDEX", "KOSPI"),
    )


SETTINGS = get_settings()
