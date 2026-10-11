"""Tests for the scene-level pipeline: sampling, fact sheet, views, claims, judge, metrics."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from PIL import Image

from tests.conftest import DATAROOT, TAX
from vlm_eval.domain import (
    EgoMotion,
    FactSentence,
    SceneDescription,
    SceneFactSheet,
    SceneSample,
    SceneView,
    ViewOutput,
)
from vlm_eval.evaluation.scene_compare import compare_scene_runs
from vlm_eval.evaluation.scene_metrics import (
    DescriptionScore,
    SceneRow,
    aggregate,
    evaluate_scenes,
    score_description,
    specificity,
    within_scene_spread,
)
from vlm_eval.evaluation.scene_report import SCENE_METRICS, render_scene_report
from vlm_eval.gt.scene_facts import SceneFactBuilder, ego_motion_from_poses, render_sentences
from vlm_eval.judge import CONTRADICTED, NEUTRAL, SUPPORTED, FakeJudge, judge_against
from vlm_eval.loaders.scene_loader import NuScenesSceneLoader, view_frame_indices
from vlm_eval.parsing.claims import split_claims, split_reference
from vlm_eval.scene_pipeline import ScenePipeline, ScenePrompt, combine_views, load_scene_prompt
from vlm_eval.vlm import MockBackend

# --- sampling -------------------------------------------------------------------------------


@pytest.mark.parametrize("n_frames", [39, 40, 41])
def test_views_are_distinct_spread_and_ordered(n_frames: int) -> None:
    views = view_frame_indices(n_frames, n_segments=6, n_views=3)
    assert len(views) == 3 and all(len(v) == 6 for v in views)
    flat = [i for v in views for i in v]
    assert len(set(flat)) == len(flat)  # no frame shared between views
    assert all(v == sorted(v) for v in views)
    assert all(0 <= i < n_frames for i in flat)
    seg = n_frames / 6
    for v in views:  # one frame per segment
        assert [int(i // seg) for i in v] == list(range(6))


def test_too_short_scene_raises() -> None:
    with pytest.raises(ValueError):
        view_frame_indices(10, n_segments=6, n_views=3)


# --- ego motion and fact sentences ----------------------------------------------------------


def test_ego_motion_states() -> None:
    t = [i * 500_000 for i in range(5)]  # 2 Hz
    stopped = ego_motion_from_poses(t, [[0, 0, 0]] * 5, [0.0] * 5)
    assert (stopped.state, stopped.stopped_fraction) == ("stopped", 1.0)
    straight = ego_motion_from_poses(t, [[5 * i, 0, 0] for i in range(5)], [0.0] * 5)
    assert straight.state == "moving" and straight.turn == "straight"
    assert straight.mean_speed_mps == pytest.approx(10.0)
    left = ego_motion_from_poses(t, [[5 * i, 0, 0] for i in range(5)], [0, 0.4, 0.8, 1.2, 1.6])
    assert left.turn == "left" and left.yaw_change_deg == pytest.approx(91.67, abs=0.1)
    right = ego_motion_from_poses(t, [[5 * i, 0, 0] for i in range(5)], [0, -0.4, -0.8, -1.2, -1.6])
    assert right.turn == "right"


def make_sheet(
    scene: str = "s1",
    view: int = 0,
    objects: dict[str, int] | None = None,
    loose: list[str] | None = None,
    night: bool = False,
    reference: str = "Night, many peds, bus",
) -> SceneFactSheet:
    objects = {"car": 3, "pedestrian": 5} if objects is None else objects
    sheet = SceneFactSheet(
        scene_name=scene,
        view_id=view,
        location="singapore-onenorth",
        reference_text=reference,
        attributes={
            "time_of_day": "night" if night else "day",
            "road_condition": "dry",
            "scene_type": "road",
            "traffic_side": "left",
        },
        objects=objects,
        loosely_present=sorted(set(objects) | set(loose or [])),
        object_states={"car": {"parked": 3}},
        ego=EgoMotion(
            mean_speed_mps=0.0,
            max_speed_mps=0.0,
            stopped_fraction=1.0,
            yaw_change_deg=0.0,
            state="stopped",
            turn="straight",
        ),
    )
    sheet.sentences = render_sentences(sheet, TAX)
    return sheet


def test_fact_sentences_are_presence_only_with_sources() -> None:
    sheet = make_sheet(loose=["truck"])
    texts = sheet.premise_sentences
    assert not any(re.search(r"\d", t) for t in texts)  # no instance counts
    assert "There are cars." in texts and "Most cars are parked." in texts
    assert "There are no buses." in texts
    assert "There are no trucks." not in texts  # a truck box exists, just not clearly visible
    assert "Our car is stopped." in texts
    assert not any("straight" in t or "turns" in t for t in texts)  # no turn when stopped
    assert {s.source for s in sheet.sentences} >= {"annotations", "ego_pose", "log", "description"}
    assert not any("dry" in t for t in texts)  # absence of "rain" is not evidence of dry


# --- combining views ------------------------------------------------------------------------


def view(view_id: int, objects: list[str], attrs: dict[str, str] | None = None) -> ViewOutput:
    return ViewOutput(
        view_id=view_id,
        frame_indices=[view_id],
        raw_output="",
        description=f"view {view_id}",
        mentioned_objects=objects,
        attributes=attrs or {},
    )


def test_combine_views_majority_and_choice() -> None:
    views = [
        view(0, ["car", "bus"], {"time_of_day": "night"}),
        view(1, ["car", "pedestrian"], {"time_of_day": "night"}),
        view(2, ["car", "pedestrian"], {"time_of_day": "day"}),
    ]
    chosen, objects, attrs, agreement = combine_views(views)
    assert objects == ["car", "pedestrian"]  # bus said once -> dropped
    assert attrs == {"time_of_day": "night"}
    assert chosen == 1  # agrees with the consensus on every fact
    assert agreement == pytest.approx(1 / 4)  # only "car" is unanimous of car/bus/ped/time


def test_combine_views_tie_goes_to_first_view() -> None:
    chosen, *_ = combine_views([view(0, ["car"]), view(1, ["car"])])
    assert chosen == 0


# --- claims and judge -----------------------------------------------------------------------


def test_split_claims_splits_phrases_and_wraps_subjectless_parts() -> None:
    text = (
        "A busy street at night, with cars parked on the side. The road is wet; pedestrians cross."
    )
    assert split_claims(text) == [
        "A busy street at night.",
        "The scene shows: with cars parked on the side.",
        "The road is wet.",
        "Pedestrians cross.",
    ]
    assert split_claims("The car turns left, passing orange traffic cones.") == [
        "The car turns left.",
        "The scene shows: passing orange traffic cones.",
    ]
    assert split_claims("Cars wait, and the light turns green.") == [
        "Cars wait.",
        "The light turns green.",
    ]
    assert split_reference("Night, after rain, many peds") == ["Night", "after rain", "many peds"]


def test_judge_against_aggregates_and_keeps_evidence() -> None:
    def rule(premise: str, hyp: str) -> str:
        if "night" in hyp and "daytime" in premise:
            return CONTRADICTED
        return SUPPORTED if hyp.lower().rstrip(".") in premise.lower() else NEUTRAL

    verdicts = judge_against(
        FakeJudge(rule),
        ["It is daytime.", "There are cars."],
        ["There are cars", "It is night", "A dog barks"],
    )
    assert [v.label for v in verdicts] == [SUPPORTED, CONTRADICTED, NEUTRAL]
    assert verdicts[0].evidence == "There are cars."
    assert verdicts[1].evidence == "It is daytime."
    assert judge_against(FakeJudge(), [], ["x y z"])[0].label == NEUTRAL


# --- metrics --------------------------------------------------------------------------------


def test_chair_and_coverage_hand_computed() -> None:
    sheet = make_sheet(objects={"car": 2, "pedestrian": 4, "two_wheeler": 1}, loose=["truck"])
    score = score_description(
        "Two cars and a bus pass a truck.", sheet, "Night, bus", FakeJudge(), TAX
    )
    assert score.mentioned == ["bus", "car", "truck"]
    assert score.hallucinated == ["bus"]  # truck has a (far) box, bus has none
    assert score.covered == ["car"]
    r = aggregate([score])
    assert r["chair_i"] == pytest.approx(1 / 3)
    assert r["chair_s"] == 1.0
    assert r["object_coverage"] == pytest.approx(1 / 3)


def test_aggregate_micro_and_spread() -> None:
    a = DescriptionScore(mentioned=["car"], hallucinated=[], labelled=["car"], covered=["car"])
    b = DescriptionScore(
        mentioned=["car", "bus"], hallucinated=["bus"], labelled=["car", "bus"], covered=[]
    )
    assert aggregate([a, b])["chair_i"] == pytest.approx(1 / 3)
    assert aggregate([a, b])["chair_s"] == 0.5

    from types import SimpleNamespace

    row = SimpleNamespace(per_view=[a, b])  # minimal stand-in exposing per_view
    assert within_scene_spread([row], "object_coverage") == 1.0  # type: ignore[list-item]


def test_empty_description_does_not_call_judge_on_nothing() -> None:
    score = score_description("", make_sheet(), "Night, bus", FakeJudge(), TAX)
    assert score.claims == [] and all(c.label == NEUTRAL for c in score.human_items)


# --- pipeline end to end (fake data, no model) ----------------------------------------------


class FakeFacts:
    def __init__(self) -> None:
        self.sheets: dict[tuple[str, int], SceneFactSheet] = {}

    def build(self, scene: SceneSample, v: SceneView) -> SceneFactSheet:
        night = scene.scene_name == "scene-b"
        sheet = make_sheet(
            scene.scene_name,
            v.view_id,
            night=night,
            reference="Night, many peds" if night else "Parked cars, peds",
        )
        self.sheets[(scene.scene_name, v.view_id)] = sheet
        return sheet


def fake_scenes(tmp: Path) -> list[SceneSample]:
    scenes = []
    for name in ("scene-a", "scene-b"):
        views = []
        for v in range(3):
            paths = []
            for f in range(2):
                path = tmp / f"{name}_{v}_{f}.jpg"
                Image.new("RGB", (8, 8)).save(path)
                paths.append(path)
            views.append(
                SceneView(
                    view_id=v,
                    frame_indices=[v, v + 3],
                    sample_tokens=[f"{name}-{v}-{f}" for f in range(2)],
                    image_paths=paths,
                )
            )
        scenes.append(SceneSample(scene_token=name, scene_name=name, n_keyframes=6, views=views))
    return scenes


def run_fake(tmp: Path, backend: MockBackend, name: str) -> Path:
    scenes = fake_scenes(tmp)
    facts = FakeFacts()
    pipeline = ScenePipeline(
        scenes,
        facts,
        backend,
        ScenePrompt("p", "{intro} Describe the drive."),
        TAX,
    )  # type: ignore[arg-type]
    descriptions, sheets = pipeline.run(tmp / name)
    evaluation = evaluate_scenes(descriptions, sheets, FakeJudge(), TAX)
    (tmp / name / SCENE_METRICS).write_text(evaluation.model_dump_json())
    render_scene_report(evaluation, tmp / name, "test protocol")
    return tmp / name


def test_scene_pipeline_writes_one_entry_per_scene(tmp_path: Path) -> None:
    run = run_fake(tmp_path, MockBackend("fixed", fixed_response="There are cars."), "fixed")
    rows = [json.loads(line) for line in (run / "scenes.jsonl").read_text().splitlines()]
    assert [r["scene_name"] for r in rows] == ["scene-a", "scene-b"]
    assert all(len(r["views"]) == 3 for r in rows)
    assert (run / "scenes.csv").read_text().count("\n") == 3
    assert (run / "report.md").exists()


def test_oracle_beats_always_car_and_shuffled_control(tmp_path: Path) -> None:
    scenes = fake_scenes(tmp_path)
    facts = FakeFacts()
    responses = {
        f"{s.scene_token}-v{v.view_id}": " ".join(facts.build(s, v).premise_sentences)
        for s in scenes
        for v in s.views
    }
    oracle = json.loads(
        (
            run_fake(tmp_path, MockBackend("table", responses=responses), "oracle") / SCENE_METRICS
        ).read_text()
    )["summary"]
    car = json.loads(
        (
            run_fake(tmp_path, MockBackend("fixed", fixed_response="A bus and a truck."), "car")
            / SCENE_METRICS
        ).read_text()
    )["summary"]
    assert oracle["claims_supported"] == 1.0
    assert oracle["chair_i"] == 0.0 and car["chair_i"] == 1.0
    assert oracle["object_coverage"] == 1.0 > car["object_coverage"]
    assert oracle["shuffled_claims_supported"] < oracle["claims_supported"]
    # The gap is own minus the pooled other scenes, the same numbers the report shows.
    assert oracle["specific_object_coverage"] == pytest.approx(
        oracle["object_coverage"] - oracle["shuffled_object_coverage"]
    )
    assert car["specific_object_coverage"] == pytest.approx(0.0)  # same text everywhere


def test_shuffled_control_uses_every_other_scene(tmp_path: Path) -> None:
    run = run_fake(tmp_path, MockBackend("fixed", fixed_response="There are cars."), "fixed")
    rows = json.loads((run / SCENE_METRICS).read_text())["rows"]
    assert all(len(r["shuffled"]) == len(rows) - 1 for r in rows)


def _row(name: str, own_covered: bool, other_covered: list[bool]) -> SceneRow:
    def score(covered: bool) -> DescriptionScore:
        return DescriptionScore(labelled=["car"], covered=["car"] if covered else [])

    return SceneRow(
        scene_name=name,
        reference_text="",
        description="",
        chosen_view=0,
        view_agreement=1.0,
        final=score(own_covered),
        per_view=[score(own_covered)],
        shuffled=[score(c) for c in other_covered],
        fact_sentences=[],
        words=0,
        repetition_loop=False,
        latency_s=0.0,
    )


def test_specificity_ci_and_p() -> None:
    names = [f"s{i}" for i in range(6)]
    specific = specificity([_row(n, True, [False] * 5) for n in names])
    assert specific["specific_object_coverage"] == pytest.approx(1.0)
    assert specific["specific_object_coverage_ci_low"] == pytest.approx(1.0)
    assert specific["specific_object_coverage_p"] == pytest.approx(2 / 2**6)  # exact sign flip
    generic = specificity([_row(n, True, [True] * 5) for n in names])
    assert generic["specific_object_coverage"] == pytest.approx(0.0)
    assert (
        generic["specific_object_coverage_ci_low"]
        <= 0
        <= generic["specific_object_coverage_ci_high"]
    )


def test_compare_scene_runs(tmp_path: Path) -> None:
    a = run_fake(tmp_path, MockBackend("fixed", fixed_response="There are cars."), "a")
    b = run_fake(tmp_path, MockBackend("fixed", fixed_response="A bus."), "b")
    text = compare_scene_runs(a, b, tmp_path / "cmp").read_text()
    assert "Object coverage" in text and "Sign-flip p" in text


def test_scene_prompts_render() -> None:
    for name in ("scene_open", "scene_guided"):
        text = load_scene_prompt(name).render(n_frames=6, span_s=16.5)
        assert "6 images" in text and "3 seconds" in text and "{" not in text


# --- real data (skipped without nuScenes) ---------------------------------------------------


def test_scene_loader_and_fact_sheet_on_mini(nusc) -> None:  # type: ignore[no-untyped-def]
    scenes = list(NuScenesSceneLoader(str(DATAROOT), nusc=nusc))
    assert len(scenes) == 10 and all(len(s.views) == 3 for s in scenes)
    builder = SceneFactBuilder(str(DATAROOT), nusc=nusc)
    by_name = {s.scene_name: s for s in scenes}
    waiting = builder.build(by_name["scene-0553"], by_name["scene-0553"].views[1])
    assert waiting.ego is not None and waiting.ego.state == "stopped"  # "Wait at intersection"
    turning = builder.build(by_name["scene-0061"], by_name["scene-0061"].views[1])
    assert turning.ego is not None and turning.ego.turn == "left"  # "turn left"
    night = builder.build(by_name["scene-1094"], by_name["scene-1094"].views[0])
    assert "It is night." in night.premise_sentences
    assert all(isinstance(s, FactSentence) for s in night.sentences)
    assert set(night.objects) <= set(night.loosely_present)


def test_scene_descriptions_model_roundtrip() -> None:
    d = SceneDescription(
        scene_token="t",
        scene_name="s",
        model="m",
        prompt_version="p",
        description="x",
        chosen_view=0,
        view_agreement=1.0,
    )
    assert SceneDescription.model_validate_json(d.model_dump_json()) == d


def test_judge_validation_probes_have_known_truth() -> None:
    from vlm_eval.evaluation.judge_validation import (
        probe_claims,
        summarize_probes,
        validate_judge,
    )

    sheet = make_sheet(objects={"car": 2}, loose=["truck"], night=True)
    probes = probe_claims(sheet, TAX)
    texts = {p.claim: p.truth for p in probes}
    assert texts["Some cars can be seen in the scene."] is True
    assert texts["A bus is clearly visible in the scene."] is False
    assert "A truck is clearly visible in the scene." not in texts  # far box: truth unknown
    assert texts["The drive takes place at night."] is True
    assert texts["The vehicle carrying the camera is not moving."] is True  # sheet: stopped

    def rule(premise: str, hyp: str) -> str:  # a judge that supports everything
        return SUPPORTED

    summary = summarize_probes(validate_judge([sheet], FakeJudge(rule), TAX))
    assert summary["all"]["true_supported"] == 1.0
    assert summary["all"]["false_supported"] == 1.0  # the validation exposes such a judge


def test_specificity_verdict_wording() -> None:
    from vlm_eval.evaluation.scene_report import specificity_verdict

    def gaps(**cis: tuple[float, float, float]) -> dict[str, float | None]:
        out: dict[str, float | None] = {}
        for key, (lo, hi, p) in cis.items():
            out[f"specific_{key}_ci_low"], out[f"specific_{key}_ci_high"] = lo, hi
            out[f"specific_{key}_p"] = p
        return out

    generic = specificity_verdict(
        gaps(
            claims_supported=(-0.3, -0.05, 0.01),  # CI below 0 and p < 0.05
            object_coverage=(-0.05, 0.05, 0.6),
            human_coverage=(-0.02, 0.1, 0.4),
        )
    )
    assert "no clear evidence" in generic and "better than their own on claims" in generic
    specific = specificity_verdict(
        gaps(
            claims_supported=(0.2, 0.5, 0.002),
            object_coverage=(0.02, 0.2, 0.15),  # CI above 0 but p = 0.15 -> borderline
            human_coverage=(-0.1, 0.1, 0.5),
        )
    )
    assert "specific to their own scene on claims (" in specific
    assert "Borderline (CI and exact test disagree) on objects." in specific
    assert "no shuffled control" in specificity_verdict({})


def test_significance_rule() -> None:
    from vlm_eval.evaluation.stats import significance

    assert significance(0.1, 0.3, 0.01) == "higher"
    assert significance(-0.3, -0.1, 0.01) == "lower"
    assert significance(0.01, 0.2, 0.15) == "borderline"  # CI only
    assert significance(-0.1, 0.2, 0.03) == "borderline"  # p only
    assert significance(-0.1, 0.2, 0.5) == "inconclusive"
    assert significance(None, None, 0.01) == "inconclusive"


@pytest.mark.parametrize(
    ("claim", "kind"),
    [
        ("The car turns left at the intersection.", "motion"),
        ("Several pedestrians are on the sidewalk.", "objects"),
        ("It is night and the road is wet.", "conditions"),
        ("The scene is in a parking lot.", "place"),
        ("Tall buildings line the street.", "place"),
        ("The sky is cloudy.", "other"),
    ],
)
def test_claim_type(claim: str, kind: str) -> None:
    from vlm_eval.evaluation.scene_metrics import claim_type

    assert claim_type(claim, TAX) == kind


def test_multi_camera_views_and_prompt(nusc) -> None:  # type: ignore[no-untyped-def]
    cams = ["CAM_FRONT_LEFT", "CAM_FRONT", "CAM_FRONT_RIGHT"]
    scene = next(
        iter(NuScenesSceneLoader(str(DATAROOT), cameras=cams, scenes=["scene-1094"], nusc=nusc))
    )
    view = scene.views[0]
    assert view.cameras == cams and len(view.image_paths) == 18  # 6 frames x 3 cameras
    assert view.image_ids[:3] == [f"{view.sample_tokens[0]}:{c}" for c in cams]  # time-major
    assert all(cam in str(p) for p, cam in zip(view.image_paths[:3], cams, strict=True))
    text = load_scene_prompt("scene_open").render(6, 15.0, view.cameras)
    assert "18 images" in text and "front-left, front, front-right" in text

    builder = SceneFactBuilder(str(DATAROOT), nusc=nusc)
    front_only = builder.build(
        scene,
        view.model_copy(
            update={"cameras": ["CAM_FRONT"], "image_paths": view.image_paths[1::3], "view_id": 9}
        ),
    )
    wide = builder.build(scene, view)
    assert set(front_only.objects) <= set(wide.objects)  # more cameras never lose objects
    assert sum(wide.objects.values()) >= sum(front_only.objects.values())


def test_gate_reads_scene_runs(tmp_path: Path) -> None:
    from vlm_eval.evaluation.gate import evaluate_gate, load_summary

    run = run_fake(tmp_path, MockBackend("fixed", fixed_response="There are cars."), "gated")
    summary = load_summary(run)
    assert "object_coverage" in summary  # flat scene keys
    checks = evaluate_gate({"thresholds": {"object_coverage": {"min": 0.0}}}, summary)
    assert [c.passed for c in checks] == [True]


def test_gate_files_only_name_metrics_that_runs_produce(tmp_path: Path) -> None:
    """Guards against stale gate keys after a metric is renamed or removed."""
    from tests.conftest import FakeLoader
    from tests.test_pipeline import build
    from vlm_eval.evaluation.gate import load_gate, load_summary

    root = Path(__file__).resolve().parents[1]
    scene_run = run_fake(tmp_path, MockBackend("fixed", fixed_response="There are cars."), "g")
    frame_run = tmp_path / "frames"
    build(FakeLoader(tmp_path), "always_car").run(frame_run)
    for gate_file, run in (("gates.yaml", scene_run), ("gates_frames.yaml", frame_run)):
        spec = load_gate(root / "configs" / gate_file)
        keys = set(spec.get("thresholds") or {}) | set(spec.get("regression") or {})
        missing = keys - set(load_summary(run))
        assert not missing, f"{gate_file} names metrics no run produces: {missing}"
