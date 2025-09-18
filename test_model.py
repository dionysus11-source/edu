from transformers import (
    AutoTokenizer, 
    AutoModelForSequenceClassification,
    Trainer,
    DataCollatorWithPadding
)
from datasets import Dataset, load_from_disk
import pandas as pd
import json
import os
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, classification_report, confusion_matrix
import numpy as np

def load_boxing_dataset(file_path):
    """박싱 데이터셋 로드"""
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            data.append(json.loads(line))
    return Dataset.from_pandas(pd.DataFrame(data))

def tokenize_function(examples, tokenizer):
    """토크나이징 함수"""
    return tokenizer(
        examples["text"],
        truncation=True,
        padding=False,
        max_length=512
    )

def compute_metrics(eval_pred):
    """평가 메트릭 계산"""
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

def evaluate_model(model_path, test_dataset_path=None):
    """저장된 모델을 테스트 데이터로 검증"""
    
    print("="*60)
    print("저장된 모델 테스트 시작")
    print("="*60)
    
    # 모델과 토크나이저 로드
    print(f"모델 로드 중: {model_path}")
    model = AutoModelForSequenceClassification.from_pretrained(model_path)
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    
    # 테스트 데이터셋 로드
    if test_dataset_path and os.path.exists(test_dataset_path):
        print(f"훈련 시 분할된 테스트 데이터셋 로드 중: {test_dataset_path}")
        test_dataset = load_from_disk(test_dataset_path)
        print(f"✅ 원본 테스트 데이터셋 사용 (훈련 시 분할된 정확한 테스트 셋)")
    else:
        print("⚠️  저장된 테스트 데이터셋이 없어서 새로 분할합니다.")
        print("   정확한 평가를 위해서는 train_code.py를 먼저 실행해주세요.")
        
        # 전체 데이터를 다시 로드해서 분할 (fallback)
        dataset = load_boxing_dataset("enhanced_boxing_dataset.jsonl")
        tokenized_dataset = dataset.map(
            lambda x: tokenize_function(x, tokenizer), 
            batched=True
        )
        tokenized_dataset = tokenized_dataset.rename_column("has_defect", "labels")
        train_test_split = tokenized_dataset.train_test_split(test_size=0.2, seed=42)
        test_dataset = train_test_split["test"]
    
    # 데이터 콜레이터
    data_collator = DataCollatorWithPadding(tokenizer=tokenizer)
    
    # 트레이너 설정
    trainer = Trainer(
        model=model,
        tokenizer=tokenizer,
        data_collator=data_collator,
        compute_metrics=compute_metrics,
    )
    
    # 예측 수행
    print("예측 수행 중...")
    predictions = trainer.predict(test_dataset)
    y_pred = predictions.predictions.argmax(axis=-1)
    y_true = predictions.label_ids
    
    # 결과 출력
    print("\n" + "="*50)
    print("테스트 결과")
    print("="*50)
    
    # 기본 메트릭
    accuracy = accuracy_score(y_true, y_pred)
    precision, recall, f1, _ = precision_recall_fscore_support(y_true, y_pred, average='weighted')
    
    print(f"테스트 샘플 수: {len(y_true)}")
    print(f"정확도 (Accuracy): {accuracy:.4f} ({accuracy*100:.2f}%)")
    print(f"정밀도 (Precision): {precision:.4f}")
    print(f"재현율 (Recall): {recall:.4f}")
    print(f"F1 점수: {f1:.4f}")
    
    # 분류 리포트
    print("\n분류 리포트:")
    target_names = ['정상', '결함']
    print(classification_report(y_true, y_pred, target_names=target_names))
    
    # 혼동 행렬
    print("혼동 행렬:")
    cm = confusion_matrix(y_true, y_pred)
    print(f"                예측")
    print(f"실제      정상  결함")
    print(f"정상      {cm[0][0]:4d}  {cm[0][1]:4d}")
    print(f"결함      {cm[1][0]:4d}  {cm[1][1]:4d}")
    
    # 클래스별 정확도
    print(f"\n클래스별 성능:")
    print(f"정상 클래스 정확도: {cm[0][0]/(cm[0][0]+cm[0][1]):.4f}")
    print(f"결함 클래스 정확도: {cm[1][1]/(cm[1][0]+cm[1][1]):.4f}")
    
    return {
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1': f1,
        'confusion_matrix': cm,
        'predictions': y_pred,
        'true_labels': y_true
    }

def test_single_text(model_path, text):
    """단일 텍스트에 대한 예측"""
    model = AutoModelForSequenceClassification.from_pretrained(model_path)
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
    outputs = model(**inputs)
    prediction = outputs.logits.argmax(dim=-1).item()
    confidence = outputs.logits.softmax(dim=-1).max().item()
    
    result = "결함" if prediction == 1 else "정상"
    print(f"텍스트: {text}")
    print(f"예측: {result} (신뢰도: {confidence:.4f})")
    
    return prediction, confidence

if __name__ == "__main__":
    # 기본 설정
    MODEL_PATH = "./boxing-classifier-final"
    TEST_DATASET_PATH = "./test_dataset"  # 훈련 시 저장된 테스트 데이터셋
    
    try:
        # 전체 테스트 수행 (훈련 시 분할된 정확한 테스트 셋 사용)
        results = evaluate_model(MODEL_PATH, TEST_DATASET_PATH)
        
        print("\n" + "="*60)
        print("테스트 완료!")
        print("="*60)
        
        # 샘플 텍스트 테스트
        print("\n샘플 텍스트 테스트:")
        sample_texts = [
            "이 코드는 잘 작동합니다.",
            "버그가 있는 것 같습니다.",
            "null pointer exception이 발생했습니다."
        ]
        
        for text in sample_texts:
            test_single_text(MODEL_PATH, text)
            print()
            
    except Exception as e:
        print(f"에러 발생: {e}")
        print("먼저 train_code.py를 실행하여 모델을 훈련시켜주세요.")
