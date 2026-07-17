# Index Mode Comparison

Both modes are available. Metrics can be compared with the limitations below.

| market feature mode | index source | dataset rows | accuracy | f1 | roc auc | strategy return reference |
|---|---|---:|---:|---:|---:|---:|
| stock_only_fallback | stock_only_fallback | 1409 | 0.4473 | 0.4781 | 0.4525 | 1.0591 |
| real_kospi | fsc | 1409 | 0.4599 | 0.4921 | 0.4448 | 1.0470 |

## Interpretation Limits

- 각 실행의 inner join 결과와 학습 행 수가 다르면 완전히 동일한 표본의 비교가 아니다.
- 단일 train/validation/test 시간 분할 결과이며 모델 안정성을 보장하지 않는다.
- 백테스트의 5영업일 보유 거래는 서로 겹칠 수 있어 실제 포트폴리오 수익률이 아니다.
- 이 비교는 교육 및 분석용이며 투자 추천이 아니다.
