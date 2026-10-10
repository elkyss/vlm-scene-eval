#!/usr/bin/env bash
# Reproduce every run, comparison and leaderboard reported in the README.
# Model answers are cached under .cache/, so a re-run only re-scores (no inference).
set -euo pipefail

# --- Scene level (main result): one description per scene -----------------------------------
SCENE_CONFIGS=${SCENE_CONFIGS:-"mock_oracle mock_always_car smolvlm_open smolvlm_guided qwen2vl_open qwen2vl_guided"}
for c in $SCENE_CONFIGS; do
  echo "=== scenes/$c"
  vlm-eval run-scenes -c "configs/scenes/$c.yaml"
done
S=outputs/scenes
vlm-eval validate-judge $S/mock_oracle --out $S/judge_validation
vlm-eval compare-scenes $S/smolvlm_open $S/qwen2vl_open --out $S/compare_models_open
vlm-eval compare-scenes $S/smolvlm_guided $S/qwen2vl_guided --out $S/compare_models_guided
vlm-eval compare-scenes $S/smolvlm_open $S/smolvlm_guided --out $S/compare_prompts_smolvlm
vlm-eval compare-scenes $S/qwen2vl_open $S/qwen2vl_guided --out $S/compare_prompts_qwen2vl
vlm-eval scene-leaderboard $S/mock_oracle $S/mock_always_car $S/smolvlm_open $S/smolvlm_guided \
  $S/qwen2vl_open $S/qwen2vl_guided --out $S/leaderboard.md

# --- Frame level (diagnostic): single frames, 5 per scene ------------------------------------
FRAME_CONFIGS=${FRAME_CONFIGS:-"mock_oracle mock_always_car smolvlm_v1 smolvlm_v2 smolvlm_v2b smolvlm_v3 qwen2vl_v2 qwen2vl_v2b qwen2vl_v3"}
for c in $FRAME_CONFIGS; do
  echo "=== frames/$c"
  vlm-eval run -c "configs/$c.yaml"
done
vlm-eval compare outputs/mock_always_car outputs/smolvlm_v1 --out outputs/compare_mock_always_car_vs_smolvlm_v1
vlm-eval compare outputs/smolvlm_v1 outputs/smolvlm_v3 --out outputs/compare_smolvlm_v1_vs_v3
vlm-eval compare outputs/smolvlm_v2 outputs/smolvlm_v3 --out outputs/compare_smolvlm_v2_vs_v3
vlm-eval compare outputs/qwen2vl_v2 outputs/qwen2vl_v2b --out outputs/compare_qwen2vl_v2_vs_v2b
vlm-eval compare outputs/qwen2vl_v2 outputs/qwen2vl_v3 --out outputs/compare_qwen2vl_v2_vs_v3
vlm-eval compare outputs/smolvlm_v3 outputs/qwen2vl_v3 --out outputs/compare_smolvlm_vs_qwen2vl_v3
vlm-eval leaderboard outputs/mock_oracle outputs/mock_always_car outputs/smolvlm_v1 outputs/smolvlm_v2 \
  outputs/smolvlm_v2b outputs/smolvlm_v3 outputs/qwen2vl_v2 outputs/qwen2vl_v2b outputs/qwen2vl_v3

# --- Results store: every run in one DuckDB file (derived; safe to rebuild) -------------------
vlm-eval ingest outputs/scenes/{mock_oracle,mock_always_car,smolvlm_open,smolvlm_guided,qwen2vl_open,qwen2vl_guided} \
  outputs/{mock_oracle,mock_always_car,smolvlm_v1,smolvlm_v2,smolvlm_v2b,smolvlm_v3,qwen2vl_v2,qwen2vl_v2b,qwen2vl_v3}
