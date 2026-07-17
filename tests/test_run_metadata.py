import json

import pandas as pd
import pytest

from src.core.run_metadata import (
    build_run_metadata,
    interpretation_notice,
    load_run_metadata,
    metadata_from_artifact,
    metadata_markdown,
    redact_secrets,
    snapshot_run_metadata,
    update_matching_run_metadata,
    write_index_mode_comparison,
    write_run_metadata,
)
from src.domain.features import add_price_features
from src.pipeline.data_pipeline import build_dataset, validate_market_features


def make_metadata(**overrides):
    values = {
        "ticker": "005930",
        "start": "2018-01-01",
        "end": "2025-12-31",
        "use_sample": False,
        "index_source": "fsc",
        "fallback_applied": False,
        "fallback_reason": None,
        "index_normalized_rows": 80,
        "merged_rows": 80,
        "stock_raw_rows": 80,
        "stock_normalized_rows": 80,
        "index_raw_rows": 80,
        "dataset_rows": 15,
        "dataset_start": "2024-03-25",
        "dataset_end": "2024-04-12",
        "latest_feature_date": "2024-04-19",
        "index_fetch_warnings": [],
        "market_feature_validation_passed": True,
    }
    values.update(overrides)
    return build_run_metadata(**values)


def test_real_index_metadata_is_distinct_from_sample_and_fallback():
    real = make_metadata()
    sample = make_metadata(use_sample=True, index_source="sample", market_feature_validation_passed=False)
    fallback = make_metadata(
        index_source="stock_only_fallback",
        fallback_applied=True,
        fallback_reason="FSC returned 403; KRX key was not set",
        index_normalized_rows=0,
        market_feature_validation_passed=False,
    )

    assert real.uses_real_kospi is True
    assert real.market_feature_mode == "real_kospi"
    assert sample.uses_real_kospi is False
    assert sample.market_feature_mode == "sample_index"
    assert fallback.uses_real_kospi is False
    assert fallback.market_feature_mode == "stock_only_fallback"


def test_run_metadata_json_contains_required_fields_without_api_key(tmp_path):
    metadata = make_metadata(
        index_source="stock_only_fallback",
        fallback_applied=True,
        fallback_reason="FSC index API returned 403 and KRX key was not set",
        index_normalized_rows=0,
        index_fetch_warnings=["HTTP 403"],
        market_feature_validation_passed=False,
    )
    path = tmp_path / "run_metadata.json"
    write_run_metadata(path, metadata)
    loaded = load_run_metadata(path)

    for field in ["index_source", "fallback_applied", "fallback_reason", "index_normalized_rows", "merged_rows"]:
        assert field in loaded
    json.loads(path.read_text(encoding="utf-8"))


def test_redact_secrets_handles_raw_and_encoded_values():
    secret = "abc+/=secret"
    message = "raw=abc+/=secret encoded=abc%2B%2F%3Dsecret"

    redacted = redact_secrets(message, [secret])

    assert secret not in redacted
    assert "abc%2B%2F%3Dsecret" not in redacted
    assert redacted.count("[REDACTED]") == 2


def test_fallback_report_notice_prevents_market_relative_interpretation():
    metadata = make_metadata(
        index_source="stock_only_fallback",
        fallback_applied=True,
        fallback_reason="KOSPI unavailable",
        index_normalized_rows=0,
        market_feature_validation_passed=False,
    ).to_dict()

    report = metadata_markdown(metadata)

    assert "Do not interpret this result as a market-relative model comparison." in report
    assert "실제 시장 대비 feature로 해석하면 안 됩니다" in report
    assert interpretation_notice(metadata) in report


def test_forced_stock_only_notice_is_not_reported_as_api_unavailable():
    metadata = make_metadata(
        index_source="stock_only_fallback",
        fallback_applied=True,
        fallback_reason="Stock-only baseline was explicitly requested with --force-stock-only.",
        index_normalized_rows=0,
        market_feature_validation_passed=False,
    ).to_dict()

    notice = interpretation_notice(metadata)

    assert "intentionally used" in notice
    assert "unavailable" not in notice


def test_market_feature_validation_detects_real_and_fallback_features():
    base = pd.DataFrame(
        {
            "date": pd.date_range("2024-01-01", periods=80, freq="B"),
            "close": range(100, 180),
            "volume": range(1000, 1080),
            "index_close": [2500 + index * 2 for index in range(80)],
        }
    )
    real_features = add_price_features(base)
    fallback_features = add_price_features(base.drop(columns="index_close"))

    assert validate_market_features(real_features, expect_real_index=True) is True
    assert validate_market_features(fallback_features, expect_real_index=True) is False


def test_old_model_artifact_without_metadata_is_rejected():
    with pytest.raises(RuntimeError, match="no run metadata"):
        metadata_from_artifact({"model": object()})


def test_sample_and_forced_stock_only_are_mutually_exclusive():
    with pytest.raises(ValueError, match="cannot be used together"):
        build_dataset("005930", "2024-01-01", "2024-12-31", use_sample=True, force_stock_only=True)


def test_metadata_update_rejects_different_run(tmp_path):
    path = tmp_path / "run_metadata.json"
    write_run_metadata(path, make_metadata())

    with pytest.raises(RuntimeError, match="does not match"):
        update_matching_run_metadata(path, expected_generated_at="different-run", test_accuracy=0.5)


def test_index_mode_comparison_requires_and_then_compares_both_modes(tmp_path):
    fallback = make_metadata(
        index_source="stock_only_fallback",
        fallback_applied=True,
        fallback_reason="KOSPI unavailable",
        index_normalized_rows=0,
        market_feature_validation_passed=False,
    ).to_dict()
    fallback.update(test_accuracy=0.45, test_f1=0.47, test_roc_auc=0.46)
    snapshot_run_metadata(tmp_path, fallback)

    report_path = write_index_mode_comparison(tmp_path)
    assert "Comparison pending" in report_path.read_text(encoding="utf-8")

    real = make_metadata(index_source="krx").to_dict()
    real.update(test_accuracy=0.52, test_f1=0.51, test_roc_auc=0.53)
    snapshot_run_metadata(tmp_path, real)

    report = write_index_mode_comparison(tmp_path).read_text(encoding="utf-8")
    assert "Both modes are available" in report
    assert "stock_only_fallback" in report
    assert "real_kospi" in report
