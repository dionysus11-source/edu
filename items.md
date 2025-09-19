## 연구 아이템 제안

- 과제 개요: C#/Tizen API 코드 조각을 입력으로 받아 성능 결함(로깅 미흡, 경량화 위반 등) 여부를 판별하는 바이너리 분류 모델을 구축한다. `train_code_for_mac.py`로 CodeBERT 기반 분류기를 학습하고, `test_model.py`로 정확도·정밀도·재현율·F1과 클래스별 리콜을 평가하며 `enhanced_boxing_dataset.jsonl`·`test_dataset/`을 활용한다.
1. 데이터 구축 전략: JSONL 구조 설계, `has_defect`·`defect_type` 다중 라벨 주석 기준, 리뷰 프로세스 기록으로 라벨 품질 관리.
2. 언어 혼합 처리: 한국어 주석과 C#/Tizen API 코드 혼합 입력에서의 토크나이즈 문제와 커스텀 전처리(토큰 병합, 정규화) 실험 결과.
3. 모델 선택 비교: CodeBERT 기반 분류기와 대조군(예: 일반 도메인 RoBERTa, 소형 CodeParrot)·대형 코드 LLM(예: StarCoder 베이스) 간 학습/추론 비용, macro F1, 소수 클래스 리콜을 비교하여 CodeBERT가 균형 성능·경량성을 동시에 확보함을 입증.
4. 데이터 불균형 대응: 결함 유형별 비중 격차를 줄이기 위한 클래스 가중치, 재표본, focal loss 비교 실험과 성능 분석.
5. 멀티태스크 전환: 이진 분류 vs. 다중/계층 분류(1차 결함 여부 + 2차 유형 분류) 구조 실험, 혼동 행렬·지표 비교.
6. 모델 해석 가능성: `test_single_text` 확장, Integrated Gradients/Attention rollout 기반 토큰 중요도 시각화 사례.
7. 경량화 및 배포: `classify_code.py` CLI, 온디바이스 추론 실험, 모델 양자화·지연 로딩으로 성능/자원 트레이드오프 검토.
8. 한계와 향후 과제: 라벨 노이즈, 코드 스타일 다양성 확대 필요성, 코드 변형/주석 번역 증강과 액티브 러닝, 규칙 기반 결합 전략 제안.
