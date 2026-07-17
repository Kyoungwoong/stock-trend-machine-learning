# Phase 1-4 실행 metadata 및 KOSPI 활성화 판정

## 목적

지수 API 호출 성공 여부가 아니라 모델 feature에 실제 KOSPI가 반영됐는지를 판정하고 fallback 모델을 시장 대비 모델로 오해하지 않게 한다.

## 무엇을 했는가

- 지수 출처, fallback 원인, 정규화/병합 행 수를 `reports/run_metadata.json`에 저장했다.
- 실제 KOSPI, 합성 샘플, stock-only fallback을 별도 `market_feature_mode`로 구분했다.
- 실제 지수 모드에서 시장 수익률과 초과수익률이 fallback 값과 다른지 검증했다.
- metadata를 모델 artifact에 저장해 평가, 백테스트, 예측이 같은 실행 상태를 사용하게 했다.
- fallback 해석 제한을 모델/백테스트 보고서와 예측 출력에 표시했다.
- 선택 모델명과 test accuracy, F1, ROC-AUC를 같은 JSON에 단계별로 추가했다.
- 평가와 백테스트 완료 metadata를 `reports/runs/`에 실행별로 보존하고 지수 모드 비교 보고서를 생성한다.
- API 예외에 인증키가 포함되어도 report 저장 전에 원문과 URL 인코딩 값을 `[REDACTED]`로 치환한다.

## 어떻게 구현했는가

데이터 파이프라인이 feature 생성 후 metadata를 만든다. 학습은 ticker를 검증하고 metadata 스냅샷을 모델에 저장한다. 평가는 모델 스냅샷과 현재 JSON의 생성 시각이 같은지 확인한 뒤 test 지표를 추가하므로 다른 실행 결과가 조용히 섞이지 않는다.

실제 지수와 겹치는 거래일이 없거나 시장 feature 검증이 실패하면 stock-only feature를 다시 생성하고 fallback 원인을 기록한다. API 오류에는 endpoint와 상태만 사용하며 인증키 값은 저장하지 않는다.

## 왜 이렇게 했는가

- `fallback_applied=false`만으로는 합성 샘플과 실제 KOSPI를 구분할 수 없다.
- 최신 JSON을 무조건 사용하면 다른 데이터 실행의 상태가 기존 모델에 잘못 붙을 수 있다.
- 행 수와 feature 값 검증을 함께 해야 빈 응답이나 잘못된 병합을 성공으로 오판하지 않는다.
- fallback 실행은 유지하되 성능 숫자의 해석 범위를 명확히 제한해야 한다.

## 공부할 내용

### 데이터 계보와 실행 식별자

데이터셋, 모델, 평가 결과를 연결하는 data lineage와 run ID를 학습한다. 이번 구현에서는 생성 시각을 최소 실행 식별자로 사용한다.

### 데이터 품질 검증

행 수, 날짜 범위, 분산, 결측률 검증과 Great Expectations 같은 도구가 필요한 시점을 비교한다.

### 모델 artifact 재현성

모델과 함께 feature 목록, 학습 기간, 데이터 출처와 라이브러리 버전을 저장해야 하는 이유를 학습한다.

### Fallback 설계

외부 API 장애 시 중단, 캐시, 기능 축소 중 어떤 정책을 선택할지와 결과의 한계를 표시하는 방법을 학습한다.

## 최종 검증 결과

- FSC 지수 API가 정상 응답해 실제 KOSPI 지수 1,473행을 수집했다.
- `uses_real_kospi=true`, `market_feature_mode=real_kospi` 검증을 통과했다.
- controlled stock-only baseline과 실제 지수 모델의 accuracy, F1, ROC-AUC 및 백테스트 참고 지표를 비교 보고서에 저장했다.
- 실제 지수 모델의 accuracy와 F1은 소폭 높았지만 ROC-AUC와 백테스트 참고 수익률은 낮아졌다. 단일 분할만으로 우열을 결론내리지 않는다.
