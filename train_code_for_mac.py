from transformers import (
    AutoTokenizer, 
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer,
    DataCollatorWithPadding
)
from datasets import Dataset
import pandas as pd
import json

# 데이터 로드
def load_boxing_dataset(file_path):
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            data.append(json.loads(line))
    return Dataset.from_pandas(pd.DataFrame(data))

# 데이터셋 로드
dataset = load_boxing_dataset('enhanced_boxing_dataset.jsonl')

# 모델과 토크나이저 초기화
model_name = "microsoft/codebert-base"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(
    model_name,
    num_labels=2,  # has_defect: 0 or 1
    problem_type="single_label_classification"
)

# 토크나이징 함수
def tokenize_function(examples):
    return tokenizer(
        examples["text"],
        truncation=True,
        padding=False,  # 동적 패딩 사용
        max_length=128  # 시퀀스 길이를 줄여 메모리 사용량 절감
    )

# 데이터셋 전처리
tokenized_dataset = dataset.map(tokenize_function, batched=True)
tokenized_dataset = tokenized_dataset.rename_column("has_defect", "labels")

# 훈련/검증 분할
train_test_split = tokenized_dataset.train_test_split(test_size=0.2, seed=42)
train_dataset = train_test_split["train"]
eval_dataset = train_test_split["test"]

# 데이터 콜레이터
data_collator = DataCollatorWithPadding(tokenizer=tokenizer)

# 훈련 설정
training_args = TrainingArguments(
    output_dir="./boxing-classifier",
    learning_rate=2e-5,
    per_device_train_batch_size=1,  # 배치 크기를 줄여 VRAM/RAM 사용량 감소
    per_device_eval_batch_size=1,
    gradient_accumulation_steps=8,  # 효과적인 배치 크기 유지
    gradient_checkpointing=True,
    num_train_epochs=5,
    weight_decay=0.01,
    eval_strategy="epoch",
    save_strategy="epoch",
    load_best_model_at_end=True,
    metric_for_best_model="eval_accuracy",
    greater_is_better=True,
    logging_dir="./logs",
    logging_steps=10,
    seed=42,
)

# 평가 메트릭
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, classification_report, confusion_matrix
import numpy as np

def compute_metrics(eval_pred):
    predictions, labels = eval_pred
    predictions = predictions.argmax(axis=-1)
    
    accuracy = accuracy_score(labels, predictions)
    precision, recall, f1, _ = precision_recall_fscore_support(labels, predictions, average='weighted')
    
    return {
        'accuracy': accuracy,
        'f1': f1,
        'precision': precision,
        'recall': recall
    }

# 트레이너 초기화
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset,
    tokenizer=tokenizer,
    data_collator=data_collator,
    compute_metrics=compute_metrics,
)

# 훈련 실행
trainer.train()

# 모델 저장
trainer.save_model("./boxing-classifier-final")

# 테스트 데이터셋 저장 (나중에 정확한 평가를 위해)
eval_dataset.save_to_disk("./test_dataset")

# 테스트 셋 검증 함수
def evaluate_on_test_set(trainer, test_dataset):
    """훈련된 모델을 테스트 셋으로 최종 검증"""
    print("\n" + "="*50)
    print("테스트 셋 최종 검증 결과")
    print("="*50)
    
    # 테스트 셋 예측
    predictions = trainer.predict(test_dataset)
    y_pred = predictions.predictions.argmax(axis=-1)
    y_true = predictions.label_ids
    
    # 정확도 계산
    accuracy = accuracy_score(y_true, y_pred)
    precision, recall, f1, _ = precision_recall_fscore_support(y_true, y_pred, average='weighted')
    
    print(f"정확도 (Accuracy): {accuracy:.4f}")
    print(f"정밀도 (Precision): {precision:.4f}")
    print(f"재현율 (Recall): {recall:.4f}")
    print(f"F1 점수: {f1:.4f}")
    
    # 분류 리포트
    print("\n분류 리포트:")
    target_names = ['정상', '결함']
    print(classification_report(y_true, y_pred, target_names=target_names))
    
    # 혼동 행렬
    print("\n혼동 행렬:")
    cm = confusion_matrix(y_true, y_pred)
    print(f"                예측")
    print(f"실제      정상  결함")
    print(f"정상      {cm[0][0]:4d}  {cm[0][1]:4d}")
    print(f"결함      {cm[1][0]:4d}  {cm[1][1]:4d}")
    
    return {
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1': f1,
        'confusion_matrix': cm
    }

# 저장된 모델로 테스트하는 함수
def test_saved_model(model_path, test_dataset, tokenizer):
    """저장된 모델을 불러와서 테스트"""
    from transformers import AutoModelForSequenceClassification
    
    print(f"\n저장된 모델 불러오기: {model_path}")
    model = AutoModelForSequenceClassification.from_pretrained(model_path)
    
    # 새로운 트레이너 생성
    test_trainer = Trainer(
        model=model,
        tokenizer=tokenizer,
        data_collator=data_collator,
        compute_metrics=compute_metrics,
    )
    
    return evaluate_on_test_set(test_trainer, test_dataset)

# 현재 훈련된 모델로 테스트 셋 검증
test_results = evaluate_on_test_set(trainer, eval_dataset)

print(f"\n모델이 './boxing-classifier-final'에 저장되었습니다.")
print(f"테스트 데이터셋이 './test_dataset'에 저장되었습니다.")
print("\n나중에 저장된 모델을 정확한 테스트 셋으로 평가하려면:")
print("python test_model.py")
print("\n또는 코드에서 직접:")
print("test_saved_model('./boxing-classifier-final', eval_dataset, tokenizer)")
