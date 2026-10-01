// Progressive enhancement only. Every piece of content is readable with this
// file blocked: tab panels start stacked with visible labels, and every command
// is selectable by hand. The script layers tabs, copy buttons, and telemetry.
(function () {
  "use strict";

  document.documentElement.classList.add("js");

  // ---- telemetry ----
  var clarityTagKeys = [
    "action",
    "actionLocation",
    "contentId",
    "contentType",
    "destinationType",
    "harnessId",
    "mediaAction",
    "pathId",
    "runtimeId",
    "scenario",
    "view"
  ];

  function currentView() {
    return document.body.getAttribute("data-view") || "unknown";
  }

  function browserFamily() {
    var ua = navigator.userAgent || "";
    if (/Edg\//.test(ua)) return "edge";
    if (/Chrome\//.test(ua)) return "chrome";
    if (/Firefox\//.test(ua)) return "firefox";
    if (/Safari\//.test(ua)) return "safari";
    return "other";
  }

  function osFamily() {
    var ua = navigator.userAgent || "";
    if (/Windows/.test(ua)) return "windows";
    if (/Android/.test(ua)) return "android";
    if (/iPhone|iPad|iPod/.test(ua)) return "ios";
    if (/Mac OS/.test(ua)) return "macos";
    if (/Linux/.test(ua)) return "linux";
    return "other";
  }

  function deviceClass() {
    var ua = navigator.userAgent || "";
    if (/iPad|Tablet/.test(ua)) return "tablet";
    if (/Mobile|Android|iPhone|iPod/.test(ua)) return "mobile";
    return "desktop";
  }

  function localeGroup() {
    var language = (navigator.language || "other").slice(0, 2).toLowerCase();
    return ["de", "en", "fr", "ja"].indexOf(language) >= 0 ? language : "other";
  }

  function referrerCategory() {
    if (!document.referrer) return "direct";
    try {
      var hostname = new URL(document.referrer).hostname.toLowerCase();
      if (hostname === "github.com" || /\.github\.com$/.test(hostname)) return "github";
      if (
        /\.microsoft\.com$/.test(hostname) ||
        hostname === "microsoft.github.io" ||
        /\.microsoft\.github\.io$/.test(hostname)
      ) return "microsoft";
      if (/google\.|bing\.com$|duckduckgo\.com$/.test(hostname)) return "search";
    } catch (error) {
      console.warn("[telemetry] could not classify referrer", error);
    }
    return "other";
  }

  function isLandingPage() {
    if (!document.referrer) return true;
    try {
      return new URL(document.referrer).origin !== location.origin;
    } catch (error) {
      console.warn("[telemetry] could not compare landing referrer", error);
      return true;
    }
  }

  function browserContext() {
    var context = {
      browserFamily: browserFamily(),
      deviceClass: deviceClass(),
      localeGroup: localeGroup(),
      osFamily: osFamily(),
      pagePath: location.pathname,
      referrerCategory: referrerCategory(),
      timeZoneOffsetMinutes: String(new Date().getTimezoneOffset()),
      view: currentView()
    };
    var scenario = document.body.getAttribute("data-scenario");
    if (scenario) context.scenario = scenario;
    return context;
  }

  function eventProperties(el) {
    var props = {};
    Array.prototype.forEach.call(el.attributes, function (attribute) {
      if (attribute.name.indexOf("data-event-") === 0) {
        var key = attribute.name
          .slice(11)
          .replace(/-([a-z])/g, function (_, letter) { return letter.toUpperCase(); });
        props[key] = attribute.value;
      }
    });
    return props;
  }

  function track(name, props, options) {
    var p = Object.assign({}, props || {});
    p.view = p.view || currentView();
    var clarityEvent = options && options.clarityEvent;
    try { console.log("[telemetry]", name, p); } catch (e) {}
    try {
      if (typeof window.clarity === "function") {
        clarityTagKeys.forEach(function (key) {
          if (p[key] !== undefined && p[key] !== null && p[key] !== "") {
            window.clarity("set", key, String(p[key]));
          }
        });
        window.clarity("event", name);
        if (clarityEvent && clarityEvent !== name) {
          window.clarity("event", clarityEvent);
        }
      }
    } catch (error) {
      console.warn("[telemetry] Clarity event failed", error);
    }
    try {
      if (
        window.mssqlAgentSkillsTelemetry &&
        typeof window.mssqlAgentSkillsTelemetry.track === "function"
      ) {
        window.mssqlAgentSkillsTelemetry.track(
          name,
          Object.assign(browserContext(), p),
          (options && options.measurements) || { count: 1 }
        );
      }
    } catch (error) {
      console.warn("[telemetry] 1DS event failed", error);
    }
  }
  window.trackHubEvent = track;
  track("site/action", { action: "pageView", isLanding: isLandingPage() });

  // Declarative events: any element with data-event fires it on click, with
  // optional data-event-* props (data-event-scenario-id becomes scenario_id).
  document.querySelectorAll("[data-event]").forEach(function (el) {
    if (el.hasAttribute("data-copy") || el.hasAttribute("data-hcopy") || el.hasAttribute("data-hprompt")) return;
    el.addEventListener("click", function () {
      track(el.getAttribute("data-event"), eventProperties(el), {
        clarityEvent: el.getAttribute("data-clarity-event")
      });
    });
  });

  // Outbound tracking for links no one annotated by hand.
  document.querySelectorAll('a[href^="http"]').forEach(function (a) {
    if (a.hasAttribute("data-event")) return;
    var toDocs = /learn\.microsoft\.com/.test(a.href);
    var toAzure = /portal\.azure\.com|aka\.ms/.test(a.href);
    if (!toDocs && !toAzure) return;
    a.addEventListener("click", function () {
      track("site/action", {
        action: "outboundClicked",
        destinationId: toDocs ? "microsoft-learn" : "azure-or-short-link",
        destinationType: toDocs ? "docs" : "other"
      });
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

  function copyContentType(text, declared) {
    if (declared) return declared;
    if (/npx skills add|plugin marketplace add|plugin (?:install|add)/.test(text)) {
      return "collection-install";
    }
    return "command";
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
        var props = eventProperties(btn);
        props.actionLocation = props.actionLocation || "prose";
        props.action = props.action || "contentCopied";
        if (props.action !== "copyPrompt") {
          props.contentId = props.contentId || currentView() + "-copy";
          props.contentType = props.contentType || (isPrompt ? "prompt" : copyContentType(text));
        }
        track("site/action", props, {
          clarityEvent: btn.getAttribute("data-clarity-event")
        });
      });
    });
  });

  // Every bare code block in prose gets a copy button.
  document.querySelectorAll(".prose pre, .scenarioProse pre").forEach(function (pre, index) {
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
      copyText(text, btn).then(function (copied) {
        if (!copied) return;
        track("site/action", {
          action: "contentCopied",
          actionLocation: "prose",
          contentId: currentView() + "-prose-" + (index + 1),
          contentType: isPrompt ? "prompt" : copyContentType(text, /npx |plugin /.test(text) ? null : "code"),
        });
      });
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
        track("site/action", { action: "pathSelected", pathId: key });
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
