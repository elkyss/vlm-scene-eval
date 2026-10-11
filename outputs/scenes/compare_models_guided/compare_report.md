# Scene-level comparison

- **A**: `SmolVLM-500M-Instruct / scene_guided@53a32872`
- **B**: `Qwen2-VL-2B-Instruct / scene_guided@53a32872`
- 10 shared scenes

Δ = B − A. The 95% CI comes from a bootstrap over scenes. Wins/losses count scenes where B is better/worse on that scene's own rate (a metric undefined for a scene, e.g. CHAIR_i with no object mentions, is skipped). The p-value is an exact paired sign-flip test on the per-scene differences (items within a scene are not independent, so nothing is tested at item level); when only one scene or none differs, p = 1 by construction. With 10 scenes, a difference whose CI crosses 0 is reported as inconclusive.

| Metric | A | B | Δ | 95% CI of Δ | B wins / losses | Sign-flip p | Verdict |
|---|---|---|---|---|---|---|---|
| CHAIR_i | 7.1% | 4.0% | -3.1% | [-8.8%, 0.0%] | 1 / 0 | 1.000 | inconclusive |
| Object coverage | 29.5% | 55.8% | 26.3% | [15.4%, 36.4%] | 9 / 0 | 0.004 | B better |
| Claims supported | 32.1% | 38.0% | 5.8% | [-10.3%, 20.6%] | 5 / 3 | 0.383 | inconclusive |
| Claims contradicted | 23.2% | 18.5% | -4.7% | [-22.4%, 11.6%] | 3 / 7 | 0.637 | inconclusive |
| Human-sentence coverage | 22.0% | 44.1% | 22.0% | [15.3%, 30.0%] | 9 / 0 | 0.004 | B better |
