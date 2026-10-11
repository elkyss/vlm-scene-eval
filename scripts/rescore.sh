#!/usr/bin/env bash
# Re-score the committed scene runs and rebuild every scene-level result in the README
# (reports, judge validation, comparisons, leaderboard). No model, no GPU, no data download:
# it reads the descriptions and fact sheets saved in outputs/scenes/<run>/.
set -euo pipefail

S=outputs/scenes
RUNS="mock_oracle mock_always_car smolvlm_open smolvlm_guided qwen2vl_open qwen2vl_guided"
# Judge validation first: every report cites its error rates per claim type.
vlm-eval validate-judge $S/mock_oracle --out $S/judge_validation
for r in $RUNS; do
  echo "=== evaluate scenes/$r"
  vlm-eval evaluate-scenes "$S/$r"
done
vlm-eval compare-scenes $S/smolvlm_open $S/qwen2vl_open --out $S/compare_models_open
vlm-eval compare-scenes $S/smolvlm_guided $S/qwen2vl_guided --out $S/compare_models_guided
vlm-eval compare-scenes $S/smolvlm_open $S/smolvlm_guided --out $S/compare_prompts_smolvlm
vlm-eval compare-scenes $S/qwen2vl_open $S/qwen2vl_guided --out $S/compare_prompts_qwen2vl
vlm-eval scene-leaderboard $S/mock_oracle $S/mock_always_car $S/smolvlm_open $S/smolvlm_guided \
  $S/qwen2vl_open $S/qwen2vl_guided --out $S/leaderboard.md
