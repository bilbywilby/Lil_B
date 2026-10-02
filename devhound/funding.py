"""FUNDING.json validation (offline). Rules follow the ecosystem spec:

DH-FUND-001  invalid JSON / wrong top-level type
DH-FUND-002  use_of_funds_breakdown must contain the five required fields
DH-FUND-003  breakdown values must be numbers 0-100 and sum to exactly 100
DH-FUND-004  boolean flags must be real JSON booleans
DH-FUND-005  sponsors must reference a defined tier
DH-FUND-006  license must be a recognised SPDX identifier
DH-FUND-007  funding_status present but no breakdown while seeking_funding is true
DH-FUND-008  privacy flags: telemetry_opt_in must be false unless explicitly intended
"""
import json
from decimal import Decimal
from pathlib import Path

from .findings import Finding
from .spdx import unknown_ids

REQUIRED_BREAKDOWN = (
    "infrastructure_costs_percentage",
    "developer_compensation_percentage",
    "community_support_percentage",
    "legal_and_compliance_percentage",
    "reserve_and_emergency_percentage",
)
BOOLEAN_KEYS = {
    "seeking_funding", "active", "accepts_donations", "accepts_individual_donations",
    "accepts_corporate_donations", "accepts_in_kind", "telemetry_opt_in",
    "sponsor_listing_requires_consent", "publish_donor_names",
    "cloud_calls_default", "cloud_features_opt_in",
}

TEMPLATE = {
    "schema_version": "1.0",
    "project": {"name": "YourProject", "repository": "", "license": "MIT"},
    "funding_status": {
        "seeking_funding": False,
        "active": True,
        "accepts_individual_donations": True,
        "accepts_corporate_donations": False,
        "accepts_in_kind": False,
    },
    "use_of_funds_breakdown": {
        "infrastructure_costs_percentage": 20,
        "developer_compensation_percentage": 40,
        "community_support_percentage": 20,
        "legal_and_compliance_percentage": 10,
        "reserve_and_emergency_percentage": 10,
    },
    "privacy": {
        "telemetry_opt_in": False,
        "publish_donor_names": False,
        "sponsor_listing_requires_consent": True,
    },
}


def _line_of(text, key):
    needle = f'"{key}"'
    for i, line in enumerate(text.splitlines(), 1):
        if needle in line:
            return i
    return None


def _walk_booleans(node, path, out):
    if isinstance(node, dict):
        for k, v in node.items():
            p = f"{path}.{k}" if path else k
            if k in BOOLEAN_KEYS and type(v) is not bool:
                out.append((p, k, v))
            _walk_booleans(v, p, out)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            _walk_booleans(v, f"{path}[{i}]", out)


def validate_data(data, text="", path="FUNDING.json", strict=False):
    f = []

    def add(rule, level, msg, key=None, fix=None):
        f.append(Finding(rule, level, msg, path, _line_of(text, key) if key else None, 1 if key else None, fix))

    if not isinstance(data, dict):
        add("DH-FUND-001", "error", "Top-level JSON value must be an object.")
        return f

    bd = data.get("use_of_funds_breakdown")
    if bd is None:
        if strict:
            add("DH-FUND-002", "error", "Missing use_of_funds_breakdown.", fix="Add the five *_percentage fields; they must total 100.")
        if data.get("funding_status", {}).get("seeking_funding") is True:
            add("DH-FUND-007", "error", "seeking_funding is true but use_of_funds_breakdown is missing.", "seeking_funding",
                "Publish how funds are used before asking for them.")
    elif not isinstance(bd, dict):
        add("DH-FUND-002", "error", "use_of_funds_breakdown must be an object.", "use_of_funds_breakdown")
    else:
        missing = [k for k in REQUIRED_BREAKDOWN if k not in bd]
        if missing:
            add("DH-FUND-002", "error", f"use_of_funds_breakdown missing fields: {', '.join(missing)}", "use_of_funds_breakdown")
        bad = [k for k, v in bd.items() if isinstance(v, bool) or not isinstance(v, (int, float, Decimal)) or not (0 <= Decimal(str(v)) <= 100)]
        if bad:
            add("DH-FUND-003", "error", f"Breakdown values must be numbers between 0 and 100: {', '.join(bad)}", "use_of_funds_breakdown")
        else:
            total = sum(Decimal(str(v)) for v in bd.values())
            if total != 100:
                add("DH-FUND-003", "error", f"use_of_funds_breakdown sums to {total}, expected exactly 100.", "use_of_funds_breakdown",
                    "Adjust the percentages so they total 100.")

    status = data.get("funding_status")
    if status is not None:
        if not isinstance(status, dict):
            add("DH-FUND-004", "error", f"funding_status must be an object of true/false flags, found {json.dumps(status, default=str)}.",
                "funding_status", 'Use e.g. {"seeking_funding": false, "active": true}; put descriptive text under project.funding_model.')
        else:
            for k, v in status.items():
                if type(v) is not bool:
                    add("DH-FUND-004", "error", f"funding_status.{k} must be a JSON boolean, found {json.dumps(v, default=str)}.", k,
                        "Use true or false without quotes.")
    if "seeking_funding" in data:
        add("DH-FUND-004", "error", "seeking_funding belongs inside funding_status, not at the top level.", "seeking_funding",
            "Move it under funding_status.")

    bad_bools = []
    _walk_booleans(data, "", bad_bools)
    for p, k, v in bad_bools:
        if p.startswith("funding_status."):
            continue
        add("DH-FUND-004", "error", f"{p} must be a JSON boolean (true/false), found {json.dumps(v, default=str)}.", k,
            'Use true or false without quotes.')

    corp = data.get("corporate_sponsorship") or {}
    names = [t.get("name") for t in corp.get("sponsorship_levels", []) if isinstance(t, dict)]
    if len(names) != len(set(names)):
        add("DH-FUND-005", "error", "Duplicate sponsorship tier names.", "sponsorship_levels")
    for s in corp.get("existing_sponsors", []):
        if s.get("level") not in names:
            add("DH-FUND-005", "error", f"Sponsor {s.get('company_name')!r} references undefined tier {s.get('level')!r}.", "existing_sponsors")

    lic = (data.get("project") or {}).get("license")
    if lic:
        unk = unknown_ids(lic)
        if unk:
            add("DH-FUND-006", "error" if strict else "warning",
                f"License {lic!r} has identifiers not in the bundled SPDX list: {', '.join(unk)}", "license",
                "Check spelling against https://spdx.org/licenses/ (the bundled list is a common-license subset).")

    if (data.get("privacy") or {}).get("telemetry_opt_in") is True:
        add("DH-FUND-008", "warning", "telemetry_opt_in is true. DevHound defaults to no telemetry.", "telemetry_opt_in")
    return f


def validate_file(path, strict=False):
    p = Path(path)
    try:
        text = p.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None, [Finding("DH-FUND-001", "error", f"{p} not found.", str(p), fix="Run `devhound init` to create one.")]
    try:
        data = json.loads(text, parse_float=Decimal)
    except json.JSONDecodeError as e:
        return None, [Finding("DH-FUND-001", "error", f"Invalid JSON: {e.msg}", str(p), e.lineno, e.colno)]
    return data, validate_data(data, text, str(p), strict)
