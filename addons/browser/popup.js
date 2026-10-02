// Reads text from the active tab ONLY when you click a button (activeTab permission), scans it locally.
function render(findings) {
  var out = document.getElementById("out");
  out.textContent = "";
  var p = document.createElement("p");
  if (!findings.length) {
    p.className = "ok";
    p.textContent = "No known secret patterns found. (This is not proof the text is safe.)";
    out.appendChild(p);
    return;
  }
  p.className = "bad";
  p.textContent = findings.length + " possible secret(s) found. Values hidden.";
  out.appendChild(p);
  var ul = document.createElement("ul");
  findings.forEach(function (f) {
    var li = document.createElement("li");
    li.textContent = f.name + " (" + f.ruleId + ") at line " + f.line + ", column " + f.column;  // textContent: no HTML injection
    ul.appendChild(li);
  });
  out.appendChild(ul);
}

async function run(mode) {
  try {
    var tabs = await chrome.tabs.query({ active: true, currentWindow: true });
    var res = await chrome.scripting.executeScript({
      target: { tabId: tabs[0].id },
      func: function (m) { return m === "selection" ? String(window.getSelection()) : document.body.innerText.slice(0, 1000000); },
      args: [mode],
    });
    render(DHScan.scanText((res[0] && res[0].result) || "", DH_RULES));
  } catch (e) {
    document.getElementById("out").textContent = "Can't read this page (browser-internal pages are blocked).";
  }
}

document.getElementById("sel").addEventListener("click", function () { run("selection"); });
document.getElementById("page").addEventListener("click", function () { run("page"); });
