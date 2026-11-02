from apm.cli import main

from .conftest import ROOT


def test_validate_example_succeeds(capsys):
    assert main(["validate", str(ROOT / "catalog"), "--today", "2026-11-02"]) == 0


def test_validate_fails_on_error_and_emits_github_annotations(repo, capsys):
    repo.edit("applications/app-kyc/application.yaml", lambda d: d["organisation"].update(owner="org-x"))
    assert main(["validate", str(repo.root), "--format", "github", "--today", "2026-11-02"]) == 1
    assert "::error file=" in capsys.readouterr().out


def test_build_generates_site(tmp_path):
    out = tmp_path / "site"
    assert main(["build", str(ROOT / "catalog"), "-o", str(out), "--today", "2026-11-02"]) == 0
    assert (out / "index.html").exists() and (out / "catalog.json").exists()
    assert (out / "apps" / "app-kyc.html").exists()
