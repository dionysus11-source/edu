from transformers import (
    AutoTokenizer, 
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer,
    TrainerCallback,
    DataCollatorWithPadding
)
from datasets import load_from_disk
import csv
from pathlib import Path

TRAIN_DATA_DIR = Path('train_dataset')
EVAL_DATA_DIR = Path('test_dataset')
MODEL_NAME = "microsoft/codebert-base"
OUTPUT_DIR = Path("boxing-classifier")
FINAL_DIR = Path("boxing-classifier-final")
NUM_EPOCHS = 5


def load_split_dataset(directory: Path):
    if not directory.exists():
        raise FileNotFoundError(f"Dataset directory not found: {directory}")
    dataset = load_from_disk(str(directory))
    if "text" not in dataset.column_names or "has_defect" not in dataset.column_names:
        raise ValueError(f"Dataset at {directory} is missing required columns")
    return dataset


raw_train_dataset = load_split_dataset(TRAIN_DATA_DIR)
raw_eval_dataset = load_split_dataset(EVAL_DATA_DIR)


tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSequenceClassification.from_pretrained(
    MODEL_NAME,
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
tokenized_train_dataset = raw_train_dataset.map(tokenize_function, batched=True)
tokenized_eval_dataset = raw_eval_dataset.map(tokenize_function, batched=True)

tokenized_train_dataset = tokenized_train_dataset.rename_column("has_defect", "labels")
tokenized_eval_dataset = tokenized_eval_dataset.rename_column("has_defect", "labels")

train_dataset = tokenized_train_dataset
eval_dataset = tokenized_eval_dataset

# 데이터 콜레이터
data_collator = DataCollatorWithPadding(tokenizer=tokenizer)

# 훈련 설정
training_args = TrainingArguments(
    output_dir=str(OUTPUT_DIR),
    learning_rate=2e-5,
    per_device_train_batch_size=1,  # 배치 크기를 줄여 VRAM/RAM 사용량 감소
    per_device_eval_batch_size=1,
    gradient_accumulation_steps=8,  # 효과적인 배치 크기 유지
    gradient_checkpointing=True,
    num_train_epochs=NUM_EPOCHS,
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

LABEL_NAMES = {0: 'normal', 1: 'defect'}


def compute_metrics(eval_pred):
    predictions, labels = eval_pred
    predictions = predictions.argmax(axis=-1)

    report = classification_report(labels, predictions, output_dict=True, zero_division=0)
    weighted = report.get('weighted avg', {})

    metrics = {
        'accuracy': report.get('accuracy', 0.0),
        'precision': weighted.get('precision', 0.0),
        'recall': weighted.get('recall', 0.0),
        'f1': weighted.get('f1-score', 0.0),
    }

    for label_id, label_name in LABEL_NAMES.items():
        label_key = str(label_id)
        label_stats = report.get(label_key, {})
        metrics[f"{label_name}_precision"] = label_stats.get('precision', 0.0)
        metrics[f"{label_name}_recall"] = label_stats.get('recall', 0.0)
        metrics[f"{label_name}_f1"] = label_stats.get('f1-score', 0.0)
        metrics[f"{label_name}_support"] = label_stats.get('support', 0)

    return metrics

class MetricsCSVLogger(TrainerCallback):
    def __init__(self, output_path: str = 'logs/metrics_history.csv', metric_prefix: str = 'eval_'):
        self.output_path = Path(output_path)
        self.metric_prefix = metric_prefix
        self.fieldnames = None

    def on_evaluate(self, args, state, control, metrics=None, **kwargs):
        if metrics is None:
            return

        eval_metrics = {k: v for k, v in metrics.items() if k.startswith(self.metric_prefix)}
        if not eval_metrics:
            return

        epoch = state.epoch if state.epoch is not None else state.global_step
        eval_metrics['epoch'] = epoch

        if self.fieldnames is None:
            self.fieldnames = ['epoch'] + [k for k in sorted(eval_metrics.keys()) if k != 'epoch']
        else:
            for key in eval_metrics.keys():
                if key not in self.fieldnames:
                    self.fieldnames.append(key)

        row = {key: eval_metrics.get(key) for key in self.fieldnames}

        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        write_header = not self.output_path.exists()
        with self.output_path.open('a', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=self.fieldnames)
            if write_header:
                writer.writeheader()
            writer.writerow(row)


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

metrics_logger = MetricsCSVLogger()
trainer.add_callback(metrics_logger)

# 훈련 실행
trainer.train()

# 모델 저장
trainer.save_model(str(args.final_dir))

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

print(f"\n모델이 '{FINAL_DIR.as_posix()}'에 저장되었습니다.")
print(f"검증 데이터 분할은 '{TRAIN_DATA_DIR.as_posix()}'과 '{EVAL_DATA_DIR.as_posix()}'에서 관리됩니다.")
print("필요 시 'split_dataset.py'를 다시 실행해 분할을 갱신하세요.")
print("\n나중에 저장된 모델을 동일한 검증 셋으로 평가하려면:")
print("python test_model.py")
print("\n또는 코드에서 직접:")
print(f"test_saved_model('{FINAL_DIR.as_posix()}', eval_dataset, tokenizer)")
