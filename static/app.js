"use strict";

const panel = document.getElementById("main-panel");
const form = document.getElementById("chat-form");
const input = document.getElementById("searchbar");
const examples = document.getElementById("examples");
const clearBtn = document.getElementById("clear-chat");
const helpBtn = document.getElementById("help-btn");
const helpModal = document.getElementById("help-modal");
const helpClose = document.getElementById("help-close");

const GREETING =
  "Hi! I'm the USD Career Assistant. Ask me about resumes, interviews, " +
  "networking, LinkedIn, or using AI in your job search — or tap an example below.";

let busy = false;

// --- helpers --------------------------------------------------------------

/** Escape HTML, then apply minimal markdown: **bold** and line breaks. */
function formatText(text) {
  const escaped = text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
  return escaped
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\n/g, "<br>");
}

/** Append a message bubble. Returns the bubble element. */
function addBubble(role, html) {
  const bubble = document.createElement("div");
  bubble.className = role; // "ai" or "user"
  bubble.setAttribute(
    "aria-label",
    role === "ai" ? "AI text message" : "User text message"
  );
  const p = document.createElement("p");
  p.innerHTML = html;
  bubble.appendChild(p);
  panel.appendChild(bubble);
  panel.scrollTop = panel.scrollHeight;
  return bubble;
}

/** Build the sources / resources footer shown inside an AI bubble. */
function metaHtml(sources, resources) {
  let html = "";
  if (sources && sources.length) {
    html +=
      '<div class="meta"><span class="meta-label">Sources:</span> ' +
      sources.map((s) => escapeAttr(s)).join(", ") +
      "</div>";
  }
  if (resources && resources.length) {
    html +=
      '<div class="meta"><span class="meta-label">You may also find these helpful:</span><br>' +
      resources
        .map(
          (r) =>
            `<a href="${escapeAttr(r.url)}" target="_blank" rel="noopener">${escapeAttr(
              r.name
            )}</a> — ${escapeAttr(r.description)}`
        )
        .join("<br>") +
      "</div>";
  }
  return html;
}

function escapeAttr(s) {
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function addGreeting() {
  addBubble("ai", formatText(GREETING));
}

// --- main ask flow --------------------------------------------------------

async function sendQuestion(question) {
  if (busy || !question.trim()) return;
  busy = true;
  input.value = "";

  addBubble("user", formatText(question));

  // Temporary typing indicator (an AI bubble we replace on response).
  const typing = addBubble(
    "ai",
    '<span class="typing"><span></span><span></span><span></span></span>'
  );

  try {
    const resp = await fetch("/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });
    const data = await resp.json();
    const p = typing.querySelector("p");

    if (!resp.ok) {
      p.innerHTML = formatText("⚠️ " + (data.error || "Something went wrong."));
    } else {
      p.innerHTML = formatText(data.answer);
      const meta = metaHtml(data.sources, data.resources);
      if (meta) typing.insertAdjacentHTML("beforeend", meta);
    }
  } catch (err) {
    typing.querySelector("p").innerHTML = formatText("⚠️ Network error: " + err.message);
  } finally {
    busy = false;
    panel.scrollTop = panel.scrollHeight;
  }
}

// --- events ---------------------------------------------------------------

form.addEventListener("submit", (e) => {
  e.preventDefault();
  sendQuestion(input.value);
});

examples.addEventListener("click", (e) => {
  const chip = e.target.closest(".example-chip");
  if (chip) sendQuestion(chip.textContent.trim());
});

clearBtn.addEventListener("click", () => {
  panel.innerHTML = "";
  addGreeting();
  input.focus();
});

helpBtn.addEventListener("click", () => helpModal.removeAttribute("hidden"));
helpClose.addEventListener("click", () => helpModal.setAttribute("hidden", ""));
helpModal.addEventListener("click", (e) => {
  if (e.target === helpModal) helpModal.setAttribute("hidden", "");
});
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") helpModal.setAttribute("hidden", "");
});

// --- init -----------------------------------------------------------------

addGreeting();
input.focus();
