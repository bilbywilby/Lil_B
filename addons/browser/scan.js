// Local secret scan. Mirrors devhound/secrets.py (rules come from the generated rules.js).
// No network, no storage, no logging of matched values: findings carry rule, line and column only.
var DHScan = (function () {
  function entropy(s) {
    if (!s) return 0;
    var counts = {};
    for (var i = 0; i < s.length; i++) counts[s[i]] = (counts[s[i]] || 0) + 1;
    var h = 0;
    for (var k in counts) { var p = counts[k] / s.length; h -= p * Math.log2(p); }
    return h;
  }

  function scanText(text, rules) {
    var findings = [];
    var lines = String(text).split(/\r\n|\r|\n/);
    var compiled = rules.patterns.map(function (p) { return { p: p, rx: new RegExp(p.source, p.flags) }; });
    var generic = new RegExp(rules.generic.source, rules.generic.flags);
    for (var i = 0; i < lines.length; i++) {
      var line = lines[i];
      if (line.indexOf(rules.ignoreMarker) !== -1) continue;
      var hitCols = [];
      compiled.forEach(function (c) {
        var m = c.rx.exec(line);
        if (m) {
          hitCols.push(m.index);
          findings.push({ ruleId: c.p.id, name: c.p.name, line: i + 1, column: m.index + 1 });
        }
      });
      var g = generic.exec(line);
      if (g && hitCols.indexOf(g.index) === -1 && entropy(g[1]) >= rules.generic.minEntropy) {
        findings.push({ ruleId: rules.generic.id, name: rules.generic.name, line: i + 1, column: g.index + 1 });
      }
    }
    return findings;
  }

  return { scanText: scanText, entropy: entropy };
})();
if (typeof module !== "undefined") { module.exports = DHScan; }
