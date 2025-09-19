# Model Comparison Summary

## Key Findings
- **CodeBERTa-small** achieves the highest F1 (0.995) while training/evaluating fastest (~32s train, 0.3s eval) and sustaining the highest throughput (~410 samples/s). Best overall trade-off.
- **CodeBERT / GraphCodeBERT** reach F1 ≈ 0.99 / 0.985 but require ~55s training and process ≈240 samples/s; heavier than CodeBERTa-small without meaningful accuracy gains.
- **DistilRoBERTa** delivers F1 ≈ 0.985 with high throughput (~390 samples/s), suitable if an even smaller general model is needed; still falls short of CodeBERTa-small.
- **RoBERTa-base** trails with F1 ≈ 0.975 and slow throughput (~237 samples/s); general-purpose pretraining alone is insufficient.

## Visual Insights
- `metrics_comparison.png`: All models exceed 0.97 F1, but CodeBERTa-small leads.
- `runtime_comparison.png`: CodeBERT/GraphCodeBERT require ~55s training vs. ~32s for lighter models.
- `size_vs_f1.png`: CodeBERTa-small offers best F1 per parameter; general models underperform.
- `throughput_vs_f1.png`: CodeBERTa-small balances highest throughput with best F1; DistilRoBERTa trades slight accuracy for speed.

## Recommendation
- Adopt **CodeBERTa-small** as default classifier; it dominates on both accuracy and efficiency.
- Keep **DistilRoBERTa** as a fallback when extreme resource constraints exist.
- Avoid heavier CodeBERT/GraphCodeBERT and RoBERTa-base unless a specific use case demands them.
