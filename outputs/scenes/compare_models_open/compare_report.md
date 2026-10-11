# Scene-level comparison

- **A**: `SmolVLM-500M-Instruct / scene_open@62f61a19`
- **B**: `Qwen2-VL-2B-Instruct / scene_open@62f61a19`
- 10 shared scenes

Δ = B − A. The 95% CI comes from a bootstrap over scenes. Wins/losses count scenes where B is better/worse on that scene's own rate (a metric undefined for a scene, e.g. CHAIR_i with no object mentions, is skipped). The p-value is an exact paired sign-flip test on the per-scene differences (items within a scene are not independent, so nothing is tested at item level); when only one scene or none differs, p = 1 by construction. With 10 scenes, a difference whose CI crosses 0 is reported as inconclusive.

| Metric | A | B | Δ | 95% CI of Δ | B wins / losses | Sign-flip p | Verdict |
|---|---|---|---|---|---|---|---|
| CHAIR_i | 0.0% | 4.3% | 4.3% | [0.0%, 12.5%] | 0 / 1 | 1.000 | inconclusive |
| Object coverage | 23.8% | 51.2% | 27.4% | [9.6%, 42.9%] | 7 / 1 | 0.039 | B better |
| Claims supported | 26.7% | 21.0% | -5.7% | [-28.6%, 12.1%] | 2 / 5 | 0.141 | inconclusive |
| Claims contradicted | 20.0% | 26.0% | 6.0% | [-11.0%, 20.4%] | 1 / 5 | 0.312 | inconclusive |
| Human-sentence coverage | 11.9% | 35.6% | 23.7% | [6.8%, 39.6%] | 7 / 2 | 0.027 | B better |
