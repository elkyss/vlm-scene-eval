#!/usr/bin/env bash
# Full pipeline: every run (including VLM inference), comparison and leaderboard in the README.
# Model answers are cached under .cache/, so a second run only re-scores; a fresh clone has no
# cache and re-runs all inference. To re-score the committed runs without a model, use
# scripts/rescore.sh (make rescore).
set -euo pipefail

# --- Scene level (main result): inference, then scoring and analysis ------------------------
# describe-scenes runs the VLM (answers are cached under .cache/; a fresh clone re-runs
# inference). scripts/rescore.sh then scores the runs and builds every scene-level result.
SCENE_CONFIGS=${SCENE_CONFIGS:-"mock_oracle mock_always_car smolvlm_open smolvlm_guided qwen2vl_open qwen2vl_guided"}
for c in $SCENE_CONFIGS; do
  echo "=== describe scenes/$c"
  vlm-eval describe-scenes -c "configs/scenes/$c.yaml"
done
./scripts/rescore.sh

# --- Frame level (diagnostic): single frames, 5 per scene ------------------------------------
FRAME_CONFIGS=${FRAME_CONFIGS:-"mock_oracle mock_always_car smolvlm_v1 smolvlm_v2 smolvlm_v2b smolvlm_v3 qwen2vl_v2 qwen2vl_v2b qwen2vl_v3"}
for c in $FRAME_CONFIGS; do
  echo "=== frames/$c"
  vlm-eval run -c "configs/frames/$c.yaml"
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
