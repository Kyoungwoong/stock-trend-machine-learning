# RULE.md

## 1. 프로젝트 핵심 규칙

이 프로젝트는 공개 금융 데이터를 활용한 교육/분석용 머신러닝 프로젝트다. 투자 자문, 매매 신호, 수익 보장을 목적으로 하지 않는다.

## 2. 데이터 규칙

- 원천 데이터는 `data/raw/`에 저장한다.
- 정제 중간 결과는 `data/interim/`에 저장한다.
- 학습용 최종 데이터셋은 `data/processed/`에 저장한다.
- raw 데이터는 가능한 한 수정하지 않는다.
- API 응답 스키마가 바뀌면 `reports/data_summary.md`에 기록한다.

## 3. 시간 규칙

- 모든 데이터는 `date` 컬럼을 기준으로 정렬한다.
- 날짜 컬럼은 pandas datetime으로 변환한다.
- train/test는 랜덤이 아니라 날짜 기준으로 나눈다.
- 오늘 예측에는 오늘 장마감 시점까지 알 수 있는 값만 사용한다.

## 4. Label 규칙

기본 label은 향후 5영업일 수익률 기준이다.

```text
future_return_5d = close.shift(-5) / close - 1
label_up_5d = 1 if future_return_5d > 0 else 0
```

주의:

- 마지막 5개 행은 label을 만들 수 없으므로 학습에서 제외한다.
- `future_return_5d`는 평가/백테스트용으로만 사용하고 모델 feature에서 제외한다.

## 5. Feature 규칙

1차 feature는 OHLCV와 시장지수 기반으로 제한한다.

허용:

- 과거 수익률
- 이동평균
- 거래량 변화율
- rolling volatility
- 시장지수 수익률
- 시장 대비 초과수익률

1차 금지:

- 뉴스 감성분석
- 공시 전문 NLP
- LSTM/Transformer용 sequence feature
- 전체 종목 랭킹 feature
- 미래 가격을 포함한 모든 파생변수

## 6. 모델 규칙

1차 모델은 설명 가능하고 구현이 단순한 모델부터 사용한다.

- LogisticRegression
- RandomForestClassifier

XGBoost/LightGBM은 2차 개선 단계에서 추가한다.

## 7. 평가 규칙

ML 지표와 투자 성과를 분리한다.

ML 지표:

- accuracy
- precision
- recall
- f1-score
- roc-auc
- confusion matrix

전략 지표:

- 모델 매수일 평균 5영업일 수익률
- buy-and-hold 수익률
- 거래 횟수
- 승률
- 최대 낙폭
- 거래비용 반영 후 수익률

## 8. 문서화 규칙

- 실험 결과는 `reports/`에 남긴다.
- 실패한 실험도 남긴다.
- 블로그용 설명은 과장하지 않는다.
- “수익률 보장”, “종목 추천”, “AI 매매” 같은 표현은 쓰지 않는다.

## 9. 보안 규칙

- API 키는 `.env`에만 둔다.
- `.env`는 커밋하지 않는다.
- `.env.example`에는 키 이름만 남긴다.

## 10. 커밋 전 체크

- [ ] `python src/data_pipeline.py --ticker 005930 --start 2018-01-01 --end 2025-12-31 --use-sample` 실행 가능
- [ ] `python src/train.py --ticker 005930` 실행 가능
- [ ] `python src/evaluate.py --ticker 005930` 실행 가능
- [ ] `python src/backtest.py --ticker 005930` 실행 가능
- [ ] `.env`가 커밋 대상에 없음
- [ ] 미래 데이터가 feature에 포함되지 않음
