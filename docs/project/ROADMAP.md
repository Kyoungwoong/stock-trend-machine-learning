# ROADMAP.md

## Phase 0. Skeleton 구성

- [x] 프로젝트 디렉터리 구조 작성
- [x] README 작성
- [x] AGENTS, RULE, CODE_REVIEW_RULES 작성
- [x] 샘플 데이터 실행 흐름 작성

## Phase 1. 단일 종목 OHLCV 기반 모델

- [x] 공공데이터포털 주식시세 API 키 발급
- [x] 삼성전자 `005930` 일별 시세 수집
- [x] KOSPI 지수 일별 시세 수집
- [x] 종목/지수 데이터 병합
- [x] 5영업일 label 생성
- [x] 기본 feature 생성
- [x] LogisticRegression 학습
- [x] RandomForest 학습
- [x] 시간 순서 기반 평가
- [x] 모델 예측 결과 저장

## Phase 2. 백테스트와 검증 강화

- [x] 단순 매수/매도 규칙 정의
- [x] 거래비용 반영
- [x] buy-and-hold 비교
- [x] confusion matrix와 수익률 비교
- [ ] walk-forward validation 추가

## Phase 3. 종목군 확장

- [ ] KOSPI 대형주 20개 선정
- [ ] 종목별 데이터 수집 자동화
- [ ] 종목별 모델 vs 통합 모델 비교
- [ ] 생존편향과 종목 변경 이슈 문서화

## Phase 4. 외부 지표 추가

- [ ] 금융투자협회 시장자금 지표 추가
- [ ] OpenDART 재무제표 추가
- [ ] 한국은행 ECOS 금리/환율 추가
- [ ] point-in-time merge 구현

## Phase 5. 포트폴리오/블로그 완성

- [ ] 최종 보고서 작성
- [ ] 블로그 10편 초안 작성
- [ ] GitHub README 보강
- [ ] 한계점 정리
- [ ] 다음 프로젝트 아이디어 정리
