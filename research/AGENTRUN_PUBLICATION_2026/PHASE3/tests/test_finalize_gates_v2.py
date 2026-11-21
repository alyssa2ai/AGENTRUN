"""Tests for the g4-v2 client-identity policy in scripts/finalize_gates.py.

    python -m pytest research/AGENTRUN_PUBLICATION_2026/PHASE3/tests -q

The seven cases required by the G4 resolution:
  1 a change in gpu_mem_gib alone does not fail client identity (and is reported)
  2 a changed client adapter fails
  3 a changed parser version fails
  4 a changed framework version fails
  5 an unknown new field fails until it is explicitly classified
  6 missing client metadata fails
  7 the 16 single-start cells still pass their strict checks (against the real campaign manifests)
"""
import hashlib
import json
import sys
from pathlib import Path

import pytest

P3 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P3 / "scripts"))

import finalize_gates as fg  # noqa: E402

V1_SHA256 = "8c1870f0725131c12ee4a4b3b67687426c3490b9d6967643b41f1364dc9e704d"

BASE_CLIENT = {
    "backend": "hf-local", "family": "qwen", "family_adapter": "evarb.clients.FamilyClient/1",
    "model": "Qwen/Qwen3-8B", "model_path": "/cache/models--Qwen--Qwen3-8B/snapshots/b968826d",
    "adapter": None, "adapter_sha256": None, "temperature": 0.7, "seed": 3,
    "decoding": "sampling top_p=0.9", "max_new_tokens": 700, "dtype": "bfloat16",
    "thinking": "disabled via chat template where supported", "parser_version": "two-pass-v2+client-fallback",
    "torch": "2.15.0+cu132", "transformers": "5.22.2", "cuda": "13.2", "gpu": "NVIDIA L40",
    "gpu_mem_gib": 44.6,
}


def manifests(*client_overrides):
    """Build one manifest line per start; each override is applied to a copy of BASE_CLIENT."""
    out = []
    for i, ov in enumerate(client_overrides):
        c = dict(BASE_CLIENT)
        for k, v in ov.items():
            if v is fg._MISSING:
                c.pop(k, None)
            else:
                c[k] = v
        out.append({"client": c, "temperature": 0.7, "seed": 3, "split_sha256": "602eb748",
                    "code_sha256": {"run_p2.py": "6be2011c"}, "configs": ["B", "G"],
                    "slurm_job_id": str(4315 + i), "resumed_with_done": 0 if i == 0 else 2345})
    return out


def test_1_gpu_mem_gib_alone_is_observational_and_reported():
    fails, obs = fg.check_client_identity("cell", manifests({}, {"gpu_mem_gib": 44.4}))
    assert fails == [], fails
    assert obs == {"gpu_mem_gib": [44.6, 44.4]}


def test_1b_identical_starts_report_nothing():
    fails, obs = fg.check_client_identity("cell", manifests({}, {}))
    assert fails == [] and obs == {}


def test_1c_single_start_cell_passes():
    fails, obs = fg.check_client_identity("cell", manifests({}))
    assert fails == [] and obs == {}


@pytest.mark.parametrize("field,changed", [
    ("family_adapter", "evarb.clients.FamilyClient/2"),
    ("adapter", "/adapters/qlora-v3"),
    ("adapter_sha256", "deadbeef"),
    ("backend", "vllm"),
])
def test_2_changed_client_adapter_fails(field, changed):
    fails, _ = fg.check_client_identity("cell", manifests({}, {field: changed}))
    assert any(f"client.{field} differs" in f for f in fails), fails
    assert any(json.dumps(changed) in f for f in fails), "the differing values must be printed"


def test_3_changed_parser_version_fails():
    fails, _ = fg.check_client_identity("cell", manifests({}, {"parser_version": "two-pass-v3"}))
    assert any("client.parser_version differs" in f for f in fails), fails


@pytest.mark.parametrize("field,changed", [
    ("transformers", "5.23.0"), ("torch", "2.16.0+cu132"), ("cuda", "13.3"),
])
def test_4_changed_framework_version_fails(field, changed):
    fails, _ = fg.check_client_identity("cell", manifests({}, {field: changed}))
    assert any(f"client.{field} differs" in f for f in fails), fails


def test_5_unknown_field_fails_until_classified():
    fails, _ = fg.check_client_identity("cell", manifests({"driver_version": "580.173.02"},
                                                          {"driver_version": "580.178.04"}))
    assert any("unclassified client field" in f and "driver_version" in f for f in fails), fails
    # ... and it still fails even when the new field is IDENTICAL across starts: fail closed, not fail on difference
    fails2, _ = fg.check_client_identity("cell", manifests({"driver_version": "580.178.04"},
                                                           {"driver_version": "580.178.04"}))
    assert any("unclassified client field" in f for f in fails2), fails2
    # ... and passes once classified
    try:
        fg.CLIENT_IDENTITY = fg.CLIENT_IDENTITY + ("driver_version",)
        fails3, _ = fg.check_client_identity("cell", manifests({"driver_version": "580.178.04"},
                                                               {"driver_version": "580.178.04"}))
        assert fails3 == [], fails3
    finally:
        fg.CLIENT_IDENTITY = tuple(k for k in fg.CLIENT_IDENTITY if k != "driver_version")


