# Study Note: 현재 ML 개념과 다음 학습 로드맵

## What I Should Learn

- 현재 프로젝트가 해결하는 supervised binary classification 문제
- feature, label, prediction probability의 차이
- 금융 시계열에서 데이터 누수와 시간 순서 검증이 중요한 이유
- Logistic Regression과 Random Forest의 역할과 한계
- accuracy 외 평가 지표와 백테스트 지표를 구분하는 방법
- 현재 결과 다음에 walk-forward validation부터 발전시켜야 하는 이유

## Why It Matters

머신러닝을 처음 공부하면 모델 알고리즘부터 배우기 쉽다. 그러나 이 프로젝트에서 더 중요한 것은 “어떤 시점에 알 수 있었던 정보로 어떤 미래를 예측했는가”이다. 문제 정의와 검증이 잘못되면 복잡한 모델도 의미가 없다.

현재 실제 KOSPI 실행의 test accuracy는 0.4599, F1은 0.4921, ROC-AUC는 0.4448이다. 한 번의 기간 분할 결과이므로 모델이 유효하거나 무효하다고 단정할 수 없다. 다음 단계는 모델을 복잡하게 만드는 것이 아니라 여러 시간 구간에서 결과가 반복되는지 검증하는 것이다.

## Key Concepts

### 1. 현재 문제: 지도학습 이진 분류

지도학습은 입력 `X`와 정답 `y`의 예제를 이용해 관계를 학습한다. 현재 프로젝트의 한 행은 한 거래일이다.

```text
X = 오늘 장 마감까지 계산할 수 있는 21개 feature
y = 5영업일 뒤 종가 수익률이 0보다 큰가
```

정답은 두 종류뿐이므로 binary classification이다.

- `1`: 향후 5영업일 수익률이 양수
- `0`: 향후 5영업일 수익률이 0 이하

모델은 미래 가격 자체를 예측하는 regression이 아니라 상승 여부와 상승 class의 확률을 출력한다.

### 2. feature와 label

feature는 모델이 예측할 때 알고 있는 입력값이다. label은 맞혀야 할 미래 정답이다.

| 컬럼 | 시점 | 용도 |
|---|---|---|
| `return_5d` | 오늘과 5영업일 전 | feature 가능 |
| `future_return_5d` | 오늘과 5영업일 뒤 | label 생성·평가용, feature 금지 |
| `label_up_5d` | 미래 수익률로 생성 | 정답, feature 금지 |

이 차이는 방향에 있다.

```text
return_5d[t]        = close[t]   / close[t-5] - 1
future_return_5d[t] = close[t+5] / close[t]   - 1
```

### 3. 데이터 누수

데이터 누수는 실제 예측 시점에 알 수 없는 정보가 학습이나 검증에 들어가는 문제다. 누수가 있으면 report 점수는 높아지지만 실전에서는 재현되지 않는다.

현재 코드의 방어선은 다음과 같다.

- `FEATURE_COLUMNS`에 미래 수익률과 label을 넣지 않는다.
- `validate_feature_columns()`가 금지 컬럼 포함 여부를 다시 검사한다.
- rolling feature는 장 마감 후 예측을 전제로 현재와 과거 행만 사용한다.
- train, validation, test를 날짜순으로 분리하고 random shuffle을 사용하지 않는다.
- 실제 지수와 주식은 동일한 거래일끼리만 결합한다.

현재일 종가를 rolling 평균에 포함하는 것은 누수가 아니다. 이 모델의 예측 시점이 장 마감 후이기 때문이다. 장 시작 전 예측 모델로 바꾸면 현재일 종가는 사용할 수 없으므로 feature를 한 칸 지연해야 한다.

### 4. Feature engineering

Feature engineering은 원본 데이터를 모델이 학습하기 쉬운 표현으로 바꾸는 과정이다.

- 수익률: 가격 수준보다 기간별 상대 변화를 표현한다.
- 이동평균: 짧고 긴 기간의 가격 추세를 요약한다.
- 이동평균 괴리율: 현재 가격이 평균보다 얼마나 위나 아래인지 표현한다.
- 거래량 변화와 평균: 시장 참여 활동의 변화를 나타낸다.
- 변동성: 최근 수익률이 얼마나 흔들렸는지 표준편차로 나타낸다.
- 시장 수익률: 개별 종목과 KOSPI가 함께 움직인 부분을 보여준다.
- 초과수익률: 종목 수익률에서 같은 기간 시장 수익률을 뺀다.

