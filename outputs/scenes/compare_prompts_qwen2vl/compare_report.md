# Scene-level comparison

- **A**: `Qwen2-VL-2B-Instruct / scene_open@c03d290e`
- **B**: `Qwen2-VL-2B-Instruct / scene_guided@97a6fd64`
- 10 shared scenes

Δ = B − A. The 95% CI comes from a bootstrap over scenes. Wins/losses count scenes where B is better/worse on that scene's own rate. The p-value is an exact paired sign-flip test on the per-scene differences (items within a scene are not independent, so nothing is tested at item level). With 10 scenes, a difference whose CI crosses 0 is reported as inconclusive.

| Metric | A | B | Δ | 95% CI of Δ | B wins / losses | Sign-flip p | Verdict |
|---|---|---|---|---|---|---|---|
| CHAIR_i | 4.3% | 4.0% | -0.3% | [-10.5%, 10.7%] | 1 / 1 | 1.000 | inconclusive |
| Object coverage | 51.2% | 55.8% | 4.7% | [-3.4%, 12.8%] | 4 / 1 | 0.312 | inconclusive |
| Claims supported | 21.0% | 38.0% | 17.0% | [6.8%, 27.2%] | 8 / 1 | 0.020 | B better |
| Claims contradicted | 26.0% | 18.5% | -7.5% | [-23.3%, 4.6%] | 5 / 4 | 0.219 | inconclusive |
| Human-sentence coverage | 35.6% | 44.1% | 8.5% | [-1.7%, 16.9%] | 6 / 2 | 0.156 | inconclusive |