def test_6_missing_client_metadata_fails():
    # whole client object absent
    man = manifests({}, {})
    del man[1]["client"]
    fails, _ = fg.check_client_identity("cell", man)
    assert any("no client metadata" in f for f in fails), fails
    # client present but empty
    man = manifests({}, {})
    man[1]["client"] = {}
    fails, _ = fg.check_client_identity("cell", man)
    assert any("no client metadata" in f for f in fails), fails
    # a single identity field absent from one start
    fails, _ = fg.check_client_identity("cell", manifests({}, {"model_path": fg._MISSING}))
    assert any("client.model_path missing in start(s) [1]" in f for f in fails), fails
    # no manifest at all
    fails, _ = fg.check_client_identity("cell", [])
    assert any("no manifest" in f for f in fails), fails


def test_6b_every_identity_field_is_checked():
    for k in fg.CLIENT_IDENTITY:
        sentinel = "CHANGED" if not isinstance(BASE_CLIENT[k], (int, float)) or isinstance(BASE_CLIENT[k], bool) else 999
        fails, _ = fg.check_client_identity("cell", manifests({}, {k: sentinel}))
        assert any(f"client.{k} differs" in f for f in fails), f"{k} is not enforced"


def test_6c_observational_set_is_not_in_identity_set():
    assert not (set(fg.CLIENT_IDENTITY) & set(fg.CLIENT_OBSERVATIONAL))
    assert fg.CLIENT_OBSERVATIONAL == ("gpu_mem_gib",)


def test_top_level_identity_still_strict():
    man = manifests({}, {})
    man[1]["code_sha256"] = {"run_p2.py": "0000"}
    assert any("code_sha256 differs" in f for f in fg.check_top_identity("cell", man))
    man = manifests({}, {})
    man[1]["split_sha256"] = "0000"
    assert any("split_sha256 differs" in f for f in fg.check_top_identity("cell", man))


def test_v1_validator_is_preserved_verbatim():
    p = P3 / "scripts" / "finalize_gates_v1_frozen.py"
    assert p.exists(), "the original g4-v1 validator must be preserved"
    assert hashlib.sha256(p.read_bytes()).hexdigest() == V1_SHA256


# --- case 7: the real campaign manifests -------------------------------------------------------------------------
RAW_CANDIDATES = [Path.home() / "AGENTRUN_HPC" / "phase3_raw", P3 / "RAW_RESULTS"]
RAW = next((p for p in RAW_CANDIDATES if p.exists() and any(p.glob("eval3_*/manifest.jsonl"))), None)
needs_raw = pytest.mark.skipif(RAW is None, reason="campaign raw results not present on this machine")


@needs_raw
def test_7_real_cells_pass_and_only_the_two_known_cells_report_telemetry():
    reported, failed = {}, {}
    for cell in fg.CELLS:
        mp = RAW / f"eval3_{cell}" / "manifest.jsonl"
        assert mp.exists(), f"missing manifest for {cell}"
        man = [json.loads(x) for x in open(mp, encoding="utf-8") if x.strip()]
        fails, obs = fg.check_client_identity(cell, man)
        fails += fg.check_top_identity(cell, man)
        if fails:
            failed[cell] = fails
        if obs:
            reported[cell] = obs
    assert failed == {}, failed
    assert set(reported) == {"qwen3_8b_T07_s3", "llama32_3b_greedy"}, reported
    for cell, obs in reported.items():
        assert obs == {"gpu_mem_gib": [44.6, 44.4]}, (cell, obs)


@needs_raw
def test_7b_sixteen_single_start_cells_are_unaffected():
    single = []
    for cell in fg.CELLS:
        man = [json.loads(x) for x in open(RAW / f"eval3_{cell}" / "manifest.jsonl", encoding="utf-8") if x.strip()]
        if len(man) == 1:
            single.append(cell)
            fails, obs = fg.check_client_identity(cell, man)
            assert fails == [] and obs == {}, (cell, fails, obs)
    assert len(single) == 16, single


@needs_raw
def test_7c_v1_would_have_failed_exactly_those_two_cells():
    """The regression this policy fixes: g4-v1 compared `client` as one blob."""
    v1_fails = []
    for cell in fg.CELLS:
        man = [json.loads(x) for x in open(RAW / f"eval3_{cell}" / "manifest.jsonl", encoding="utf-8") if x.strip()]
        if len({json.dumps(m.get("client"), sort_keys=True) for m in man}) > 1:
            v1_fails.append(cell)
    assert v1_fails == ["qwen3_8b_T07_s3", "llama32_3b_greedy"] or set(v1_fails) == {
        "qwen3_8b_T07_s3", "llama32_3b_greedy"}, v1_fails
