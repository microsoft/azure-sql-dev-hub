// Progressive enhancement only. Every piece of content on this site is readable
// with this file blocked or failing to load: the tab panels below start life as
// plain stacked headings, and the copy buttons are conveniences layered on top of
// code blocks you can already select by hand.
(function () {
  "use strict";

  // ---- analytics: fan a custom event out to whatever provider loaded ----
  // No-ops until a provider is configured (see _includes/analytics.html).
  function track(name, props) {
    try {
      if (window.appInsights && typeof window.appInsights.trackEvent === "function") {
        window.appInsights.trackEvent({ name: name }, props || {});
      }
    } catch (e) {}
  }

  // ---- copy to clipboard ----
  function flash(btn) {
    var label = btn.querySelector(".copy-label");
    var prev = label ? label.textContent : btn.textContent;
    if (label) { label.textContent = "Copied"; } else { btn.textContent = "Copied"; }
    btn.classList.add("is-copied");
    setTimeout(function () {
      if (label) { label.textContent = prev; } else { btn.textContent = prev; }
      btn.classList.remove("is-copied");
    }, 1600);
  }

  // Make a copied command paste-safe on every shell. The page keeps the readable
  // multi-line form with a trailing backslash, but bash and zsh use "\" for line
  // continuation while PowerShell uses a backtick and cmd uses "^", so a copied
  // multi-line block breaks on Windows. Joining the continuations into one line
  // produces a command that runs verbatim in bash, PowerShell, and cmd.
  function normalizeCommand(text) {
    if (!text) return "";
    return text
      .replace(/\\\s*\n\s*/g, " ")   // join backslash continuations
      .replace(/[ \t]+\n/g, "\n")    // drop trailing whitespace
      .trim();
  }

  function copyText(text, btn) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(function () { flash(btn); }, function () {});
    } else {
      var ta = document.createElement("textarea");
      ta.value = text; document.body.appendChild(ta); ta.select();
      try { document.execCommand("copy"); flash(btn); } catch (e) {}
      document.body.removeChild(ta);
    }
  }

  // Classify what was copied so the event is useful without recording the
  // command text itself.
  function commandKind(text, declared) {
    if (declared) return declared;
    if (/npx skills add|plugin marketplace add|plugin add/.test(text)) return "install";
    if (/docker login/.test(text)) return "registry-login";
    if (/docker run/.test(text)) return "container-start";
    if (/sqlcmd/.test(text)) return "verify";
    return "command";
  }

  // explicit copy controls (the hero command block)
  document.querySelectorAll("[data-copy], [data-copy-text]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var text = btn.getAttribute("data-copy-text");
      if (!text) {
        var target = document.querySelector(btn.getAttribute("data-copy"));
        text = target ? target.innerText : "";
      }
      var normalized = normalizeCommand(text);
      copyText(normalized, btn);
      track("copy_command", {
        kind: commandKind(normalized, btn.getAttribute("data-copy-kind")),
        location: "hero"
      });
    });
  });

  // a copy button on every code block in the prose
  document.querySelectorAll(".prose pre").forEach(function (pre) {
    var btn = document.createElement("button");
    btn.className = "copy-btn";
    btn.type = "button";
    btn.setAttribute("aria-label", "Copy code");
    btn.innerHTML = '<span class="copy-label">Copy</span>';
    btn.addEventListener("click", function () {
      var code = pre.querySelector("code") || pre;
      var normalized = normalizeCommand(code.innerText);
      copyText(normalized, btn);
      var panel = pre.closest(".tab-panel");
      track("copy_command", {
        kind: commandKind(normalized, null),
        location: panel ? panel.getAttribute("data-tab-name") : "prose"
      });
    });
    pre.appendChild(btn);
  });

  // ---- tabs ----
  // An h2 marked .tab-group owns every following sibling until the next h2 or an
  // element marked .tab-end. Within that run, each h3 marked .tab opens a panel.
  function buildTabs(h2) {
    var groups = [];
    var current = null;
    var node = h2.nextElementSibling;

    while (node && node.tagName !== "H2" && !node.classList.contains("tab-end")) {
      var next = node.nextElementSibling;
      if (node.tagName === "H3" && node.classList.contains("tab")) {
        current = { heading: node, nodes: [node] };
        groups.push(current);
      } else if (current) {
        current.nodes.push(node);
      }
      node = next;
    }
    if (groups.length < 2) return;   // one panel is not a tab set

    var list = document.createElement("div");
    list.className = "tablist";
    list.setAttribute("role", "tablist");
    h2.parentNode.insertBefore(list, groups[0].heading);

    var tabs = [];
    var panels = [];

    groups.forEach(function (g, i) {
      var name = g.heading.textContent.trim();
      var slug = (g.heading.id || name.toLowerCase().replace(/[^a-z0-9]+/g, "-")).replace(/^-|-$/g, "");
      var panelId = "panel-" + slug;
      var tabId = "tab-" + slug;

      var panel = document.createElement("div");
      panel.className = "tab-panel";
      panel.id = panelId;
      panel.setAttribute("role", "tabpanel");
      panel.setAttribute("aria-labelledby", tabId);
      panel.setAttribute("data-tab-name", slug);
      panel.hidden = i !== 0;
      g.nodes[0].parentNode.insertBefore(panel, g.nodes[0]);
      g.nodes.forEach(function (n) { panel.appendChild(n); });

      var tab = document.createElement("button");
      tab.type = "button";
      tab.id = tabId;
      tab.textContent = name;
      tab.setAttribute("role", "tab");
      tab.setAttribute("aria-controls", panelId);
      tab.setAttribute("aria-selected", i === 0 ? "true" : "false");
      tab.tabIndex = i === 0 ? 0 : -1;
      list.appendChild(tab);

      tabs.push(tab);
      panels.push(panel);
    });

    function select(i, focus) {
      tabs.forEach(function (t, j) {
        t.setAttribute("aria-selected", j === i ? "true" : "false");
        t.tabIndex = j === i ? 0 : -1;
        panels[j].hidden = j !== i;
      });
      if (focus) tabs[i].focus();
      track("tab_select", { group: h2.id || "", tab: panels[i].getAttribute("data-tab-name") });
    }

    tabs.forEach(function (tab, i) {
      tab.addEventListener("click", function () { select(i, false); });
      tab.addEventListener("keydown", function (e) {
        var delta = e.key === "ArrowRight" ? 1 : e.key === "ArrowLeft" ? -1 : 0;
        if (delta) {
          e.preventDefault();
          select((i + delta + tabs.length) % tabs.length, true);
        } else if (e.key === "Home") {
          e.preventDefault(); select(0, true);
        } else if (e.key === "End") {
          e.preventDefault(); select(tabs.length - 1, true);
        }
      });
    });

    // Deep link: /#start-cloud opens the Cloud tab inside the #start group.
    var hash = location.hash.replace("#", "");
    if (hash.indexOf(h2.id + "-") === 0) {
      var want = hash.slice(h2.id.length + 1);
      panels.forEach(function (p, i) {
        if (p.getAttribute("data-tab-name") === want) select(i, false);
      });
    }
  }

  document.querySelectorAll("h2.tab-group").forEach(buildTabs);
})();
