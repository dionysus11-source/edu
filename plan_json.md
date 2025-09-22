# 데이터셋 생성 계획

- 새 레코드는 모두 `defect_type: 3`으로 통일하고 `has_defect`로 결함 여부를 표현한다.
- 총 500개 샘플을 생성하며 결함/정상 비율은 대략 1:1로 유지한다.
- 주요 결함 패턴: Newtonsoft.Json 사용, 대규모 일괄 적재(`ReadAllText`, `Parse`, `ToArray()` 등), 동기식 대용량 I/O, 대형 버퍼 및 StringBuilder 재할당, System.Text.Json 기반 값 비교.
- 주요 정상 패턴: System.Text.Json 소스 생성, `Utf8JsonReader` 스트리밍, `ArrayPool<T>` 재사용, `JsonSerializerOptions` 캐시, `Tizen.TV.JsonMap` 값 검증.
- 각 패턴은 비슷한 도메인 시나리오로 결함/정상 짝을 이루도록 작성해 모델이 교차 비교 학습을 할 수 있도록 한다.
- 500개 샘플을 50개 단위로 나누어 `@defect_json.jsonl`에 순차적으로 추가하고, 각 배치 완료 시 사용자에게 진행 상황을 보고한다.
