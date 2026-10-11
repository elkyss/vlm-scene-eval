# Scene-level leaderboard

| Run | Model | Prompt | CHAIR_i | CHAIR_s | Obj. coverage | Supported | Specific support (own − other scenes) [95% CI] | Unverifiable | Human coverage | Repetition loops | View agreement | s / call |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| mock_oracle | mock-oracle | scene_open | 0.0% | 0.0% | 100.0% | 100.0% | 44.9% [41.9%, 47.8%] | 0.0% | 62.7% | 0.0% | 89.8% | 0.00 |
| mock_always_car | mock-fixed | scene_open | 10.0% | 20.0% | 41.9% | 20.0% | 0.0% [-16.7%, 16.7%] | 45.0% | 16.9% | 0.0% | 100.0% | 0.00 |
| smolvlm_open | SmolVLM-500M-Instruct | scene_open | 0.0% | 0.0% | 23.8% | 26.7% | -4.4% [-10.1%, 0.8%] | 53.3% | 11.9% | 60.0% | 70.0% | 13.30 |
| smolvlm_guided | SmolVLM-500M-Instruct | scene_guided | 7.1% | 10.0% | 29.5% | 32.1% | 6.2% [0.2%, 13.2%] | 44.6% | 22.0% | 10.0% | 43.2% | 10.99 |
| qwen2vl_open | Qwen2-VL-2B-Instruct | scene_open | 4.3% | 10.0% | 51.2% | 21.0% | 11.1% [3.9%, 18.8%] | 53.0% | 35.6% | 20.0% | 51.0% | 10.19 |
| qwen2vl_guided | Qwen2-VL-2B-Instruct | scene_guided | 4.0% | 10.0% | 55.8% | 38.0% | 9.6% [4.3%, 15.8%] | 43.5% | 44.1% | 0.0% | 52.1% | 10.37 |
