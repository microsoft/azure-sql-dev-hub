// Progressive enhancement only. Every piece of content is readable with this
// file blocked: tab panels start stacked with visible labels, and every command
// is selectable by hand. The script layers tabs, copy buttons, and telemetry.
(function () {
  "use strict";

  document.documentElement.classList.add("js");

  // ---- telemetry ----
  // Telemetry contract for engineering. One track() fans out to every provider.
  // Providers join the fan-out when their IDs are configured in _config.yml.
  // Event taxonomy:
  //   quickstart_start, agent_start_clicked, install_cmd_copy, copy_command,
  //   copy_prompt, copy_code, gallery_card_open, docs_deep_read, docs_outbound,
  //   azure_outbound, md_fetch, existing_data_clicked, walkthrough_open
  var clarityTagKeys = ["agent_id", "mode", "scenario_id", "source", "video_id"];

  function track(name, props) {
    var p = props || {};
    p.path = location.pathname;
    try { console.log("[telemetry]", name, p); } catch (e) {}
    try {
      if (typeof window.clarity === "function") {
        clarityTagKeys.forEach(function (key) {
          if (p[key] !== undefined && p[key] !== null && p[key] !== "") {
            window.clarity("set", key, String(p[key]));
          }
        });
        window.clarity("event", name);
      }
    } catch (e) {}
    try {
      if (window.appInsights && typeof window.appInsights.trackEvent === "function") {
        window.appInsights.trackEvent({ name: name }, p);
      }
    } catch (e) {}
  }
  window.trackHubEvent = track;

  // Declarative events: any element with data-event fires it on click, with
  // optional data-event-* props (data-event-scenario-id becomes scenario_id).
  document.querySelectorAll("[data-event]").forEach(function (el) {
    if (el.hasAttribute("data-copy") || el.hasAttribute("data-hcopy") || el.hasAttribute("data-hprompt")) return;
    el.addEventListener("click", function () {
      var props = {};
      Array.prototype.forEach.call(el.attributes, function (a) {
        if (a.name.indexOf("data-event-") === 0) {
          props[a.name.slice(11).replace(/-/g, "_")] = a.value;
        }
      });
      ["agent", "scenario", "video"].forEach(function (key) {
        var value = el.getAttribute("data-" + key);
        if (value) props[key + "_id"] = value;
      });
      track(el.getAttribute("data-event"), props);
    });
  });

  // Outbound tracking for links no one annotated by hand.
  document.querySelectorAll('a[href^="http"]').forEach(function (a) {
    if (a.hasAttribute("data-event")) return;
    var toDocs = /learn\.microsoft\.com/.test(a.href);
    var toAzure = /portal\.azure\.com|aka\.ms/.test(a.href);
    if (!toDocs && !toAzure) return;
    a.addEventListener("click", function () {
      track(toDocs ? "docs_outbound" : "azure_outbound", { href: a.href });
    });
  });

  // ---- copy ----
  function flash(btn) {
    var prev = btn.textContent;
    btn.textContent = "Copied";
    btn.classList.add("is-copied");
    setTimeout(function () {
      btn.textContent = prev;
      btn.classList.remove("is-copied");
    }, 1200);
  }

  // A copied command must paste cleanly on every shell. The page shows the
  // readable multi-line form with a trailing backslash, but PowerShell and cmd
  // use different continuation characters, so joining the continuations into
  // one line produces a command that runs verbatim everywhere.
  function normalizeCommand(text) {
    if (!text) return "";
    return text
      .replace(/\\\s*\n\s*/g, " ")
      .replace(/[ \t]+\n/g, "\n")
      .trim();
  }

  function copyText(text, btn) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      return navigator.clipboard.writeText(text).then(function () { flash(btn); return true; }, function () { btn.textContent = "Select text to copy"; return false; });
    } else {
      var ta = document.createElement("textarea");
      ta.value = text; document.body.appendChild(ta); ta.select();
      var copied = false;
      try { copied = document.execCommand("copy"); if (copied) flash(btn); } catch (e) {}
      document.body.removeChild(ta);
      return Promise.resolve(copied);
    }
  }

  function commandEvent(text, declared) {
    if (declared) return declared;
    if (/npx skills add|plugin marketplace add|plugin (?:install|add)/.test(text)) return "install_cmd_copy";
    return "copy_command";
  }

  // Buttons that name their source: data-copy points at the element to copy,
  // data-copy-event names the telemetry event, data-copy-source labels where.
  document.querySelectorAll("[data-copy]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var target = document.querySelector(btn.getAttribute("data-copy"));
      var raw = target ? target.textContent : "";
      var isPrompt = btn.getAttribute("data-copy-kind") === "prompt";
      var text = isPrompt ? raw.trim() : normalizeCommand(raw);
      copyText(text, btn).then(function (copied) { if (!copied) return;
      track(
        btn.getAttribute("data-copy-event") || (isPrompt ? "copy_prompt" : commandEvent(text, null)),
        { source: btn.getAttribute("data-copy-source") || "page" }
      ); });
    });
  });

  // Every bare code block in prose gets a copy button.
  document.querySelectorAll(".prose pre, .scenarioProse pre").forEach(function (pre) {
    if (pre.querySelector(".copyBtn")) return;
    var btn = document.createElement("button");
    btn.className = "copyBtn";
    btn.type = "button";
    btn.setAttribute("aria-label", "Copy code");
    btn.textContent = "Copy";
    btn.addEventListener("click", function () {
      var code = pre.querySelector("code") || pre;
      var text = normalizeCommand(code.innerText);
      var isPrompt = code.classList.contains("language-text");
      copyText(text, btn).then(function (copied) { if (copied) track(isPrompt ? "copy_prompt" : commandEvent(text, /npx |plugin /.test(text) ? null : "copy_code"), { source: "prose" }); });
    });
    pre.appendChild(btn);
  });

  // ---- tabs ----
  // A [data-tabgroup] holds [data-tab] buttons and [data-panel] panels keyed by
  // the same name. Without the script every panel is visible and labeled.
  document.querySelectorAll("[data-tabgroup]").forEach(function (group) {
    var name = group.getAttribute("data-tabgroup");
    var tabs = Array.prototype.slice.call(group.querySelectorAll("[data-tab]"));
    var panels = Array.prototype.slice.call(group.querySelectorAll("[data-panel]"));
    if (tabs.length < 2 || panels.length < 2) return;

    function select(key, opts) {
      tabs.forEach(function (t) {
        var on = t.getAttribute("data-tab") === key;
        t.setAttribute("aria-selected", on ? "true" : "false");
        t.tabIndex = on ? 0 : -1;
        if (on && opts && opts.focus) t.focus();
      });
      panels.forEach(function (p) {
        p.hidden = p.getAttribute("data-panel") !== key;
      });
      var status = group.querySelector("[data-tab-status]");
      if (status) {
        var active = panels.filter(function (p) { return !p.hidden; })[0];
        if (active && active.getAttribute("data-status")) {
          status.textContent = active.getAttribute("data-status");
        }
      }
      if (opts && opts.user && name === "quickstart") {
        track("quickstart_start", { mode: key });
      }
    }

    tabs.forEach(function (tab, i) {
      tab.setAttribute("role", "tab");
      tab.addEventListener("click", function () { select(tab.getAttribute("data-tab"), { user: true }); });
      tab.addEventListener("keydown", function (e) {
        var d = e.key === "ArrowRight" ? 1 : e.key === "ArrowLeft" ? -1 : 0;
        if (!d) return;
        e.preventDefault();
        var next = tabs[(i + d + tabs.length) % tabs.length];
        select(next.getAttribute("data-tab"), { user: true, focus: true });
      });
    });

    // Default to the first tab. Unlike the mockup, the initial render fires no
    // telemetry: quickstart_start means a person chose a path, not a page load.
    select(tabs[0].getAttribute("data-tab"), {});
    group.setAttribute("data-tabs-ready", "true");

    // Buttons elsewhere can jump a group to a mode (the hero secondary CTA).
    document.querySelectorAll("[data-mode-link]").forEach(function (el) {
      el.addEventListener("click", function () {
        if (group.getAttribute("data-tabgroup") === "quickstart") {
          select(el.getAttribute("data-mode-link"), { user: true });
        }
      });
    });
  });
})();
