from doctor.paper2.tools.entity_normalizer import normalize_entities, normalize_entity


def test_normalize_entity_accepts_project_aliases():
    assert normalize_entity("sore throat") == "sore_throat"
    assert normalize_entity("sore_throat") == "sore_throat"
    assert normalize_entity("咽痛") == "sore_throat"
    assert normalize_entity("yellow-greasy-coating") == "yellow_greasy_coating"


def test_normalize_entities_deduplicates_and_drops_unknowns():
    assert normalize_entities(["fever", "发热", "unknown", "red tongue"]) == [
        "fever",
        "red_tongue",
    ]
