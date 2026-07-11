export class TrackedActionsController {
  constructor({
    target,
    undoRegion,
    request,
    refresh,
    notify,
    escapeHtml,
    emptyStateHtml,
    canWrite,
    undoWindowMs = 10000,
  }) {
    this.target = target;
    this.undoRegion = undoRegion;
    this.request = request;
    this.refresh = refresh;
    this.notify = notify;
    this.escapeHtml = escapeHtml;
    this.emptyStateHtml = emptyStateHtml;
    this.canWrite = canWrite;
    this.undoWindowMs = undoWindowMs;
    this.items = [];
    this.undoTimers = new Map();
    this.target?.addEventListener("click", (event) => this.handleClick(event));
  }

  render(items) {
    this.items = Array.isArray(items) ? [...items] : [];
    this.renderCurrent();
  }

  renderCurrent() {
    if (!this.target) return;
    if (!this.items.length) {
      this.target.className = "row-stack";
      this.target.innerHTML = this.emptyStateHtml(
        "No tracked POAM items.",
        "Open action items and suspenses appear here once added.",
      );
      return;
    }
    const writable = this.canWrite();
    const rows = this.items.map((item) => this.rowHtml(item, writable)).join("");
    const readOnlyNote = writable
      ? ""
      : '<p class="helper-text">Open a personal workspace to update tracked actions.</p>';
    this.target.className = "row-stack";
    this.target.innerHTML = rows + readOnlyNote;
  }

  rowHtml(item, writable) {
    const title = String(item.title || "Untitled action");
    const actionId = String(item.action_id || "");
    const controls = writable && actionId
      ? [
          '<div class="action-row-controls">',
          '<button type="button" class="secondary small" data-action-complete="',
          this.escapeHtml(actionId),
          '" aria-label="Mark ',
          this.escapeHtml(title),
          ' done">Mark done</button>',
          "</div>",
        ].join("")
      : "";
    return [
      '<article class="data-row" data-action-row="',
      this.escapeHtml(actionId),
      '">',
      '<div class="data-row-head"><span class="strip-label">',
      this.escapeHtml(item.status || "open"),
      "</span><strong>",
      this.escapeHtml(title),
      "</strong></div><p>",
      this.escapeHtml(item.owner ? "Owner: " + item.owner : "Owner not assigned"),
      '</p><p class="meta-inline">',
      this.escapeHtml(
        [
          item.category,
          item.priority,
          item.suspense_date ? "Due " + item.suspense_date : "",
        ].filter(Boolean).join(" | "),
      ),
      "</p><p>",
      this.escapeHtml(item.description || item.notes || "No additional notes yet."),
      "</p>",
      controls,
      "</article>",
    ].join("");
  }

  async handleClick(event) {
    const target = event.target instanceof Element ? event.target : null;
    const button = target?.closest("[data-action-complete]");
    if (!button) return;
    const actionId = button.dataset.actionComplete;
    const index = this.items.findIndex((item) => item.action_id === actionId);
    if (index < 0) return;
    const item = this.items[index];
    const previousStatus = item.status || "open";
    this.items.splice(index, 1);
    this.renderCurrent();
    try {
      await this.request("/actions/" + encodeURIComponent(actionId), {
        method: "PATCH",
        auth: true,
        body: JSON.stringify({ status: "closed" }),
      });
      try {
        await this.refresh();
      } catch (refreshError) {
        console.error("Action completed, but the workspace refresh failed", refreshError);
      }
      // A workspace refresh may complete while the PATCH is in flight and
      // briefly rehydrate the still-open action. The successful write is
      // authoritative, so remove it again before presenting Undo.
      this.items = this.items.filter((candidate) => candidate.action_id !== actionId);
      this.renderCurrent();
      this.addUndoNotice(item, index, previousStatus);
      this.notify("Marked " + item.title + " done.");
    } catch (error) {
      this.items.splice(index, 0, item);
      this.renderCurrent();
      this.notify(error.message || "Could not mark that action done.", true);
      this.focusAction(actionId);
    }
  }

  addUndoNotice(item, index, previousStatus) {
    if (!this.undoRegion) return;
    const notice = document.createElement("div");
    notice.className = "undo-notice";
    notice.dataset.undoActionId = item.action_id;
    const message = document.createElement("span");
    message.textContent = "Marked " + item.title + " done.";
    const undoButton = document.createElement("button");
    undoButton.type = "button";
    undoButton.className = "secondary small";
    undoButton.textContent = "Undo";
    undoButton.setAttribute("aria-label", "Undo completion of " + item.title);
    undoButton.addEventListener("click", () => this.undo(item, index, previousStatus, notice));
    notice.append(message, undoButton);
    this.undoRegion.appendChild(notice);
    const timer = window.setTimeout(() => this.removeUndoNotice(item.action_id, notice), this.undoWindowMs);
    this.undoTimers.set(item.action_id, timer);
    undoButton.focus();
  }

  async undo(item, index, previousStatus, notice) {
    const timer = this.undoTimers.get(item.action_id);
    if (timer) window.clearTimeout(timer);
    try {
      await this.request("/actions/" + encodeURIComponent(item.action_id), {
        method: "PATCH",
        auth: true,
        body: JSON.stringify({ status: previousStatus }),
      });
      this.removeUndoNotice(item.action_id, notice);
      await this.refresh();
      this.notify("Restored " + item.title + ".");
      this.focusAction(item.action_id);
    } catch (error) {
      this.notify(error.message || "Could not restore that action.", true);
      notice.querySelector("button")?.focus();
    }
  }

  removeUndoNotice(actionId, notice) {
    const timer = this.undoTimers.get(actionId);
    if (timer) window.clearTimeout(timer);
    this.undoTimers.delete(actionId);
    notice.remove();
  }

  focusAction(actionId) {
    window.setTimeout(() => {
      this.target?.querySelector('[data-action-complete="' + CSS.escape(actionId) + '"]')?.focus();
    }, 0);
  }
}
