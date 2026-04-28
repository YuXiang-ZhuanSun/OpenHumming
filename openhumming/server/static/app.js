const state = {
  sessionId: "",
  showcase: null,
  providerSettings: null,
};

const providerFieldRules = {
  local: [],
  openai: ["model", "api_key", "clear_api_key"],
  openai_compatible: [
    "model",
    "base_url",
    "api_key",
    "reasoning_effort",
    "thinking_enabled",
    "clear_api_key",
  ],
  deepseek: [
    "model",
    "base_url",
    "api_key",
    "reasoning_effort",
    "thinking_enabled",
    "clear_api_key",
  ],
  anthropic: ["model", "api_key", "clear_api_key"],
};

const dom = {
  chatForm: document.querySelector("#chat-form"),
  chatInput: document.querySelector("#chat-input"),
  chatLog: document.querySelector("#chat-log"),
  sessionInput: document.querySelector("#session-id"),
  reviewButton: document.querySelector("#review-button"),
  lastDraft: document.querySelector("#last-draft"),
  lastReview: document.querySelector("#last-review"),
  workspaceState: document.querySelector("#workspace-state"),
  agentMemory: document.querySelector("#agent-memory"),
  userMemory: document.querySelector("#user-memory"),
  publishedSkills: document.querySelector("#published-skills"),
  draftSkills: document.querySelector("#draft-skills"),
  memoryProposals: document.querySelector("#memory-proposals"),
  reviewOutput: document.querySelector("#review-output"),
  showcaseTabs: document.querySelector("#showcase-tabs"),
  showcaseBody: document.querySelector("#showcase-body"),
  template: document.querySelector("#message-template"),
  providerForm: document.querySelector("#provider-form"),
  providerSelect: document.querySelector("#provider-select"),
  providerModel: document.querySelector("#provider-model"),
  providerBaseUrl: document.querySelector("#provider-base-url"),
  providerApiKey: document.querySelector("#provider-api-key"),
  providerReasoningEffort: document.querySelector("#provider-reasoning-effort"),
  providerThinkingEnabled: document.querySelector("#provider-thinking-enabled"),
  providerClearApiKey: document.querySelector("#provider-clear-api-key"),
  providerKeyStatus: document.querySelector("#provider-key-status"),
  providerStatus: document.querySelector("#provider-status"),
  providerActiveBadge: document.querySelector("#provider-active-badge"),
  providerFields: [...document.querySelectorAll("[data-provider-field]")],
};

async function main() {
  hydrateSession();
  bindEvents();
  appendMessage(
    "assistant",
    "OpenHumming local console is ready.\nUse the Provider panel to switch APIs without editing .env.",
    "System"
  );
  await Promise.all([
    refreshWorkspaceState(),
    loadShowcase(),
    loadProviderSettings(),
  ]);
}

function hydrateSession() {
  const saved = window.localStorage.getItem("openhumming-session-id");
  if (saved) {
    state.sessionId = saved;
    dom.sessionInput.value = saved;
  }
}

function bindEvents() {
  dom.chatForm.addEventListener("submit", onSendMessage);
  dom.reviewButton.addEventListener("click", onRunDailyReview);
  dom.sessionInput.addEventListener("change", () => {
    state.sessionId = dom.sessionInput.value.trim();
    persistSession();
  });
  dom.providerForm.addEventListener("submit", onSaveProviderSettings);
  dom.providerSelect.addEventListener("change", onProviderSelectionChanged);
}

function persistSession() {
  if (state.sessionId) {
    window.localStorage.setItem("openhumming-session-id", state.sessionId);
  }
}

async function onSendMessage(event) {
  event.preventDefault();
  const message = dom.chatInput.value.trim();
  if (!message) {
    return;
  }

  appendMessage("user", message, "You");
  dom.chatInput.value = "";

  const payload = { message };
  if (state.sessionId) {
    payload.session_id = state.sessionId;
  }

  try {
    toggleComposer(true);
    const data = await postJson("/chat", payload);
    state.sessionId = data.session_id;
    dom.sessionInput.value = state.sessionId;
    persistSession();
    appendMessage("assistant", formatAssistantReply(data), "OpenHumming");
    renderMemoryProposals(data.memory_proposals || []);
    renderCreatedDraft(data.created_skill_draft);
    await refreshWorkspaceState();
  } catch (error) {
    appendMessage("assistant", `Request failed\n${String(error)}`, "Error");
  } finally {
    toggleComposer(false);
  }
}

