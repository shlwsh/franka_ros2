from doctor.paper2.langgraph_router.graph import run_trial
from doctor.paper2.tools.dataset_loader import load_cases


def test_b3_low_quality_case_uses_resample_tool():
    case = next(item for item in load_cases() if item["conflict_type"] == "vision_low_quality")
    state = run_trial(case, baseline="B3", trial_id="test_001")
    assert any(call["tool"] == "execute_skill" for call in state["tool_calls"])
    assert state["q_img"] >= 0.55
