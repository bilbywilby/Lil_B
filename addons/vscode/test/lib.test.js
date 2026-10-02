const test = require("node:test");
const assert = require("node:assert");
const lib = require("../lib");
const { activate } = require("../extension");

test("args are an array, never a shell string", () => {
  assert.deepStrictEqual(lib.buildArgs("scan", []), ["scan", ".", "--format", "json"]);
  assert.deepStrictEqual(lib.buildArgs("check", ["-m", "devhound"]), ["-m", "devhound", "check", "--format", "json"]);
  assert.throws(() => lib.buildArgs("rm -rf /", []));
});

test("falls back to python3 -m devhound", () => {
  const c = lib.commandCandidates("devhound");
  assert.deepStrictEqual(c[1], ["python3", ["-m", "devhound"]]);
  assert.strictEqual(lib.commandCandidates("  ")[0][0], "devhound");
});

test("parseFindings handles empty, valid and bad output", () => {
  assert.deepStrictEqual(lib.parseFindings(""), []);
  assert.deepStrictEqual(lib.parseFindings("[]"), []);
  assert.throws(() => lib.parseFindings("not json"));
  assert.throws(() => lib.parseFindings('{"a":1}'));
});

test("groupByFile converts to zero-based ranges and keeps fix hints", () => {
  const m = lib.groupByFile([{ path: "a.py", line: 3, column: 5, level: "error", message: "bad", rule_id: "DH-SEC-002", fix: "rotate it" }]);
  const d = m.get("a.py")[0];
  assert.strictEqual(d.line, 2);
  assert.strictEqual(d.col, 4);
  assert.match(d.message, /bad \[DH-SEC-002\]\nFix: rotate it/);
});

function fakeVscode() {
  const sets = [];
  const handlers = {};
  const collection = { clear() { sets.length = 0; }, set(u, d) { sets.push([u.fsPath, d]); }, dispose() {} };
  const status = { text: "", show() {}, dispose() {} };
  const messages = [];
  const vscode = {
    DiagnosticSeverity: { Error: 0, Warning: 1, Information: 2 },
    StatusBarAlignment: { Left: 1 },
    Range: class { constructor(a, b, c, d) { Object.assign(this, { a, b, c, d }); } },
    Diagnostic: class { constructor(r, m, s) { Object.assign(this, { range: r, message: m, severity: s }); } },
    Uri: { file: (p) => ({ fsPath: p }) },
    languages: { createDiagnosticCollection: () => collection },
    window: {
      createStatusBarItem: () => status,
      showErrorMessage: (m) => messages.push(["error", m]),
      showWarningMessage: (m) => messages.push(["warn", m]),
    },
    workspace: {
      workspaceFolders: [{ uri: { fsPath: "/repo" } }],
      getConfiguration: () => ({ get: (k) => (k === "executable" ? "devhound" : false) }),
      onDidSaveTextDocument: () => ({ dispose() {} }),
    },
    commands: { registerCommand: (id, fn) => { handlers[id] = fn; return { dispose() {} }; } },
  };
  return { vscode, sets, handlers, status, messages };
}

test("scan command publishes diagnostics from CLI output", async () => {
  const f = fakeVscode();
  const calls = [];
  const execFile = (cmd, args, opts, cb) => {
    calls.push([cmd, args, opts.cwd]);
    cb(Object.assign(new Error("exit 1"), { code: 1 }), JSON.stringify([{ path: "src/a.py", line: 2, column: 1, level: "error", message: "AWS access key ID detected (value hidden).", rule_id: "DH-SEC-002" }]), "");
  };
  activate({ subscriptions: [] }, { vscode: f.vscode, execFile });
  await f.handlers["devhound.scan"]();
  assert.deepStrictEqual(calls[0], ["devhound", ["scan", ".", "--format", "json"], "/repo"]);
  assert.strictEqual(f.sets[0][0], "/repo/src/a.py");
  assert.strictEqual(f.sets[0][1][0].severity, 0);
  assert.strictEqual(f.status.text, "DevHound: 1 issue(s)");
});

test("ENOENT falls back to python3 -m devhound, then reports not installed", async () => {
  const f = fakeVscode();
  const seen = [];
  const execFile = (cmd, args, opts, cb) => { seen.push(cmd); cb(Object.assign(new Error("nf"), { code: "ENOENT" }), "", ""); };
  activate({ subscriptions: [] }, { vscode: f.vscode, execFile });
  await f.handlers["devhound.scan"]();
  assert.deepStrictEqual(seen, ["devhound", "python3"]);
  assert.match(f.messages[0][1], /not found/);
});

test("clean run clears old diagnostics and shows clean", async () => {
  const f = fakeVscode();
  const execFile = (c, a, o, cb) => cb(null, "[]", "");
  activate({ subscriptions: [] }, { vscode: f.vscode, execFile });
  await f.handlers["devhound.scan"]();
  assert.strictEqual(f.sets.length, 0);
  assert.strictEqual(f.status.text, "DevHound: clean");
});
