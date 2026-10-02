"""SARIF v2.1.0 output (spec section 2B)."""
from . import __version__

_RULES = {
    "DH-SEC-001": "Hardcoded secret-like value",
    "DH-SEC-002": "AWS access key ID", "DH-SEC-003": "GitHub token", "DH-SEC-004": "Slack token",
    "DH-SEC-005": "Private key block", "DH-SEC-006": "Google API key", "DH-SEC-007": "Stripe live key",
    "DH-SEC-008": "DevHound personal access token",
    "DH-FUND-001": "FUNDING.json unreadable", "DH-FUND-002": "Breakdown fields", "DH-FUND-003": "Breakdown total",
    "DH-FUND-004": "Boolean types", "DH-FUND-005": "Sponsor tiers", "DH-FUND-006": "SPDX license",
    "DH-FUND-007": "Funding ask without breakdown", "DH-FUND-008": "Telemetry flag",
    "DH-BRAND-001": "Missing brand asset", "DH-BRAND-002": "Brand asset altered or invalid",
}


def to_sarif(findings):
    results = []
    for f in findings:
        loc = {"artifactLocation": {"uri": f.path}}
        if f.line:
            loc["region"] = {"startLine": f.line, "startColumn": f.column or 1}
        r = {"ruleId": f.rule_id, "level": f.level, "message": {"text": f.message},
             "locations": [{"physicalLocation": loc}]}
        if f.fingerprint:
            r["partialFingerprints"] = {"devhound/v1": f.fingerprint}
        results.append(r)
    return {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [{
            "tool": {"driver": {
                "name": "DevHound Sniffer", "semanticVersion": __version__,
                "rules": [{"id": k, "shortDescription": {"text": v}} for k, v in _RULES.items()],
            }},
            "results": results,
        }],
    }
