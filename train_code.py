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
        max_length=512
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
    per_device_train_batch_size=8,
    per_device_eval_batch_size=8,
    num_train_epochs=5,
    weight_decay=0.01,
    evaluation_strategy="epoch",
    save_strategy="epoch",
    load_best_model_at_end=True,
    metric_for_best_model="eval_accuracy",
    greater_is_better=True,
    logging_dir="./logs",
    logging_steps=10,
    seed=42,
)

# 평가 메트릭
from sklearn.metrics import accuracy_score, precision_recall_fscore_support

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
