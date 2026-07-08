# Backtest Summary

## Rule

모델이 `상승`이라고 예측한 날만 매수하고, 향후 5영업일 수익률을 거래별 수익률로 계산한다.
거래비용은 거래당 `0.1500%`로 차감한다.

## Metrics

| metric | value |
|---|---:|
| test_rows | 256 |
| trade_count | 220 |
| avg_strategy_trade_return | -0.0131 |
| win_rate | 0.4000 |
| strategy_total_return_reference | -0.9537 |
| buy_and_hold_return | -0.5230 |
| strategy_max_drawdown_reference | -0.9584 |
| buy_and_hold_max_drawdown | -0.5333 |
| trading_cost_per_trade | 0.0015 |

## Important Notes

- 이 백테스트는 교육용 단순 백테스트다.
- 5영업일 보유 거래가 매일 겹칠 수 있으므로 실제 포트폴리오 수익률로 해석하면 안 된다.
- ML 지표가 좋아도 거래비용 반영 후 수익률이 낮을 수 있다.
- 투자 추천이나 매매 신호가 아니다.
