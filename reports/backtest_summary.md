# Backtest Summary

## Data Context

| field | value |
|---|---|
| index_source | `fsc` |
| fallback_applied | `False` |
| fallback_reason | `None` |
| index_normalized_rows | `1473` |
| merged_rows | `1473` |
| uses_real_kospi | `True` |
| market_feature_mode | `real_kospi` |

This run used real KOSPI index data. 실제 KOSPI 지수가 날짜 기준으로 결합되었습니다.

## Rule

모델이 `상승`이라고 예측한 날만 매수하고, 향후 5영업일 수익률을 거래별 수익률로 계산한다.
거래비용은 거래당 `0.1500%`로 차감한다.

## Metrics

| metric | value |
|---|---:|
| test_rows | 237 |
| trade_count | 107 |
| avg_strategy_trade_return | 0.0077 |
| win_rate | 0.5794 |
| strategy_total_return_reference | 1.0470 |
| buy_and_hold_return | 1.0693 |
| strategy_max_drawdown_reference | -0.4427 |
| buy_and_hold_max_drawdown | -0.1467 |
| trading_cost_per_trade | 0.0015 |

## Important Notes

- 이 백테스트는 교육용 단순 백테스트다.
- 5영업일 보유 거래가 매일 겹칠 수 있으므로 실제 포트폴리오 수익률로 해석하면 안 된다.
- ML 지표가 좋아도 거래비용 반영 후 수익률이 낮을 수 있다.
- 투자 추천이나 매매 신호가 아니다.
