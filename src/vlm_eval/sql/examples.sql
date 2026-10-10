-- Example questions over outputs/results.duckdb (build it with: vlm-eval ingest ...).
-- Run one with: vlm-eval query --example leaderboard

-- name: leaderboard
SELECT r.run_id, r.model, split_part(r.prompt_version, '@', 1) AS prompt,
       round(100 * max(CASE WHEN m.key = 'object_coverage' THEN m.value END), 1) AS objects_pct,
       round(100 * max(CASE WHEN m.key = 'claims_supported' THEN m.value END), 1) AS supported_pct,
       round(100 * max(CASE WHEN m.key = 'specific_claims_supported' THEN m.value END), 1) AS specific_pts
FROM runs r JOIN run_metrics m USING (run_id)
WHERE r.level = 'scene'
GROUP BY ALL ORDER BY objects_pct DESC;

-- name: missed_by_every_model
-- Object types that are clearly visible but that no real model mentions in its final description.
WITH real AS (SELECT run_id FROM runs WHERE level = 'scene' AND model NOT LIKE 'mock-%')
SELECT scene_name, missed_type, count(*) AS runs_missing
FROM (SELECT run_id, scene_name, unnest(missed) AS missed_type
      FROM scene_metrics WHERE is_final AND run_id IN (SELECT run_id FROM real))
GROUP BY ALL
HAVING count(*) = (SELECT count(*) FROM real)
ORDER BY scene_name;

-- name: invented_objects
-- Which object types each model invents (no box of that type in the frames shown).
SELECT r.model, h AS invented_type, count(*) AS views
FROM (SELECT run_id, unnest(hallucinated) AS h FROM scene_metrics) s
JOIN runs r USING (run_id)
GROUP BY ALL ORDER BY views DESC;

-- name: contradicted_claims
-- Contradicted claims of the final descriptions (indicative: see the judge validation).
SELECT run_id, scene_name, claim
FROM claims WHERE is_final AND label = 'contradicted' AND run_id NOT LIKE 'scene:mock_%'
ORDER BY run_id, scene_name;
