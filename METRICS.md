## Metrics Logging Workflow
- `train_code_for_mac.py` now 기록: 평가 시마다 `logs/metrics_history.csv`에 정확도와 클래스별 정밀도/재현율/F1을 추가합니다.
- CSV에는 열 이름이 `eval_*` 형태로 저장되며 `epoch` 컬럼 기준으로 정렬됩니다.
- 학습 후 `python plot_metrics.py --metrics-file logs/metrics_history.csv --output metrics.png`를 실행하면 주요 메트릭 변화를 한 그래프로 확인할 수 있습니다.
- 다른 지표를 보고 싶다면 `--metrics eval_defect_precision eval_normal_recall` 형태로 열 이름을 지정하세요.