60일 이동평균은 첫 59개 행에서 계산할 수 없다. feature 생성 후 결측 행을 제거하기 때문에 processed 데이터의 시작일이 raw 데이터보다 늦어진다. 이것은 오류가 아니라 warm-up period다.

### 5. 전처리 Pipeline

scikit-learn의 `Pipeline`은 전처리와 모델을 정해진 순서로 묶는다.

- `SimpleImputer(strategy="median")`: 결측값을 train 데이터의 중앙값으로 대체한다.
- `StandardScaler`: 각 feature의 크기를 비슷한 범위로 변환한다.
- classifier: 전처리된 입력으로 class를 학습한다.

전처리기가 `fit()`될 때 train 데이터만 보는 것이 중요하다. 전체 데이터로 중앙값과 평균을 먼저 계산하면 validation/test 분포가 train에 새어 들어간다. 현재 코드는 Pipeline 전체를 `x_train`에 fit하므로 이 누수를 피한다.

### 6. Logistic Regression

이름에 Regression이 있지만 여기서는 classification 모델이다. feature의 가중합을 sigmoid 함수로 0~1 확률로 바꾼다.

장점:

- 빠르고 단순하다.
- feature와 결과의 선형 관계를 출발점으로 보기 좋다.
- scaling과 결합한 baseline으로 설명하기 쉽다.

한계:

- 복잡한 비선형 관계와 feature 상호작용을 스스로 충분히 표현하지 못할 수 있다.
- 계수 해석은 feature 상관관계와 scaling을 함께 고려해야 한다.

### 7. Random Forest

여러 decision tree를 서로 조금 다른 데이터와 feature로 학습하고 결과를 합친 ensemble 모델이다.

장점:

- 비선형 관계와 feature 상호작용을 표현할 수 있다.
- scaling이 필수적이지 않다.
- 단일 tree보다 과적합을 완화할 수 있다.

한계:

- 시간 변화에 자동으로 대응하지 않는다.
- feature가 많거나 데이터가 적으면 여전히 불안정할 수 있다.
- 기본 importance만 보고 인과관계로 해석하면 안 된다.

현재 프로젝트는 두 모델 중 validation accuracy가 높은 하나를 선택한다. 복잡한 모델을 추가하기 전에 검증 구조가 믿을 만한지 확인하려는 선택이다.

### 8. train, validation, test

| 구간 | 질문 |
|---|---|
| train | 모델이 어떤 패턴을 배울 것인가? |
| validation | 후보 모델 중 무엇을 선택할 것인가? |
| test | 선택 과정에서 보지 않은 미래 구간에서도 결과가 유지되는가? |

test 결과를 보고 모델이나 feature를 반복 수정하면 test도 선택 과정에 들어간다. 그때는 더 뒤의 새로운 기간이 필요하다.

### 9. 분류 평가 지표

먼저 confusion matrix의 네 경우를 이해한다.

- TP: 상승이라고 예측했고 실제 상승
- FP: 상승이라고 예측했지만 실제 비상승
- FN: 비상승이라고 예측했지만 실제 상승
- TN: 비상승이라고 예측했고 실제 비상승

| 지표 | 핵심 질문 |
|---|---|
| accuracy | 전체 예측 중 몇 개가 맞았는가? |
| precision | 상승 예측 중 실제 상승 비율은? |
| recall | 실제 상승 중 몇 개를 상승으로 찾았는가? |
| F1 | precision과 recall의 조화 평균은? |
| ROC-AUC | threshold를 바꿀 때 양성과 음성을 얼마나 잘 순위화하는가? |

상승/비상승 비율이 불균형하면 accuracy만으로 판단하기 어렵다. 또한 ROC-AUC가 0.5 근처면 확률 순위가 무작위와 비슷하다는 신호지만, 단일 기간 결과만으로 일반화하면 안 된다.

### 10. ML 지표와 백테스트 지표

ML 평가는 예측의 통계적 품질을 묻고, 백테스트는 예측을 거래 규칙으로 바꾸었을 때의 결과를 묻는다.

- precision은 상승 예측의 적중 비율과 관련되지만 거래 수익의 크기는 반영하지 않는다.
- win rate가 높아도 손실 거래의 크기가 크면 전체 수익률은 낮을 수 있다.
- 거래비용은 작은 예측 우위를 없앨 수 있다.
- max drawdown은 최고점 대비 가장 큰 하락을 보여준다.
- buy-and-hold는 모델 전략을 비교하기 위한 단순 기준선이다.

