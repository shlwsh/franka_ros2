from doctor.paper2.agents.kg_conflict_agent import compute_conflict_gate


def test_supporting_entities_score_above_conflict_case():
    supporting = compute_conflict_gate(
        symptom_entities=[{"name": "fever"}, {"name": "sore_throat"}],
        expected_entities=["fever", "sore_throat"],
        vision_tags=[{"name": "red_tongue"}],
        q_img=0.9,
    )
    conflicting = compute_conflict_gate(
        symptom_entities=[{"name": "cold_aversion"}],
        expected_entities=["cold_aversion"],
        vision_tags=[{"name": "yellow_greasy_coating"}],
        q_img=0.9,
    )
    assert supporting["gamma_conflict"] > conflicting["gamma_conflict"]
    assert conflicting["contradiction_penalty"] > 0