async function onRunDailyReview() {
  try {
    dom.reviewButton.disabled = true;
    const data = await postJson("/reviews/daily", {});
    dom.lastReview.textContent = `${data.review_date} / ${data.promoted_skills.length} promoted`;
    renderReviewOutput(data);
    await refreshWorkspaceState();
  } catch (error) {
    renderReviewOutput({
      promoted_skills: [],
      open_questions: [`Daily review failed: ${String(error)}`],
      reviewed_skill_drafts: [],
    });
  } finally {
    dom.reviewButton.disabled = false;
  }
}

async function onSaveProviderSettings(event) {
  event.preventDefault();
  const payload = collectProviderPayload();

  try {
    setProviderStatus("Saving provider settings...");
    const data = await postJson("/settings/provider", payload);
    state.providerSettings = data;
    renderProviderSettings();
    updateWorkspaceStatus();
    appendMessage(
      "assistant",
      `Provider switched to ${data.active_provider}. New chats will use this backend immediately.`,
      "System"
    );
    setProviderStatus(`Active provider: ${describeProvider(data.active_provider)}.`);
  } catch (error) {
    setProviderStatus(`Provider update failed: ${String(error)}`);
  }
}

function collectProviderPayload() {
  const providerId = dom.providerSelect.value;
  const visibleFields = new Set(providerFieldRules[providerId] || []);
  const payload = { active_provider: providerId };

  if (visibleFields.has("model")) {
    payload.model = valueOrNull(dom.providerModel.value);
  }
  if (visibleFields.has("base_url")) {
    payload.base_url = valueOrNull(dom.providerBaseUrl.value);
  }
  if (visibleFields.has("reasoning_effort")) {
    payload.reasoning_effort = valueOrNull(dom.providerReasoningEffort.value);
  }
  if (visibleFields.has("thinking_enabled")) {
    payload.thinking_enabled = dom.providerThinkingEnabled.checked;
  }
  if (visibleFields.has("clear_api_key") && dom.providerClearApiKey.checked) {
    payload.clear_api_key = true;
  }

  const typedKey = valueOrNull(dom.providerApiKey.value);
  if (typedKey) {
    payload.api_key = typedKey;
  }
  return payload;
}

function onProviderSelectionChanged() {
  hydrateProviderForm(dom.providerSelect.value);
}

function toggleComposer(isBusy) {
  const sendButton = document.querySelector("#send-button");
  sendButton.disabled = isBusy;
  dom.reviewButton.disabled = isBusy;
}

function appendMessage(role, content, meta) {
  const node = dom.template.content.firstElementChild.cloneNode(true);
  node.classList.add(role);
  node.querySelector(".message-meta").textContent = meta;
  node.querySelector(".message-content").textContent = content;
  dom.chatLog.appendChild(node);
  dom.chatLog.scrollTop = dom.chatLog.scrollHeight;
}

function formatAssistantReply(data) {
  const lines = [data.response || ""];
  if (data.created_skill_draft) {
    lines.push("", `Created skill draft: ${data.created_skill_draft.name}`);
  }
  return lines.join("\n");
}

function renderMemoryProposals(items) {
  renderList(
    dom.memoryProposals,
    items.map((item) => `${item.target} / ${item.section} / ${item.content}`),
    "No proposals yet"
  );
}

function renderCreatedDraft(draft) {
  if (!draft) {
    return;
  }
  dom.lastDraft.textContent = `${draft.name} / ${draft.status}`;
}

async function refreshWorkspaceState() {
  const [agent, user, skills, drafts] = await Promise.all([
    fetchJson("/memory/agent"),
    fetchJson("/memory/user"),
    fetchJson("/skills"),
    fetchJson("/skills/drafts"),
  ]);

  dom.agentMemory.textContent = agent.content || "";
  dom.userMemory.textContent = user.content || "";
  renderList(
    dom.publishedSkills,
    (skills || []).map((item) => `${item.name} / ${item.status}`),
    "No published skills"
  );
  renderList(
    dom.draftSkills,
    (drafts || []).map((item) => {
      const confidence = item.metadata?.confidence;
      const label =
        typeof confidence === "number" ? confidence.toFixed(2) : String(confidence ?? "n/a");
      return `${item.name} / ${label}`;
    }),
    "No draft skills"
  );
  updateWorkspaceStatus();
}

async function loadProviderSettings() {
  state.providerSettings = await fetchJson("/settings/provider");
  populateProviderOptions();
  renderProviderSettings();
}

function populateProviderOptions() {
  dom.providerSelect.innerHTML = "";
  for (const item of state.providerSettings.available_providers || []) {
    const option = document.createElement("option");
    option.value = item.id;
    option.textContent = `${item.label} / ${item.id}`;
    dom.providerSelect.appendChild(option);
  }
}

function renderProviderSettings() {
  const activeProvider = state.providerSettings.active_provider;
  dom.providerSelect.value = activeProvider;
  hydrateProviderForm(activeProvider);
  updateWorkspaceStatus();
}

