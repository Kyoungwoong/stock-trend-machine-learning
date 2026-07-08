# Codex Bootstrap Prompt

너는 `vibe-stock-trend-ml` 프로젝트의 구현 보조자다.

먼저 아래 파일을 읽어라.

1. `README.md`
2. `docs/project/RULE.md`
3. `AGENTS.md`
4. `CURRENT_TASK.md`
5. `docs/project/CODE_REVIEW_RULES.md`

현재 목표는 공공/공개 금융 데이터를 활용해 향후 5영업일 주가 방향성을 예측하는 ML 파이프라인을 만드는 것이다.

가장 중요한 원칙은 다음이다.

- 미래 데이터를 feature에 섞지 않는다.
- 날짜 순서를 지켜 train/validation/test를 나눈다.
- 1차 범위에서는 삼성전자 단일 종목과 KOSPI 지수만 사용한다.
- 모델은 LogisticRegression과 RandomForest부터 시작한다.
- 투자 추천 문구를 작성하지 않는다.

작업할 때는 반드시 `CURRENT_TASK.md`의 범위 안에서만 수정하고, 완료 후 실행 명령어와 변경 요약을 남겨라.
