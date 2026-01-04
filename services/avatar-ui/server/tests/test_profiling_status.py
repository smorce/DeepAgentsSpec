from src import profile_service


def test_run_profiling_includes_exception_message(monkeypatch):
    def raise_error(_: str):
        raise RuntimeError("Failed to load profile YAML: path")

    monkeypatch.setattr(profile_service, "update_profile_from_transcript", raise_error)

    status = profile_service.run_profiling("test transcript")

    assert status.status == "failed"
    assert status.message == "Failed to load profile YAML: path"