function hydrateProviderForm(providerId) {
  const profile = state.providerSettings?.profiles?.[providerId];
  const descriptor = providerDescriptor(providerId);

  dom.providerSelect.value = providerId;
  dom.providerModel.value = profile?.model || "";
  dom.providerBaseUrl.value = profile?.base_url || "";
  dom.providerReasoningEffort.value = profile?.reasoning_effort || "";
  dom.providerThinkingEnabled.checked = Boolean(profile?.thinking_enabled);
  dom.providerApiKey.value = "";
  dom.providerClearApiKey.checked = false;
  dom.providerKeyStatus.textContent = profile?.has_api_key
    ? "API key is configured and hidden."
    : "No API key configured.";
  dom.providerActiveBadge.textContent = describeProvider(providerId);
  setProviderStatus(descriptor?.description || "Provider settings loaded.");
  toggleProviderFields(providerId);
}

function toggleProviderFields(providerId) {
  const visible = new Set(providerFieldRules[providerId] || []);
  for (const node of dom.providerFields) {
    const fieldName = node.dataset.providerField;
    node.hidden = !visible.has(fieldName);
  }
}

function providerDescriptor(providerId) {
  return (state.providerSettings?.available_providers || []).find(
    (item) => item.id === providerId
  );
}

function describeProvider(providerId) {
  const descriptor = providerDescriptor(providerId);
  return descriptor ? descriptor.label : providerId;
}

function setProviderStatus(message) {
  dom.providerStatus.textContent = message;
}

function updateWorkspaceStatus() {
  const activeProvider = state.providerSettings?.active_provider || "local";
  dom.workspaceState.textContent = `Live / ${describeProvider(activeProvider)}`;
}

async function fetchJson(url) {
  const response = await fetch(url);
  const data = await decodeJsonResponse(response);
  if (!response.ok) {
    throw new Error(extractErrorMessage(data));
  }
  return data;
}

async function postJson(url, payload) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await decodeJsonResponse(response);
  if (!response.ok) {
    throw new Error(extractErrorMessage(data));
  }
  return data;
}

async function decodeJsonResponse(response) {
  try {
    return await response.json();
  } catch (error) {
    return {
      detail: `Non-JSON response (${response.status})`,
    };
  }
}

function extractErrorMessage(data) {
  if (typeof data === "string") {
    return data;
  }
  if (data?.detail) {
    return typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail);
  }
  return JSON.stringify(data);
}

function renderList(container, items, emptyText) {
  container.innerHTML = "";
  if (!items.length) {
    const li = document.createElement("li");
    li.className = "empty";
    li.textContent = emptyText;
    container.appendChild(li);
    return;
  }
  for (const item of items) {
    const li = document.createElement("li");
    li.textContent = item;
    container.appendChild(li);
  }
}

function renderReviewOutput(data) {
  const lines = [
    ...(data.promoted_skills || []).map((item) => `Promoted: ${item}`),
    ...(data.open_questions || []),
  ];
  renderList(dom.reviewOutput, lines, "No review output");
}

async function loadShowcase() {
  state.showcase = await fetchJson("/showcase/evolution");
  renderShowcaseTabs();
  renderShowcaseBody(state.showcase.items[0]);
}

function renderShowcaseTabs() {
  dom.showcaseTabs.innerHTML = "";
  state.showcase.items.forEach((item, index) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `tab-button${index === 0 ? " active" : ""}`;
    button.textContent = `${item.label.en} / ${item.label.zh}`;
    button.addEventListener("click", () => {
      [...dom.showcaseTabs.children].forEach((node) => node.classList.remove("active"));
      button.classList.add("active");
      renderShowcaseBody(item);
    });
    dom.showcaseTabs.appendChild(button);
  });
}

function renderShowcaseBody(item) {
  dom.showcaseBody.innerHTML = `
    <div class="showcase-split">
      <article class="showcase-pane">
        <h3>${item.before_title.en} / ${item.before_title.zh}</h3>
        <pre>${escapeHtml(item.before_content)}</pre>
      </article>
      <article class="showcase-pane">
        <h3>${item.after_title.en} / ${item.after_title.zh}</h3>
        <pre>${escapeHtml(item.after_content)}</pre>
      </article>
    </div>
    <ul class="showcase-highlights">
      ${item.highlights
        .map(
          (point) =>
            `<li><strong>${escapeHtml(point.en)}</strong><br />${escapeHtml(point.zh)}</li>`
        )
        .join("")}
    </ul>
  `;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function valueOrNull(value) {
  const normalized = String(value || "").trim();
  return normalized || null;
}

main().catch((error) => {
  appendMessage("assistant", `UI bootstrap failed\n${String(error)}`, "Error");
});
