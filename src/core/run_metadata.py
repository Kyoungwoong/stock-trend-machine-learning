from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote, unquote


REAL_INDEX_SOURCES = {"fsc", "krx"}


@dataclass(frozen=True)
class RunMetadata:
    schema_version: int
    run_id: str
    generated_at_utc: str
    ticker: str
    start: str
    end: str
    data_mode: str
    index_source: str
    fallback_applied: bool
    fallback_reason: str | None
    index_normalized_rows: int
    merged_rows: int
    uses_real_kospi: bool
    market_feature_mode: str
    stock_raw_rows: int
    stock_normalized_rows: int
    index_raw_rows: int
    dataset_rows: int
    dataset_start: str
    dataset_end: str
    latest_feature_date: str
    index_fetch_warnings: list[str]
    market_feature_validation_passed: bool
    model_selected: str | None = None
    test_accuracy: float | None = None
    test_f1: float | None = None
    test_roc_auc: float | None = None
    backtest_trade_count: int | None = None
    backtest_avg_trade_return: float | None = None
    backtest_win_rate: float | None = None
    backtest_strategy_return_reference: float | None = None
    backtest_buy_and_hold_return: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_run_metadata(
    *,
    ticker: str,
    start: str,
    end: str,
    use_sample: bool,
    index_source: str,
    fallback_applied: bool,
    fallback_reason: str | None,
    index_normalized_rows: int,
    merged_rows: int,
    stock_raw_rows: int,
    stock_normalized_rows: int,
    index_raw_rows: int,
    dataset_rows: int,
    dataset_start: str,
    dataset_end: str,
    latest_feature_date: str,
    index_fetch_warnings: list[str],
    market_feature_validation_passed: bool,
) -> RunMetadata:
    uses_real_kospi = (
        not use_sample
        and not fallback_applied
        and index_source in REAL_INDEX_SOURCES
        and index_normalized_rows > 0
        and merged_rows > 0
    )
    if fallback_applied:
        market_feature_mode = "stock_only_fallback"
    elif use_sample:
        market_feature_mode = "sample_index"
    elif uses_real_kospi:
        market_feature_mode = "real_kospi"
    else:
        raise ValueError("Index state is inconsistent: the run is neither real, sample, nor fallback.")

    generated_at = datetime.now(UTC)
    run_id = f"{generated_at.strftime('%Y%m%dT%H%M%S%fZ')}_{ticker}_{market_feature_mode}"
    return RunMetadata(
        schema_version=1,
        run_id=run_id,
        generated_at_utc=generated_at.isoformat().replace("+00:00", "Z"),
        ticker=ticker,
        start=start,
        end=end,
        data_mode="sample" if use_sample else "real_api",
        index_source=index_source,
        fallback_applied=fallback_applied,
        fallback_reason=fallback_reason,
        index_normalized_rows=int(index_normalized_rows),
        merged_rows=int(merged_rows),
        uses_real_kospi=uses_real_kospi,
        market_feature_mode=market_feature_mode,
        stock_raw_rows=int(stock_raw_rows),
        stock_normalized_rows=int(stock_normalized_rows),
        index_raw_rows=int(index_raw_rows),
        dataset_rows=int(dataset_rows),
        dataset_start=dataset_start,
        dataset_end=dataset_end,
        latest_feature_date=latest_feature_date,
        index_fetch_warnings=list(index_fetch_warnings),
        market_feature_validation_passed=market_feature_validation_passed,
    )