현재 백테스트는 겹치는 5일 거래를 독립적으로 누적하므로 실제 포트폴리오 회계가 아니다.

### 11. 다음 학습 로드맵

#### 1순위: Walk-forward validation

현재 한 번의 분할만으로는 특정 기간에 우연히 잘 맞았는지 알기 어렵다. 여러 기준 시점을 이동하며 “과거로 학습하고 바로 다음 기간을 검증”해야 한다.

공부할 것:

- expanding window와 rolling window
- fold별 train/validation 기간
- fold별 지표 평균뿐 아니라 분산과 최악 구간
- 각 fold에서 전처리와 모델을 새로 fit하는 이유

완료 판단:

- 모든 fold가 날짜순이고 겹침 정책이 명확하다.
- fold별 지표와 기간이 report에 남는다.
- 미래 fold 데이터가 과거 학습에 들어가지 않는다.

#### 2순위: 모델 안정성과 feature importance

walk-forward 결과가 구간마다 크게 다르면 어떤 feature가 어느 구간에서 작동했는지 확인한다. Random Forest의 기본 importance만 사용하지 않고 permutation importance를 우선 공부한다.

완료 판단:

- importance는 train이 아닌 validation/test 성능 변화로 계산한다.
- importance를 인과관계나 투자 근거로 표현하지 않는다.
- 여러 fold에서 방향과 순위가 유지되는지 비교한다.

#### 3순위: 백테스트 현실화

ML 성능과 투자 성과의 차이가 확인되면 포지션 겹침, 자본 배분, 진입·청산 시점, 거래비용을 명확히 한다.

완료 판단:

- 동시에 보유할 수 있는 포지션 수와 자본 사용 규칙이 있다.
- 신호 생성 시점보다 앞선 가격으로 체결하지 않는다.
- benchmark와 동일한 평가 기간을 사용한다.

#### 4순위: 다종목과 일반화

단일 삼성전자 모델의 패턴이 다른 종목에서도 유지되는지 확인한다. 종목별 모델과 통합 모델을 비교하고 생존편향을 문서화한다.

#### 5순위: Point-in-time 외부 데이터

DART 재무제표와 ECOS 경제지표를 추가할 때는 값의 기준일이 아니라 당시 사용자가 실제로 알 수 있었던 공시·발표일을 사용한다. 이 단계는 feature 수를 늘리는 작업이 아니라 시점 정합성을 지키는 데이터 엔지니어링 작업이다.

## Related Concepts To Study Next

- `TimeSeriesSplit`, expanding window, rolling window
- 지표의 평균, 표준편차, confidence interval
- permutation importance와 feature correlation
- probability calibration과 decision threshold
- transaction cost, slippage, overlapping position
- survivorship bias와 point-in-time data

## Common Mistakes

- test accuracy가 한 번 높았다는 이유로 모델이 일반화된다고 판단하는 것
- random split이나 shuffle로 미래와 과거를 섞는 것
- 전체 데이터로 imputer와 scaler를 먼저 fit하는 것
- `future_return_5d`를 feature로 넣어 성능을 인위적으로 높이는 것
- feature importance를 원인이나 투자 추천으로 해석하는 것
- 더 복잡한 모델을 검증 신뢰성보다 먼저 추가하는 것
- 겹치는 거래를 단순 복리 계산해 실제 계좌 수익률이라고 표현하는 것
- 공시 결산일이나 경제지표 대상 월을 곧바로 사용 가능일로 간주하는 것

## How This Appears In Our Code

- 문제의 입력: `src/domain/features.py`의 `FEATURE_COLUMNS`
- 문제의 정답: `src/domain/labeling.py`
- 시간 분할과 전처리 Pipeline: `src/pipeline/train.py`
- 분류 지표: `src/pipeline/evaluate.py`
- 거래 지표: `src/pipeline/backtest.py`
- 누수 방지 테스트: `tests/test_features.py`, `tests/test_labeling.py`
- 다음 단계: `docs/project/ROADMAP.md`의 Phase 2 walk-forward validation

## Blog Angle

“좋은 모델보다 먼저 믿을 수 있는 검증을 만든 이유”로 구성할 수 있다. 과거 수익률과 미래 수익률의 한 줄 차이에서 데이터 누수를 설명하고, 단일 split 결과의 한계를 보여준 뒤 walk-forward validation으로 이어가면 프로젝트의 학습 목표와 다음 개발 단계가 자연스럽게 연결된다.
