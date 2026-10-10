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
    aggregate,
    evaluate_scenes,
    score_description,
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


def test_split_claims_keeps_subjectless_phrases_attached() -> None:
    text = (
        "A busy street at night, with cars parked on the side. The road is wet; pedestrians cross."
    )
    assert split_claims(text) == [
        "A busy street at night, with cars parked on the side.",
        "The road is wet.",
        "Pedestrians cross.",
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
        ScenePrompt("p", "Describe {n_frames} frames, {spacing}s apart."),
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


def test_compare_scene_runs(tmp_path: Path) -> None:
    a = run_fake(tmp_path, MockBackend("fixed", fixed_response="There are cars."), "a")
    b = run_fake(tmp_path, MockBackend("fixed", fixed_response="A bus."), "b")
    text = compare_scene_runs(a, b, tmp_path / "cmp").read_text()
    assert "Object coverage" in text and "McNemar" in text


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


def test_judge_box_check_precisions() -> None:
    from vlm_eval.evaluation.scene_metrics import CheckedText, judge_box_check

    claims = [
        CheckedText(text="A bus.", label=SUPPORTED, object_class="bus", box_present=True),
        CheckedText(text="A truck.", label=SUPPORTED, object_class="truck", box_present=False),
        CheckedText(
            text="No cones.", label=CONTRADICTED, object_class="traffic_cone", box_present=False
        ),
        CheckedText(text="A dog.", label=NEUTRAL, object_class="car", box_present=True),
        CheckedText(text="It is night.", label=SUPPORTED),
        CheckedText(
            text="A long claim about a bus that goes on and on.",
            label=SUPPORTED,
            object_class="bus",
            box_present=False,
        ),
    ]
    check = judge_box_check([DescriptionScore(claims=claims)])
    assert check["judge_support_n"] == 2 and check["judge_support_precision"] == 0.5
    assert check["judge_contradiction_n"] == 1 and check["judge_contradiction_precision"] == 1.0
