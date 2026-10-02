// Pure logic, no VS Code or filesystem access, so it can be unit-tested with plain Node.
"use strict";

const SUBCOMMANDS = {
  scan: ["scan", ".", "--format", "json"],
  check: ["check", "--format", "json"],
  brand: ["brand", "--format", "json"],
};

/** Ordered list of [command, baseArgs] to try; the second is the Python fallback. */
function commandCandidates(executable) {
  const exe = (executable || "devhound").trim() || "devhound";
  return [[exe, []], ["python3", ["-m", "devhound"]]];
}

function buildArgs(kind, base) {
  if (!SUBCOMMANDS[kind]) throw new Error("unknown command: " + kind);
  return base.concat(SUBCOMMANDS[kind]);
}

/** devhound prints a JSON array of findings on stdout. Returns [] for empty output. */
function parseFindings(stdout) {
  const text = String(stdout || "").trim();
  if (!text) return [];
  const data = JSON.parse(text);
  if (!Array.isArray(data)) throw new Error("unexpected output shape");
  return data;
}

/** Group findings by file path and convert to zero-based ranges. */
function groupByFile(findings) {
  const map = new Map();
  for (const f of findings) {
    const line = Math.max((f.line || 1) - 1, 0);
    const col = Math.max((f.column || 1) - 1, 0);
    const msg = `${f.message} [${f.rule_id}]` + (f.fix ? `\nFix: ${f.fix}` : "");
    if (!map.has(f.path)) map.set(f.path, []);
    map.get(f.path).push({ line, col, level: f.level, message: msg, code: f.rule_id });
  }
  return map;
}

module.exports = { commandCandidates, buildArgs, parseFindings, groupByFile };
