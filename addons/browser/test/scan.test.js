const test = require("node:test");
const assert = require("node:assert");
const fs = require("fs");
const path = require("path");
const rules = require("../rules.js");
const { scanText } = require("../scan.js");

const cases = JSON.parse(fs.readFileSync(path.join(__dirname, "../../../tests/fixtures/secret_cases.json"), "utf8"));

for (const c of cases) {
  test(`parity: ${c.name}`, () => {
    const got = scanText(c.parts.join(""), rules).map((f) => f.ruleId);
    assert.deepStrictEqual(got, c.expect);
  });
}

test("findings never contain the matched value", () => {
  const secret = "AKIA" + "ABCDEFGHIJKLMNOP";
  const out = JSON.stringify(scanText("k=" + secret, rules));
  assert.ok(!out.includes(secret));
  assert.ok(!out.includes("ABCDEFGH"));
});

test("reports line and column", () => {
  const f = scanText("ok\nk=" + "AKIA" + "ABCDEFGHIJKLMNOP", rules)[0];
  assert.strictEqual(f.line, 2);
  assert.strictEqual(f.column, 3);
});

test("handles CRLF and huge single line without throwing", () => {
  assert.deepStrictEqual(scanText("a\r\nb\r\n", rules), []);
  assert.doesNotThrow(() => scanText("x".repeat(1_000_000), rules));
});