def write_run_metadata(path: Path, metadata: RunMetadata | dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = metadata.to_dict() if isinstance(metadata, RunMetadata) else metadata
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_run_metadata(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Run metadata not found: {path}. Run data_pipeline.py before training.")
    metadata = json.loads(path.read_text(encoding="utf-8"))
    required = {
        "index_source",
        "fallback_applied",
        "fallback_reason",
        "index_normalized_rows",
        "merged_rows",
        "uses_real_kospi",
        "market_feature_mode",
    }
    missing = required.difference(metadata)
    if missing:
        raise ValueError(f"Run metadata is missing required fields: {sorted(missing)}")
    return metadata


def metadata_from_artifact(artifact: dict[str, Any]) -> dict[str, Any]:
    metadata = artifact.get("run_metadata")
    if not isinstance(metadata, dict):
        raise RuntimeError("Model artifact has no run metadata. Re-run data_pipeline.py and train.py.")
    return metadata


def interpretation_warning(metadata: dict[str, Any]) -> str:
    mode = metadata["market_feature_mode"]
    if mode == "stock_only_fallback":
        return "This model used stock-only fallback features and is not a real market-relative model."
    if mode == "sample_index":
        return "This model used synthetic sample index data and is not a real market-relative model."
    return "This model used normalized real KOSPI index data joined by trading date."


def interpretation_notice(metadata: dict[str, Any]) -> str:
    if metadata["market_feature_mode"] == "stock_only_fallback":
        if "--force-stock-only" in str(metadata.get("fallback_reason")):
            return (
                "This run intentionally used a stock-only baseline for comparison.\n"
                "Market-relative features are not based on real KOSPI index data in this baseline.\n\n"
                "이번 실행은 비교용 stock-only baseline을 의도적으로 사용했습니다.\n"
                "따라서 이 baseline의 market_return, excess_return feature는 실제 시장 대비 feature가 아닙니다."
            )
        return (
            "This run used stock-only fallback because KOSPI index data was unavailable.\n"
            "Market-relative features are not based on real KOSPI index data.\n"
            "Do not interpret this result as a market-relative model comparison.\n\n"
            "이번 실행은 KOSPI 지수 데이터가 없어 stock-only fallback으로 수행되었습니다.\n"
            "따라서 market_return, excess_return feature는 실제 시장 대비 feature로 해석하면 안 됩니다."
        )
    if metadata["market_feature_mode"] == "sample_index":
        return "This run used synthetic sample index data. 샘플 실행 결과를 실제 시장 대비 모델로 해석하면 안 됩니다."
    return "This run used real KOSPI index data. 실제 KOSPI 지수가 날짜 기준으로 결합되었습니다."


def metadata_markdown(metadata: dict[str, Any]) -> str:
    return f"""## Data Context

| field | value |
|---|---|
| index_source | `{metadata['index_source']}` |
| fallback_applied | `{metadata['fallback_applied']}` |
| fallback_reason | `{metadata['fallback_reason']}` |
| index_normalized_rows | `{metadata['index_normalized_rows']}` |
| merged_rows | `{metadata['merged_rows']}` |
| uses_real_kospi | `{metadata['uses_real_kospi']}` |
| market_feature_mode | `{metadata['market_feature_mode']}` |

{interpretation_notice(metadata)}"""


def update_matching_run_metadata(path: Path, expected_generated_at: str, **updates: Any) -> dict[str, Any]:
    metadata = load_run_metadata(path)
    if metadata.get("generated_at_utc") != expected_generated_at:
        raise RuntimeError("Run metadata does not match the model dataset. Re-run data_pipeline.py and train.py in order.")
    metadata.update(updates)
    write_run_metadata(path, metadata)
    return metadata


def redact_secrets(message: str, secrets: list[str | None]) -> str:
    redacted = message
    for secret in secrets:
        if not secret:
            continue
        variants = {secret, quote(secret, safe=""), unquote(secret)}
        for variant in sorted(variants, key=len, reverse=True):
            if variant:
                redacted = redacted.replace(variant, "[REDACTED]")
    return redacted


def snapshot_run_metadata(report_dir: Path, metadata: dict[str, Any]) -> Path:
    run_id = metadata.get("run_id")
    if not run_id:
        raise ValueError("Run metadata has no run_id.")
    path = report_dir / "runs" / f"{run_id}.json"
    write_run_metadata(path, metadata)
    return path


def write_index_mode_comparison(report_dir: Path) -> Path:
    run_dir = report_dir / "runs"
    snapshots: list[dict[str, Any]] = []
    for path in sorted(run_dir.glob("*.json")) if run_dir.exists() else []:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("test_accuracy") is not None:
            snapshots.append(payload)

    latest: dict[str, dict[str, Any]] = {}
    for metadata in snapshots:
        mode = metadata.get("market_feature_mode")
        if mode in {"stock_only_fallback", "real_kospi"}:
            latest[mode] = metadata

    rows = []
    for mode in ["stock_only_fallback", "real_kospi"]:
        metadata = latest.get(mode)
        if not metadata:
            rows.append(f"| {mode} | pending | - | - | - | - | - |")
            continue
        rows.append(
            "| {mode} | {source} | {dataset_rows} | {accuracy:.4f} | {f1:.4f} | {auc:.4f} | {strategy} |".format(
                mode=mode,
                source=metadata.get("index_source"),
                dataset_rows=metadata.get("dataset_rows"),
                accuracy=float(metadata.get("test_accuracy")),
                f1=float(metadata.get("test_f1")),
                auc=float(metadata.get("test_roc_auc")),
                strategy=(
                    f"{float(metadata['backtest_strategy_return_reference']):.4f}"
                    if metadata.get("backtest_strategy_return_reference") is not None
                    else "pending"
                ),
            )
        )

    comparison_ready = {"stock_only_fallback", "real_kospi"}.issubset(latest)
    status = (
        "Both modes are available. Metrics can be compared with the limitations below."
        if comparison_ready
        else "Comparison pending: both a fallback run and a real KOSPI run are required."
    )
    content = f"""# Index Mode Comparison

{status}

| market feature mode | index source | dataset rows | accuracy | f1 | roc auc | strategy return reference |
|---|---|---:|---:|---:|---:|---:|
{chr(10).join(rows)}

## Interpretation Limits

- 각 실행의 inner join 결과와 학습 행 수가 다르면 완전히 동일한 표본의 비교가 아니다.
- 단일 train/validation/test 시간 분할 결과이며 모델 안정성을 보장하지 않는다.
- 백테스트의 5영업일 보유 거래는 서로 겹칠 수 있어 실제 포트폴리오 수익률이 아니다.
- 이 비교는 교육 및 분석용이며 투자 추천이 아니다.
"""
    path = report_dir / "index_mode_comparison.md"
    path.write_text(content, encoding="utf-8")
    return path
