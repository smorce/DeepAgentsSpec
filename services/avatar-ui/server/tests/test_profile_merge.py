import copy

from src.profile_service import ProfileUpdate, apply_profile_updates


def test_apply_profile_updates_respects_confidence_and_empty_values():
    schema = {
        "基本情報": {"名前": {"フルネーム": ""}},
        "性格": {"気質": {"明るい/暗い": ""}},
    }
    profile = copy.deepcopy(schema)
    updates = [
        ProfileUpdate(path=["基本情報", "名前", "フルネーム"], value="山田太郎", confidence=0.2),
        ProfileUpdate(path=["性格", "気質", "明るい/暗い"], value="", confidence=0.9),
        ProfileUpdate(path=["性格", "気質", "明るい/暗い"], value="明るい", confidence=0.95),
    ]

    updated, applied = apply_profile_updates(profile, schema, updates, min_confidence=0.6)

    assert applied == 1
    assert updated["基本情報"]["名前"]["フルネーム"] == ""
    assert updated["性格"]["気質"]["明るい/暗い"] == "明るい"


def test_apply_profile_updates_skips_invalid_paths():
    schema = {"基本情報": {"名前": {"フルネーム": ""}}}
    profile = copy.deepcopy(schema)
    updates = [
        ProfileUpdate(path=["基本情報", "名前", "ミドルネーム"], value="太郎", confidence=0.9),
    ]

    updated, applied = apply_profile_updates(profile, schema, updates, min_confidence=0.6)

    assert applied == 0
    assert updated == schema
