from doctor.paper2.langgraph_router.routing import decide_route


def test_b0_always_generates():
    gate = {
        "vision_quality": 0.1,
        "entity_completeness": 0.0,
        "contradiction_penalty": 0.9,
        "gamma_conflict": 0.0,
        "tau_gating": 0.65,
    }
    assert decide_route(gate, baseline="B0", retry_count=0) == "generate_emr"


def test_b3_resamples_low_quality():
    gate = {
        "vision_quality": 0.4,
        "entity_completeness": 1.0,
        "contradiction_penalty": 0.0,
        "gamma_conflict": 0.5,
        "tau_gating": 0.65,
    }
    assert decide_route(gate, baseline="B3", retry_count=0) == "resample_vision"


def test_kg_contradiction_queries_kg():
    gate = {
        "vision_quality": 0.8,
        "entity_completeness": 1.0,
        "contradiction_penalty": 0.7,
        "gamma_conflict": 0.3,
        "tau_gating": 0.65,
    }
    assert decide_route(gate, baseline="B2", retry_count=0) == "query_kg"


def test_retry_limit_routes_to_human_review_then_fail_safe():
    gate = {
        "vision_quality": 0.8,
        "entity_completeness": 1.0,
        "contradiction_penalty": 0.0,
        "gamma_conflict": 0.2,
        "tau_gating": 0.65,
    }

    assert decide_route(gate, baseline="B4", retry_count=2, max_retries=1) == "human_review"
    assert decide_route(gate, baseline="B4", retry_count=3, max_retries=1) == "fail_safe"
