"use strict";
const path = require("path");
const lib = require("./lib");

function realDeps() {
  return { vscode: require("vscode"), execFile: require("child_process").execFile };
}

function run(execFile, candidates, kind, cwd) {
  return new Promise((resolve) => {
    const [cmd, base] = candidates[0];
    execFile(cmd, lib.buildArgs(kind, base), { cwd, maxBuffer: 10 * 1024 * 1024 }, (err, stdout, stderr) => {
      if (err && err.code === "ENOENT" && candidates.length > 1) {
        return resolve(run(execFile, candidates.slice(1), kind, cwd));
      }
      if (err && err.code === "ENOENT") return resolve({ missing: true });
      // devhound exits 1 when it has findings: that is normal, not a failure.
      try {
        resolve({ findings: lib.parseFindings(stdout) });
      } catch (e) {
        resolve({ error: (stderr || String(e)).toString().slice(0, 300) });
      }
    });
  });
}

function activate(context, deps) {
  const { vscode, execFile } = deps || realDeps();
  const collection = vscode.languages.createDiagnosticCollection("devhound");
  const status = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 0);
  status.text = "DevHound";
  status.command = "devhound.scan";
  status.show();
  context.subscriptions.push(collection, status);

  const severity = (l) =>
    l === "error" ? vscode.DiagnosticSeverity.Error : l === "warning" ? vscode.DiagnosticSeverity.Warning : vscode.DiagnosticSeverity.Information;

  async function runKind(kind) {
    const folder = vscode.workspace.workspaceFolders && vscode.workspace.workspaceFolders[0];
    if (!folder) return vscode.window.showWarningMessage("DevHound: open a folder first.");
    const cwd = folder.uri.fsPath;
    const cfg = vscode.workspace.getConfiguration("devhound");
    status.text = "DevHound: running…";
    const res = await run(execFile, lib.commandCandidates(cfg.get("executable")), kind, cwd);
    if (res.missing) {
      status.text = "DevHound: not installed";
      return vscode.window.showErrorMessage("DevHound not found. Install it (`pip install .` in the Lil_B repo) or set devhound.executable.");
    }
    if (res.error) {
      status.text = "DevHound: error";
      return vscode.window.showErrorMessage("DevHound failed: " + res.error);
    }
    collection.clear();
    for (const [file, items] of lib.groupByFile(res.findings)) {
      const diags = items.map((i) => {
        const d = new vscode.Diagnostic(new vscode.Range(i.line, i.col, i.line, 1000), i.message, severity(i.level));
        d.source = "DevHound";
        d.code = i.code;
        return d;
      });
      collection.set(vscode.Uri.file(path.join(cwd, file)), diags);
    }
    const n = res.findings.length;
    status.text = n ? `DevHound: ${n} issue(s)` : "DevHound: clean";
  }

  for (const kind of ["scan", "check", "brand"]) {
    context.subscriptions.push(vscode.commands.registerCommand("devhound." + kind, () => runKind(kind)));
  }
  context.subscriptions.push(
    vscode.commands.registerCommand("devhound.clear", () => { collection.clear(); status.text = "DevHound"; })
  );
  context.subscriptions.push(
    vscode.workspace.onDidSaveTextDocument(() => {
      if (vscode.workspace.getConfiguration("devhound").get("scanOnSave")) runKind("scan");
    })
  );
  return { runKind };
}

function deactivate() {}

module.exports = { activate, deactivate };
