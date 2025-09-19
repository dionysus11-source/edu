## 2024-09-19 Progress Snapshot

- `train_code_for_mac.py`
  - 확장된 `compute_metrics`로 정확도뿐 아니라 정상/결함 클래스별 precision·recall·F1·support를 계산.
  - `MetricsCSVLogger` 콜백을 도입하여 매 평가마다 `logs/metrics_history.csv`에 지표를 기록.
- `plot_metrics.py`
  - `logs/metrics_history.csv`를 읽어 에폭별 주요 지표 곡선을 그리고 `metrics.png`로 저장.
- `classify_code.py`
  - `boxing-classifier-final/` 모델을 로드하여 CLI에서 코드 스니펫을 정상/결함으로 분류.
- 문서
  - `AGENTS.md`에 저장소 가이드라인 정리.
  - `items.md`에 논문 아이템 목록 작성.
  - `METRICS.md`에 지표 로깅·시각화 사용법 기록.
- 산출물
  - `logs/metrics_history.csv`: 에폭별 평가 지표.
  - `metrics.png`: 지표 그래프 이미지.
