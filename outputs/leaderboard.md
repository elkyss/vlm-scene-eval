# Leaderboard

| Run | Model | Prompt | Object F1 | Blind baseline F1 | Precision | Recall | Hallucination | Count exact | Day/night bal. acc. | Attr. mean bal. acc. | Valid output | Latency/frame (s) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| mock_oracle | mock-oracle | v2_structured | 100.0% | 54.7% | 100.0% | 100.0% | 0.0% | 100.0% | 100.0% | 100.0% | 100.0% | 0.00 |
| mock_always_car | mock-always_car | v2_structured | 64.1% | 54.7% | 71.7% | 57.9% | 26.0% | 53.0% | 50.0% | 45.8% | 100.0% | 0.00 |
| smolvlm_v1 | SmolVLM-500M-Instruct | v1_open | 67.8% | 54.7% | 89.9% | 54.4% | 9.6% | 53.2% | 3.3% | 14.2% | 100.0% | 1.74 |
| smolvlm_v2 | SmolVLM-500M-Instruct | v2_structured | 0.0% | 54.7% | – | 0.0% | – | – | 20.0% | 10.4% | 48.0% | 2.06 |
| smolvlm_v2b | SmolVLM-500M-Instruct | v2b_structured | 0.0% | 54.7% | – | 0.0% | – | – | 0.0% | 0.0% | 0.0% | 1.49 |
| smolvlm_v3 | SmolVLM-500M-Instruct | v3_questionnaire | 63.4% | 54.7% | 50.3% | 86.0% | 46.0% | 68.4% | 100.0% | 67.2% | 100.0% | 17.42 |
| qwen2vl_v2 | Qwen2-VL-2B-Instruct | v2_structured | 59.1% | 54.7% | 83.9% | 45.6% | 15.2% | 51.9% | 100.0% | 73.6% | 96.0% | 4.12 |
| qwen2vl_v2b | Qwen2-VL-2B-Instruct | v2b_structured | 35.1% | 54.7% | 76.5% | 22.8% | 21.1% | 80.8% | 100.0% | 70.4% | 100.0% | 4.72 |
| qwen2vl_v3 | Qwen2-VL-2B-Instruct | v3_questionnaire | 73.4% | 54.7% | 70.7% | 76.3% | 27.9% | 67.8% | 100.0% | 71.2% | 100.0% | 18.14 |
