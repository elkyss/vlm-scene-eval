#!/usr/bin/env bash
# Reproduce every run and comparison reported in the README.
set -euo pipefail
CONFIGS=${CONFIGS:-"mock_oracle mock_always_car smolvlm_v1 smolvlm_v2 smolvlm_v2b smolvlm_v3 qwen2vl_v2 qwen2vl_v2b qwen2vl_v3"}
for c in $CONFIGS; do
  echo "=== $c"
  vlm-eval run -c "configs/$c.yaml"
done
vlm-eval compare outputs/mock_always_car outputs/smolvlm_v1 --out outputs/compare_mock_always_car_vs_smolvlm_v1
vlm-eval compare outputs/smolvlm_v1 outputs/smolvlm_v3 --out outputs/compare_smolvlm_v1_vs_v3
vlm-eval compare outputs/smolvlm_v2 outputs/smolvlm_v3 --out outputs/compare_smolvlm_v2_vs_v3
vlm-eval compare outputs/qwen2vl_v2 outputs/qwen2vl_v2b --out outputs/compare_qwen2vl_v2_vs_v2b
vlm-eval compare outputs/smolvlm_v3 outputs/qwen2vl_v3 --out outputs/compare_smolvlm_vs_qwen2vl_v3
vlm-eval compare outputs/qwen2vl_v2 outputs/qwen2vl_v3 --out outputs/compare_qwen2vl_v2_vs_v3
vlm-eval leaderboard outputs/mock_oracle outputs/mock_always_car outputs/smolvlm_v1 outputs/smolvlm_v2 outputs/smolvlm_v2b outputs/smolvlm_v3 outputs/qwen2vl_v2 outputs/qwen2vl_v2b outputs/qwen2vl_v3
