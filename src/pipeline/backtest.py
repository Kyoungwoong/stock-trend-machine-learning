from __future__ import annotations

import argparse

import joblib
import numpy as np
import pandas as pd

from src.core.config import SETTINGS
from src.core.storage import load_parquet, write_report
from src.pipeline.train import split_by_date


def max_drawdown(equity_curve: pd.Series) -> float:
    running_max = equity_curve.cummax()
    drawdown = equity_curve / running_max - 1
    return float(drawdown.min())


def backtest(ticker: str, trading_cost: float = 0.0015) -> None:
    dataset_path = SETTINGS.data_dir / "processed" / f"{ticker}_dataset.parquet"
    model_path = SETTINGS.model_dir / f"{ticker}_model.joblib"
    df = load_parquet(dataset_path).sort_values("date")
    artifact = joblib.load(model_path)
    model = artifact["model"]
    feature_columns = artifact["feature_columns"]

    _, _, test_df = split_by_date(df)
    x_test = test_df[feature_columns]
    pred = model.predict(x_test)

    bt = test_df[["date", "ticker", "close", "future_return_5d"]].copy()
    bt["prediction"] = pred
    bt["strategy_return"] = np.where(bt["prediction"] == 1, bt["future_return_5d"] - trading_cost, 0.0)
    bt["buy_and_hold_5d_return"] = bt["future_return_5d"]

    # 겹치는 5일 보유 거래를 단순 합산하면 과대해석될 수 있으므로, 여기서는 거래별 평균과 단순 누적 equity만 참고용으로 본다.
    strategy_trades = bt[bt["prediction"] == 1]
    strategy_equity = (1 + bt["strategy_return"].fillna(0)).cumprod()
    hold_daily_return = bt["close"].pct_change().fillna(0)
    hold_equity = (1 + hold_daily_return).cumprod()

    metrics = {
        "test_rows": len(bt),
        "trade_count": int((bt["prediction"] == 1).sum()),
        "avg_strategy_trade_return": float(strategy_trades["strategy_return"].mean()) if not strategy_trades.empty else 0.0,
        "win_rate": float((strategy_trades["strategy_return"] > 0).mean()) if not strategy_trades.empty else 0.0,
        "strategy_total_return_reference": float(strategy_equity.iloc[-1] - 1),
        "buy_and_hold_return": float(hold_equity.iloc[-1] - 1),
        "strategy_max_drawdown_reference": max_drawdown(strategy_equity),
        "buy_and_hold_max_drawdown": max_drawdown(hold_equity),
        "trading_cost_per_trade": trading_cost,
    }

    content = f"""
# Backtest Summary

## Rule

모델이 `상승`이라고 예측한 날만 매수하고, 향후 5영업일 수익률을 거래별 수익률로 계산한다.
거래비용은 거래당 `{trading_cost:.4%}`로 차감한다.

## Metrics

| metric | value |
|---|---:|
{chr(10).join(f'| {name} | {value:.4f} |' if isinstance(value, float) else f'| {name} | {value} |' for name, value in metrics.items())}

## Important Notes

- 이 백테스트는 교육용 단순 백테스트다.
- 5영업일 보유 거래가 매일 겹칠 수 있으므로 실제 포트폴리오 수익률로 해석하면 안 된다.
- ML 지표가 좋아도 거래비용 반영 후 수익률이 낮을 수 있다.
- 투자 추천이나 매매 신호가 아니다.
"""
    write_report(SETTINGS.report_dir / "backtest_summary.md", content.strip() + "\n")
    print(content)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ticker", default=SETTINGS.default_ticker)
    parser.add_argument("--trading-cost", type=float, default=0.0015)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    backtest(args.ticker, trading_cost=args.trading_cost)


if __name__ == "__main__":
    main()
