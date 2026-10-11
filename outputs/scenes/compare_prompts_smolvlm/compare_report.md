# Scene-level comparison

- **A**: `SmolVLM-500M-Instruct / scene_open@62f61a19`
- **B**: `SmolVLM-500M-Instruct / scene_guided@53a32872`
- 10 shared scenes

Δ = B − A. The 95% CI comes from a bootstrap over scenes. Wins/losses count scenes where B is better/worse on that scene's own rate (a metric undefined for a scene, e.g. CHAIR_i with no object mentions, is skipped). The p-value is an exact paired sign-flip test on the per-scene differences (items within a scene are not independent, so nothing is tested at item level); when only one scene or none differs, p = 1 by construction. With 10 scenes, a difference whose CI crosses 0 is reported as inconclusive.

| Metric | A | B | Δ | 95% CI of Δ | B wins / losses | Sign-flip p | Verdict |
|---|---|---|---|---|---|---|---|
| CHAIR_i | 0.0% | 7.1% | 7.1% | [0.0%, 21.4%] | 0 / 1 | 1.000 | inconclusive |
| Object coverage | 23.8% | 29.5% | 5.7% | [-1.5%, 12.5%] | 3 / 2 | 0.375 | inconclusive |
| Claims supported | 26.7% | 32.1% | 5.5% | [-24.2%, 31.7%] | 5 / 4 | 0.703 | inconclusive |
| Claims contradicted | 20.0% | 23.2% | 3.2% | [-32.3%, 27.5%] | 2 / 5 | 0.906 | inconclusive |
| Human-sentence coverage | 11.9% | 22.0% | 10.2% | [-2.9%, 23.4%] | 4 / 2 | 0.188 | inconclusive |
