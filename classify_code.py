"""Interactive snippet classifier using the fine-tuned CodeBERT model."""
import argparse
from pathlib import Path
from typing import Tuple

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

LABELS = {0: "정상", 1: "결함"}


def load_model(model_dir: Path) -> Tuple[AutoTokenizer, AutoModelForSequenceClassification]:
    """Load tokenizer and model from the specified directory."""
    tokenizer = AutoTokenizer.from_pretrained(model_dir)
    model = AutoModelForSequenceClassification.from_pretrained(model_dir)
    model.eval()
    return tokenizer, model


def classify_snippet(text: str, tokenizer, model, max_length: int) -> Tuple[str, float, list]:
    """Run inference on the provided text and return label, confidence, and probabilities."""
    with torch.no_grad():
        inputs = tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=max_length,
        )
        outputs = model(**inputs)
        probs = outputs.logits.softmax(dim=-1)[0]
        confidence, prediction = torch.max(probs, dim=0)
    label = LABELS.get(prediction.item(), str(prediction.item()))
    return label, confidence.item(), probs.tolist()


def read_multiline_input(prompt: str = "코드를 입력하세요 (빈 줄 입력 시 종료):\n") -> str:
    """Collect multiline input until an empty line is entered."""
    print(prompt, end="")
    lines = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if not line:
            break
        lines.append(line)
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Classify code snippets with the fine-tuned CodeBERT model.")
    parser.add_argument(
        "text",
        nargs="?",
        help="Optional single-line snippet to classify. Leave empty to enter interactive mode.",
    )
    parser.add_argument(
        "--model-dir",
        default="./boxing-classifier-final",
        help="Path to the fine-tuned model directory (default: ./boxing-classifier-final).",
    )
    parser.add_argument(
        "--max-length",
        type=int,
        default=512,
        help="Maximum sequence length used during tokenization.",
    )

    args = parser.parse_args()
    model_path = Path(args.model_dir)
    if not model_path.exists():
        raise FileNotFoundError(f"모델 경로를 찾을 수 없습니다: {model_path}")

    tokenizer, model = load_model(model_path)

    if args.text:
        snippets = [args.text]
    else:
        snippets = []
        while True:
            snippet = read_multiline_input()
            if not snippet:
                print("입력을 감지하지 못했습니다. 종료합니다.")
                break
            snippets.append(snippet)
            label, confidence, probs = classify_snippet(snippet, tokenizer, model, args.max_length)
            print(f"예측: {label} (신뢰도: {confidence:.4f})")
            print(f"정상/결함 확률: {probs}")
            print("\n계속하려면 코드를 입력하고, 종료하려면 빈 줄을 입력하세요.\n")
        return

    for snippet in snippets:
        label, confidence, probs = classify_snippet(snippet, tokenizer, model, args.max_length)
        print(f"예측: {label} (신뢰도: {confidence:.4f})")
        print(f"정상/결함 확률: {probs}")


if __name__ == "__main__":
    main()
