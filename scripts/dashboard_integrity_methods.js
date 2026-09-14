  // Dashboard integrity repair: persisted journal and explicit workspace identity.
  _apiHeaders(extra) {
    const headers = Object.assign({}, extra || {});
    const key = sessionStorage.getItem("smcr_access_key");
    if (key) headers["X-Local-API-Key"] = key;
    return headers;
  }
  toggleBenchAdd(idx) {
    return () => {
      const card = this.state.benchCards[idx];
      if (card.title === "Personal files") { this.triggerFilePicker(idx, -1)(); return; }
      this.setState((s) => ({ benchCards: s.benchCards.map((c, i) => i === idx ? { ...c, addOpen: !c.addOpen, draftName: "", draftMeta: "" } : c) }));
    };
  }
  addBenchItem(idx) {
    return async (event) => {
      event.preventDefault();
      const card = this.state.benchCards[idx];
      const title = (card.draftName || "").trim();
      if (!title) return;
      try {
        const response = await fetch("/product-templates/manual", { method: "POST", headers: this._apiHeaders({ "Content-Type": "application/json" }), body: JSON.stringify({ template_name: title, template_type: "other", description: card.draftMeta || "", reusable_guidance: card.draftMeta ? [card.draftMeta] : [] }) });
        if (!response.ok) throw new Error("save failed");
        this.setState((s) => ({ benchCards: s.benchCards.map((c, i) => i === idx ? { ...c, addOpen: false, draftName: "", draftMeta: "" } : c), documentSaveStatus: "Reference saved in Template library" }));
        this._loadRealWorkspace();
      } catch (err) { window.alert("Could not save the reference. Your entries remain in the form; try Add again."); }
    };
  }
  async onFileSelected(event) {
    const file = event.target.files && event.target.files[0];
    event.target.value = "";
    if (!file) return;
    const form = new FormData();
    form.append("file", file);
    form.append("document_type", "other");
    try {
      const response = await fetch("/context/upload", { method: "POST", headers: this._apiHeaders(), body: form });
      if (!response.ok) throw new Error("upload failed");
      this.setState({ pendingFileTarget: null, benchModal: null, documentSaveStatus: "File saved locally in Personal files" });
      this._loadRealWorkspace();
    } catch (err) { window.alert("Could not save the file. Your original file is unchanged; select it again to retry."); }
  }
  benchAddDraft(cardIdx, itemIdx) {
    return async () => {
      const source = this.state.benchCards[cardIdx].items[itemIdx];
      try {
        const response = await fetch("/product-templates/" + (source.meta === "system" ? "system/" : "") + encodeURIComponent(source.templateId), { headers: this._apiHeaders() });
        if (!response.ok) throw new Error("template load failed");
        const template = await response.json();
        const content = template.sections ? template.sections.map((s) => "## " + s.heading + "\n\n" + s.scaffold).join("\n\n") : (template.reusable_headings || []).map((h) => "## " + h).concat(template.reusable_guidance || []).join("\n\n");
        const id = "pending-" + crypto.randomUUID();
        const doc = { id, title: source.name, templateType: "template", kind: "Staff product", data: { content }, receipts: [], path: "", receiptsFolder: "" };
        this.setState((s) => ({ workflowDocs: [doc, ...s.workflowDocs], workflowEditorId: id, benchModal: null }));
        await this._createPendingDocument("generations", id);
      } catch (err) { window.alert("Could not start the template draft. Try again when the server is available."); }
    };
  }
  async _loadTemplateDetail(templateId) {
    try {
      let response = await fetch("/product-templates/system/" + encodeURIComponent(templateId), { headers: this._apiHeaders() });
      if (response.status === 404) response = await fetch("/product-templates/" + encodeURIComponent(templateId), { headers: this._apiHeaders() });
      if (!response.ok) throw new Error("load failed");
      const detail = await response.json();
      if (!detail.sections) detail.sections = [{ key: "content", heading: detail.template_name, scaffold: (detail.reusable_headings || []).concat(detail.reusable_guidance || []).join("\n\n"), example: detail.example_excerpt || "" }];
      this.setState((s) => s.templateViewer && s.templateViewer.id === templateId ? { templateViewer: { ...s.templateViewer, loading: false, detail } } : null);
    } catch (err) {
      this.setState((s) => s.templateViewer && s.templateViewer.id === templateId ? { templateViewer: { ...s.templateViewer, loading: false, error: "Could not load this template. Check the server and retry." } } : null);
    }
  }
  async onReceiptFileSelected(event) {
    const files = Array.from(event.target.files || []), id = this._pendingReceiptDoc;
    event.target.value = "";
    if (!files.length || !id) return;
    if (this._isPending(id)) { window.alert("Wait for the draft to save, then select receipts again."); return; }
    const key = this.userKey, version = this._modeVersion;
    for (const file of files) {
      const form = new FormData(); form.append("file", file); form.append("document_type", "other");
      try {
        const response = await fetch("/context/upload", { method: "POST", headers: this._apiHeaders(), body: form });
        if (!response.ok) throw new Error("upload failed");
        const item = (await response.json()).item;
        if (key !== this.userKey || version !== this._modeVersion) return;
        this.setState((s) => ({ workflowDocs: s.workflowDocs.map((d) => d.id === id ? { ...d, receiptsFolder: "local_context/files", receipts: [...d.receipts, { id: item.context_id, name: item.filename, path: "local_context/files/" + item.context_id + "-" + item.filename }] } : d) }));
        if (!await this._saveGeneration(id)) return;
      } catch (err) { window.alert("Could not save receipt " + file.name + ". Your original is unchanged; select it again to retry."); return; }
    }
    this._loadRealWorkspace();
  }
  removeReceipt(docId, receiptId) {
    return () => {
      this.setState((s) => ({ workflowDocs: s.workflowDocs.map((d) => d.id === docId ? { ...d, receipts: d.receipts.filter((r) => r.id !== receiptId) } : d) }));
      this._saveGeneration(docId);
    };
  }
  updateActionField(id, field) {
    return (event) => {
      const value = event.target.value;
      this.setState((s) => ({ actions: s.actions.map((a) => a.id === id ? { ...a, [field]: value } : a) }));
      if (this._isPending(id)) return;
      const apiField = field === "due" ? "suspense_date" : field;
      this._writeDocument("/actions/" + encodeURIComponent(id), { [apiField]: field === "due" && (!value || value === "unscheduled") ? null : value });
    };
  }
  updateFeedField(id, field) {
    return (event) => {
      const feed = this.state.feeds.find((f) => f.id === id);
      if (!feed || !feed.isReal) { window.alert("Built-in feed settings are maintained by the app. Add a custom feed for your own source."); return; }
      const value = event.target.value;
      this.setState((s) => ({ feeds: s.feeds.map((f) => f.id === id ? { ...f, [field]: value } : f) }));
      const apiField = field === "meta" ? "category" : field === "trust" ? "trust_level" : field;
      this._writeDocument("/custom-watch-feeds/" + encodeURIComponent(id), { [apiField]: field === "trust" ? this._feedTrustToLevel(value) : value });
    };
  }
  _writeDocument(url, payload, method) {
    const key = this.userKey, version = this._modeVersion;
    const request = { url, payload, method: method || "PATCH", headers: this._apiHeaders({ "Content-Type": "application/json" }) };
    this._failedDocumentWrites = this._failedDocumentWrites || {};
    this._documentWrites = this._documentWrites || {};
    this._failedDocumentWrites[url] = request;
    this._documentDirty = true;
    this.setState({ documentSaveStatus: "Saving document edits…" });
    const save = async () => {
      try {
        const response = await fetch(url, { method: request.method, headers: request.headers, body: JSON.stringify(payload) });
        if (!response.ok) throw new Error("save failed");
        if (this._failedDocumentWrites[url] === request) delete this._failedDocumentWrites[url];
        this._documentDirty = Object.keys(this._failedDocumentWrites).length > 0;
        if (key === this.userKey && version === this._modeVersion) this.setState({ documentSaveStatus: this._documentDirty ? "Document edits still need saving" : "Document edits saved" });
        return true;
      } catch (err) {
        if (key === this.userKey && version === this._modeVersion) this.setState({ documentSaveStatus: "Could not save document edits. Keep this page open and retry." });
        return false;
      }
    };
    this._documentWrites[url] = (this._documentWrites[url] || Promise.resolve()).then(save, save);
    return this._documentWrites[url];
  }
  async retryDocumentSaves() {
    const writes = Object.values(this._failedDocumentWrites || {});
    const pending = [
      ...this.state.workflowDocs.filter((d) => this._isPending(d.id)).map((d) => this._createPendingDocument("generations", d.id)),
      ...this.state.fitreps.filter((d) => this._isPending(d.id)).map((d) => this._createPendingDocument("fitreps", d.id)),
    ];
    if (this._noteDirty) pending.push(this.saveNote()());
    return (await Promise.all([...pending, ...writes.map((r) => this._writeDocument(r.url, r.payload, r.method))])).every(Boolean);
  }
  async _createPendingDocument(category, id) {
    this._pendingCreates = this._pendingCreates || new Set();
    if (this._pendingCreates.has(id)) return false;
    const field = category === "fitreps" ? "fitreps" : "workflowDocs";
    const active = category === "fitreps" ? "activeFitrepId" : "workflowEditorId";
    const doc = this.state[field].find((d) => d.id === id);
    if (!doc) return false;
    const key = this.userKey, version = this._modeVersion;
    this._pendingCreates.add(id);
    this._documentDirty = true;
    try {
      const payload = category === "fitreps" ? this._fitrepPayload(doc) : this._generationPayload(doc);
      const response = await fetch("/user-docs/" + category + "/" + encodeURIComponent(key), { method: "POST", headers: this._apiHeaders({ "Content-Type": "application/json" }), body: JSON.stringify(payload) });
      if (!response.ok) throw new Error("create failed");
      const saved = await response.json();
      if (key !== this.userKey || version !== this._modeVersion) return true;
      this.setState((s) => ({
        [field]: s[field].map((d) => d.id === id ? { ...d, id: saved.id, path: "User Docs/" + (category === "fitreps" ? "FitReps" : "Generations") + "/" + saved.id + ".md" } : d),
        [active]: s[active] === id ? saved.id : s[active],
      }));
      return category === "fitreps" ? await this._saveFitrep(saved.id) : await this._saveGeneration(saved.id);
    } catch (err) {
      if (key === this.userKey && version === this._modeVersion) this.setState({ documentSaveStatus: "Could not create document. Your edits are retained; retry document saves." });
      return false;
    } finally { this._pendingCreates.delete(id); }
  }
  _saveFitrep(id) {
    const record = this.state.fitreps.find((f) => f.id === id);
    if (!record || this._isPending(id)) return Promise.resolve(false);
    return this._writeDocument("/user-docs/fitreps/" + encodeURIComponent(this.userKey) + "/" + encodeURIComponent(id), this._fitrepPayload(record));
  }
  _saveAgentNote(kind, id) {
    const note = (kind === "agent" ? this.state.agentNotes : this.state.skillNotes)[id] || "";
    return this._writeDocument("/agent-notes/" + encodeURIComponent(this.userKey) + "/" + kind + "/" + encodeURIComponent(id), { note }, "PUT");
  }
  newNote() {
    return async () => {
      if (this._noteDirty && !await this.saveNote()()) return;
      const id = "pending-" + crypto.randomUUID();
      this.setState((s) => ({ notes: [{ id, title: "Untitled note", body: "", archived: false }, ...s.notes], activeNoteId: id, draftTitle: "Untitled note", draftBody: "" }));
      this._documentDirty = true;
      this._noteDirty = true;
      this.setState({ documentSaveStatus: "New note is unsaved. Choose Save note to keep it." });
    };
  }
  saveNote() {
    return async () => {
      const id = this.state.activeNoteId;
      if (!id) return false;
      const key = this.userKey, version = this._modeVersion;
      const title = this.state.draftTitle || "Untitled note", body = this.state.draftBody;
      const record = this.state.notes.find((n) => n.id === id);
      const payload = { title, body, fields: { archived: !!(record && record.archived) } };
      const base = "/user-docs/notebook/" + encodeURIComponent(key);
      let savedId = id;
      if (this._isPending(id)) {
        if (this._creatingNote) return false;
        this._creatingNote = true;
        try {
          const response = await fetch(base, { method: "POST", headers: this._apiHeaders({ "Content-Type": "application/json" }), body: JSON.stringify(payload) });
          if (!response.ok) throw new Error("create failed");
          savedId = (await response.json()).id;
        } catch (err) {
          this.setState({ documentSaveStatus: "Could not create note. Your text is retained; choose Save note to retry." });
          return false;
        } finally { this._creatingNote = false; }
      } else if (!await this._writeDocument(base + "/" + encodeURIComponent(id), payload)) return false;
      if (key !== this.userKey || version !== this._modeVersion) return true;
      this.setState((s) => ({ notes: s.notes.map((n) => n.id === id ? { ...n, id: savedId, title, body } : n), activeNoteId: s.activeNoteId === id ? savedId : s.activeNoteId, documentSaveStatus: "Note saved" }));
      this._documentDirty = this.state.draftTitle !== title || this.state.draftBody !== body || Object.keys(this._failedDocumentWrites || {}).length > 0;
      this._noteDirty = this.state.draftTitle !== title || this.state.draftBody !== body;
      return true;
    };
  }
  archiveNote(archived) {
    return async () => {
      if (!await this.saveNote()()) return;
      const id = this.state.activeNoteId;
      if (!await this._writeDocument("/user-docs/notebook/" + encodeURIComponent(this.userKey) + "/" + encodeURIComponent(id), { fields: { archived } })) return;
      this.setState((s) => ({ notes: s.notes.map((n) => n.id === id ? { ...n, archived } : n) }));
      this.setNoteView(this.state.noteView)();
    };
  }
  async _deleteSavedDocument(category, id) {
    if (this._isPending(id)) return true;
    const url = "/user-docs/" + category + "/" + encodeURIComponent(this.userKey) + "/" + encodeURIComponent(id);
    const timers = category === "fitreps" ? this._fitrepSaveTimers : this._generationSaveTimers;
    if (timers) { clearTimeout(timers[id]); delete timers[id]; }
    if (this._documentWrites && this._documentWrites[url]) await this._documentWrites[url];
    try {
      const response = await fetch(url, { method: "DELETE", headers: this._apiHeaders() });
      if (!response.ok) throw new Error("delete failed");
      if (this._failedDocumentWrites) delete this._failedDocumentWrites[url];
      return true;
    } catch (err) { window.alert("Could not delete this document. It remains available; try Delete again."); return false; }
  }
  deleteNote() {
    return async () => {
      const id = this.state.activeNoteId;
      if (!id || !window.confirm("Permanently delete this note?")) return;
      if (!await this._deleteSavedDocument("notebook", id)) return;
      this.setState((s) => ({ notes: s.notes.filter((n) => n.id !== id) }));
      this._noteDirty = false;
      this.setNoteView(this.state.noteView)();
    };
  }
  deleteFitrep() {
    return async () => {
      const id = this.state.activeFitrepId;
      if (!id || !window.confirm("Permanently delete this report?")) return;
      if (!await this._deleteSavedDocument("fitreps", id)) return;
      this.setState((s) => ({ fitreps: s.fitreps.filter((f) => f.id !== id), activeFitrepId: null }));
    };
  }
  deleteWorkflowDoc(id) {
    return async () => {
      if (!window.confirm("Permanently delete this draft?")) return;
      if (!await this._deleteSavedDocument("generations", id)) return;
      this.setState((s) => ({ workflowDocs: s.workflowDocs.filter((d) => d.id !== id), workflowEditorId: s.workflowEditorId === id ? null : s.workflowEditorId }));
    };
  }
  _editorSnapshot() {
    const keys = ["staffLaneNotes", "staffLaneContacts", "staffLaneDoctrineByKey", "staffLaneResourcesByKey", "staffLanePromptsByKey", "gearItems", "promptPacks", "tzSelected", "customTz"];
    return Object.fromEntries(keys.map((key) => [key, this.state[key]]));
  }
  selectNote(id) {
    return async () => {
      if (this._noteDirty && !await this.saveNote()()) return;
      const note = this.state.notes.find((n) => n.id === id);
      this.setState({ activeNoteId: id, draftTitle: note ? note.title : "", draftBody: note ? note.body : "" });
    };
  }
  setNoteView(view) {
    return async () => {
      if (this._noteDirty && !await this.saveNote()()) return;
      const next = this.state.notes.find((n) => !!n.archived === (view === "archived"));
      this.setState({ noteView: view, activeNoteId: next ? next.id : null, draftTitle: next ? next.title : "", draftBody: next ? next.body : "" });
    };
  }
  _installEditorPersistence() {
    this._editorDefaults = JSON.parse(JSON.stringify(this._editorSnapshot()));
    const original = this.setState.bind(this);
    this._editorSetState = original;
    this.setState = (update, callback) => {
      const before = JSON.stringify(this._editorSnapshot());
      const changes = typeof update === "function" ? update(this.state) : update;
      if (!this._editorsLoaded && changes && Object.keys(this._editorDefaults).some((key) => key in changes)) {
        original({ editorSaveStatus: "Workspace editors are unavailable. Retry loading before editing." });
        return;
      }
      original(changes, callback);
      if (this._editorsLoaded && before !== JSON.stringify(this._editorSnapshot())) {
        this._editorDirty = true;
        clearTimeout(this._editorTimer);
        original({ editorSaveStatus: "Unsaved workspace edits" });
        this._editorTimer = setTimeout(() => this._saveEditorState(), 400);
      }
    };
    this._loadEditorState();
  }
  async _loadEditorState() {
    if (!this._editorSetState) return;
    const key = this.userKey;
    const version = this._modeVersion;
    clearTimeout(this._editorTimer);
    this._editorsLoaded = false;
    this._editorDirty = false;
    this._editorSetState({ ...JSON.parse(JSON.stringify(this._editorDefaults)), editorSaveStatus: "Loading workspace editors…" });
    try {
      const response = await fetch("/dashboard/editors/" + encodeURIComponent(key), { headers: this._apiHeaders() });
      if (!response.ok && response.status !== 404) throw new Error("load failed");
      const data = response.ok ? await response.json() : {};
      if (key !== this.userKey || version !== this._modeVersion) return;
      const merged = { ...JSON.parse(JSON.stringify(this._editorDefaults)), ...data };
      for (const field of ["staffLaneNotes", "staffLaneContacts", "staffLaneDoctrineByKey", "staffLaneResourcesByKey", "staffLanePromptsByKey"]) {
        merged[field] = { ...this._editorDefaults[field], ...(data[field] || {}) };
      }
      this._editorSetState({ ...merged, editorSaveStatus: "Workspace editors ready" });
      this._editorsLoaded = true;
    } catch (err) {
      if (key === this.userKey && version === this._modeVersion) this._editorSetState({ editorSaveStatus: "Could not load workspace editors. Reload before editing." });
    }
  }
  _saveEditorState() {
    if (!this._editorsLoaded) return Promise.resolve(false);
    const key = this.userKey, version = this._modeVersion;
    const snapshot = JSON.stringify(this._editorSnapshot());
    this._editorDirty = true;
    this._editorSetState({ editorSaveStatus: "Saving workspace edits…" });
    const save = async () => {
      try {
        const response = await fetch("/dashboard/editors/" + encodeURIComponent(key), { method: "PUT", headers: this._apiHeaders({ "Content-Type": "application/json" }), body: snapshot });
        if (!response.ok) throw new Error("save failed");
        if (key === this.userKey && version === this._modeVersion && snapshot === JSON.stringify(this._editorSnapshot())) {
          this._editorDirty = false;
          this._editorSetState({ editorSaveStatus: "Workspace edits saved" });
        }
        return true;
      } catch (err) {
        if (key === this.userKey && version === this._modeVersion) this._editorSetState({ editorSaveStatus: "Could not save workspace edits. Keep this page open and retry." });
        return false;
      }
    };
    this._editorWrites = (this._editorWrites || Promise.resolve()).then(save, save);
    return this._editorWrites;
  }
  _journalFromHandoff(handoff) {
    if (Array.isArray(handoff.drill_handoffs)) return handoff.drill_handoffs;
    const admin = (handoff.admin_watch_items || []).join("\n");
    const drill = (handoff.recurring_drill_notes || []).join("\n");
    return admin || drill ? [{ id: "legacy-handoff", label: "Saved session handoff", date: (handoff.updated_at || "").slice(0, 10), admin, drill, archived: false }] : [];
  }
  _journalChanged(entries, activeId) {
    this.setState({ handoffs: entries, activeHandoffId: activeId, handoffSaveStatus: "Unsaved changes", handoffDirty: true });
  }
  selectHandoff(id) {
    return () => this.setState({ activeHandoffId: id });
  }
  saveHandoffField(field) {
    return (e) => {
      if (!this.state.handoffLoaded) return;
      const value = e.target.value;
      let entries = this.state.handoffs;
      let id = this.state.activeHandoffId;
      if (!id) {
        id = crypto.randomUUID();
        entries = [{ id, label: "Drill handoff", date: new Date().toISOString().slice(0, 10), admin: "", drill: "", archived: false }, ...entries];
      }
      this._journalChanged(entries.map((h) => h.id === id ? { ...h, [field]: value } : h), id);
    };
  }
  newHandoff() {
    return () => {
      if (!this.state.handoffLoaded) return;
      const id = crypto.randomUUID();
      const date = new Date().toISOString().slice(0, 10);
      this._journalChanged([{ id, label: "Drill handoff " + date, date, admin: "", drill: "", archived: false }, ...this.state.handoffs], id);
      this.setState({ handoffView: "active" });
    };
  }
  archiveHandoff(archived) {
    return () => {
      if (!this.state.activeHandoffId) return;
      const entries = this.state.handoffs.map((h) => h.id === this.state.activeHandoffId ? { ...h, archived } : h);
      const next = entries.find((h) => h.archived === (this.state.handoffView === "archived"));
      this._journalChanged(entries, next ? next.id : null);
      this._persistHandoffJournal();
    };
  }
  deleteHandoff() {
    return () => {
      const selected = this.state.handoffs.find((h) => h.id === this.state.activeHandoffId);
      if (!selected || !window.confirm(`Permanently delete "${selected.label}"? This cannot be undone.`)) return;
      const entries = this.state.handoffs.filter((h) => h.id !== selected.id);
      const next = entries.find((h) => h.archived === (this.state.handoffView === "archived"));
      this._journalChanged(entries, next ? next.id : null);
      this._persistHandoffJournal();
    };
  }
  setHandoffView(view) {
    return () => {
      const next = this.state.handoffs.find((h) => h.archived === (view === "archived"));
      this.setState({ handoffView: view, activeHandoffId: next ? next.id : null });
    };
  }
  _persistHandoffJournal() {
    if (!this.state.handoffLoaded) {
      this.setState({ handoffSaveStatus: "Handoff not loaded. Reload the workspace before saving." });
      return Promise.resolve(false);
    }
    const userKey = this.userKey;
    const version = this._modeVersion;
    const entries = this.state.handoffs.map((h) => ({ ...h, id: String(h.id) }));
    const snapshot = JSON.stringify(entries);
    this.setState({ handoffSaveStatus: "Saving handoff…" });
    const save = async () => {
      try {
        const res = await fetch("/handoffs/" + encodeURIComponent(userKey) + "/journal", {
          method: "PATCH", headers: this._apiHeaders({ "Content-Type": "application/json" }), body: JSON.stringify({ entries }),
        });
        if (!res.ok) throw new Error("save failed: " + res.status);
        const handoff = await res.json();
        if (userKey !== this.userKey || version !== this._modeVersion) return false;
        this._handoffData = handoff;
        const unchanged = JSON.stringify(this.state.handoffs) === snapshot;
        this.setState({ handoffSaveStatus: unchanged ? "Handoff saved" : "Unsaved changes", handoffDirty: !unchanged });
        return true;
      } catch (err) {
        if (userKey === this.userKey && version === this._modeVersion) this.setState({ handoffSaveStatus: "Could not save handoff. Your changes remain here; click Save handoff to retry.", handoffDirty: true });
        return false;
      }
    };
    this._handoffWrites = (this._handoffWrites || Promise.resolve()).then(save, save);
    return this._handoffWrites;
  }
  async _loadRealHandoff() {
    const userKey = this.userKey;
    const version = this._modeVersion;
    try {
      const res = await fetch("/handoffs/" + encodeURIComponent(userKey), { headers: this._apiHeaders() });
      if (res.status !== 404 && !res.ok) throw new Error("handoff fetch failed: " + res.status);
      const handoff = res.status === 404 ? { user_key: userKey } : await res.json();
      if (userKey !== this.userKey || version !== this._modeVersion) return;
      if (!this.state.demoModeManual && this.state.demoMode && !handoff.rank && !handoff.display_name) {
        await this._switchDemoMode(true, { seed: "ifEmpty" });
        return;
      }
      this._handoffData = handoff;
      const entries = this._journalFromHandoff(handoff);
      const first = entries.find((h) => h.archived === (this.state.handoffView === "archived"));
      const rank = handoff.rank || "";
      const name = handoff.display_name || "";
      this.setState({
        profileRank: rank, profileLastName: rank && name.startsWith(rank + " ") ? name.slice(rank.length + 1) : name,
        profileBillet: handoff.billet || "", profileUnit: handoff.unit_id || "",
        demoMode: userKey === "demo-smcr-officer", demoModeManual: true,
        handoffs: entries, activeHandoffId: first ? first.id : null,
        handoffLoaded: true, handoffDirty: false, handoffSaveStatus: "",
      });
    } catch (err) {
      if (userKey === this.userKey && version === this._modeVersion) this.setState({ handoffLoaded: false, handoffSaveStatus: "Could not load handoffs. Reload the workspace to retry." });
    }
  }
  _saveHandoff() {
    // Profile writes share the journal queue and fetch current state to avoid
    // replacing a freshly saved journal with an older profile snapshot.
    const userKey = this.userKey;
    const profile = {
      rank: this.state.profileRank || null,
      display_name: [this.state.profileRank, this.state.profileLastName].filter(Boolean).join(" ") || null,
      billet: this.state.profileBillet || null, unit_id: this.state.profileUnit || null,
    };
    const save = async () => {
      try {
        const url = "/handoffs/" + encodeURIComponent(userKey);
        const previous = await fetch(url, { headers: this._apiHeaders() });
        if (previous.status !== 404 && !previous.ok) throw new Error("profile load failed");
        const base = previous.status === 404 ? { user_key: userKey } : await previous.json();
        const response = await fetch(url, { method: "PUT", headers: this._apiHeaders({ "Content-Type": "application/json" }), body: JSON.stringify({ ...base, ...profile, user_key: userKey }) });
        if (!response.ok) throw new Error("profile save failed");
        const body = await response.json();
        if (userKey === this.userKey) this._handoffData = body.handoff;
      } catch (err) { window.alert("Could not save your profile. Please retry after checking the server and passkey."); }
    };
    this._handoffWrites = (this._handoffWrites || Promise.resolve()).then(save, save);
    return this._handoffWrites;
  }
  async _switchDemoMode(on, opts) {
    await this._flushScheduledDocuments();
    if (this._noteDirty && !await this.saveNote()()) return;
    if (this._documentDirty && !window.confirm("Document edits may be unsaved. Switch workspace anyway?")) return;
    if (this._editorDirty && !await this._saveEditorState()) return;
    this._failedDocumentWrites = {};
    this._documentDirty = false;
    clearTimeout(this._handoffSaveTimer);
    this._modeVersion = (this._modeVersion || 0) + 1;
    const version = this._modeVersion;
    this._realUserKey = this._realUserKey || this._resolveUserKey();
    this.userKey = on ? "demo-smcr-officer" : this._realUserKey;
    this._handoffData = null;
    try { window.localStorage.setItem("smcr_workspace_mode", on ? "demo" : "personal"); } catch (err) {}
    this.setState((s) => ({
      demoMode: on, demoModeManual: true, profileRank: "", profileLastName: "", profileBillet: "", profileUnit: "",
      handoffs: [], activeHandoffId: null, handoffLoaded: false, handoffDirty: false, handoffSaveStatus: "Loading handoffs…",
      actions: [], notes: [], activeNoteId: null, draftTitle: "", draftBody: "", fitreps: [], activeFitrepId: null, workflowDocs: [],
      travelCases: [], activeTravelTripId: null, familyReadinessEvents: [], activeFamilyReadinessId: null,
      familyReadinessOpen: false, workflowEditorId: null, benchModal: null, staffLaneModal: null,
      fitrepImportProposal: null, fitrepAnalyticsWorkspace: { reports: [], rs_profiles: [], goals: [] },
      fitrepAnalytics: { sample_size: 0, relative_value_trend: [], by_reporting_senior: [], trait_trends: {}, data_quality_warnings: [] },
      sourceLibrarySources: [], sourceLibraryResults: [], sourceLibraryPreview: null, sourceLibraryRecheck: null,
      agentNotes: {}, skillNotes: {}, chiefUnit: "", chiefBillet: "", chiefEchelon: "", chiefDrill: "", chiefIntent: "",
      chiefPriorities: "", chiefRhythm: "", chiefWatch: "", chiefBriefingBlock: "", chiefConfigured: false,
      workspaceLoaded: false, workspaceLoadError: null, realMaradmins: [], realAlmars: [], realSourceUpdates: [],
      benchCards: s.benchCards.map((c) => (c.title === "Personal files" || c.title === "Project files") ? { ...c, items: [] } : c),
    }));
    if (on) {
      try {
        const query = opts && opts.seed === "ifEmpty" ? "?only_if_empty=true" : "";
        const response = await fetch("/demo/workspace/seed" + query, { method: "POST", headers: this._apiHeaders() });
        if (!response.ok) throw new Error("demo seed failed");
      } catch (err) {
        if (version === this._modeVersion) this.setState({ workspaceLoadError: "Could not prepare the demo workspace." });
      }
    }
    if (version !== this._modeVersion) return;
    this._loadRealHandoff();
    this._loadRealWorkspace();
    this._loadSourceLibrary();
    this._loadRealLinks();
    this._loadRealProjects(on);
    this._loadRealNotes();
    this._loadRealFitreps();
    this._loadTravelCases();
    this._loadFamilyReadiness();
    this._loadFitrepAnalytics();
    this._loadRealGenerations();
    this._loadRealAgentNotes();
    this._loadRealChiefSetup();
    this._loadRealAutomations();
    this._loadEditorState();
  }
  _overviewIntegrityBindings() {
    const open = this.state.workspaceLoaded ? this.state.actions.filter((a) => !a.done) : [];
    const next = open[0];
    const today = new Date();
    const dateKey = [today.getFullYear(), String(today.getMonth() + 1).padStart(2, "0"), String(today.getDate()).padStart(2, "0")].join("-");
    const future = ((this._handoffData || {}).drill_dates || []).map((d) => d.drill_date).filter((d) => d >= dateKey).sort();
    return {
      nextDrillLabel: future[0] ? "Next drill · " + future[0] : "Next drill · No upcoming date saved",
      readinessHeading: this.state.workspaceLoadError ? "Status unavailable" : !this.state.workspaceLoaded ? "Loading workspace" : "Saved work",
      readinessSummary: this.state.workspaceLoadError ? "Could not load your tasks. Reload the workspace to retry." : !this.state.workspaceLoaded ? "Checking saved tasks…" : open.length ? open.length + " open tracked action(s). This is not an official readiness assessment." : "No open actions are tracked. Add your tasks in Watch; an empty list does not confirm readiness.",
      decisiveAction: next ? next.title : "Review your tasks and next drill handoff.",
      actNowEmpty: this.state.workspaceLoaded && !open.length,
      handoffSaveStatus: this.state.handoffSaveStatus,
      handoffUnavailable: !this.state.handoffLoaded,
      handoffLabel: (this.state.handoffs.find((h) => h.id === this.state.activeHandoffId) || {}).label || "",
      onHandoffLabelChange: this.saveHandoffField("label"),
    };
  }
  _saveGeneration(id) {
    const doc = this.state.workflowDocs.find((item) => item.id === id);
    if (!doc || this._isPending(id)) return Promise.resolve(false);
    const userKey = this.userKey;
    const payload = this._generationPayload(doc);
    return this._writeDocument("/user-docs/generations/" + encodeURIComponent(userKey) + "/" + encodeURIComponent(id), payload);
  }
  async _flushScheduledDocuments() {
    const writes = [];
    for (const [field, save] of [["_fitrepSaveTimers", (id) => this._saveFitrep(id)], ["_generationSaveTimers", (id) => this._saveGeneration(id)], ["_agentNoteSaveTimers", (key) => { const split = key.indexOf(":"); return this._saveAgentNote(key.slice(0, split), key.slice(split + 1)); }]]) {
      for (const [id, timer] of Object.entries(this[field] || {})) { clearTimeout(timer); writes.push(save(id)); }
      this[field] = {};
    }
    await Promise.all(writes);
  }
  moveWorkflowDocToProject(docId) {
    return async () => {
      const folder = this.state.draftMoveTarget[docId];
      if (!folder) return;
      if (this._isPending(docId)) {
        window.alert("This draft is still being created. Wait for it to finish saving, then try again.");
        return;
      }
      const userKey = this.userKey;
      const version = this._modeVersion;
      const doc = this.state.workflowDocs.find((item) => item.id === docId);
      if (!doc) return;
      if (this._generationSaveTimers) clearTimeout(this._generationSaveTimers[docId]);
      if (!await this._saveGeneration(docId)) {
        window.alert("Could not save your latest draft changes. The draft has not been moved; retry when the server is available.");
        return;
      }
      try {
        const response = await fetch("/user-docs/generations/" + encodeURIComponent(userKey) + "/" + encodeURIComponent(docId) + "/save-to-project", {
          method: "POST", headers: this._apiHeaders({ "Content-Type": "application/json" }), body: JSON.stringify({ project: folder }),
        });
        if (!response.ok) throw new Error("project save failed");
        const saved = await response.json();
        if (userKey !== this.userKey || version !== this._modeVersion) return;
        this.setState((s) => ({ workflowDocs: s.workflowDocs.filter((item) => item.id !== docId), workflowEditorId: s.workflowEditorId === docId ? null : s.workflowEditorId, documentSaveStatus: "Saved Markdown and Word files in projects/" + folder + "/products/" + (saved.word_path ? " — " + saved.word_path.split("/").pop() : "") }));
        this._loadRealProjects();
      } catch (err) {
        window.alert("Could not save this draft to the project. It is still in Drafted files.");
      }
    };
  }
  // --- AI page Round table tab. Two honest modes:
  //  * external AI configured  -> live round table behind the approval preview
  //  * no external AI          -> "staff call packet": input + seats' lenses for the
  //                                user's own AI. No template is ever shown as an answer.
  async _loadRoundtableCapability() {
    try {
      const res = await fetch("/agents/roundtable/capability", { headers: this._apiHeaders() });
      if (!res.ok) throw new Error("capability check failed");
      const cap = await res.json();
      this.setState({ roundtableCapability: cap });
    } catch (err) {
      this.setState({ roundtableCapability: { external_available: false, model: null, note: "Could not reach the server to check for an external AI. Packet mode only." } });
    }
  }
  _roundtablePayload(question) {
    return {
      scenario: question,
      preset: this.state.roundtablePreset || "full_staff",
      rounds: Number(this.state.roundtableRounds || 1),
      inference: "auto",
      context: { request_is_training_or_fictional: true, user_key: this.userKey },
    };
  }
  async _buildRoundtablePacket(save) {
    const question = (this.state.roundtableQuestion || "").trim();
    if (!question) { this.setState({ roundtableError: "Type the SITREP, question, or task first." }); return; }
    this.setState({ roundtableBusy: true, roundtableError: "", roundtableResult: null, roundtablePreview: null });
    const payload = {
      scenario: question, preset: this.state.roundtablePreset || "full_staff", kind: "roundtable",
      synthesizer: "chief-of-staff", include_role_notes: this.state.roundtableRoleNotes !== false,
      save: !!save, user_key: this.userKey,
    };
    try {
      const res = await fetch("/agents/roundtable/packet", { method: "POST", headers: this._apiHeaders({ "Content-Type": "application/json" }), body: JSON.stringify(payload) });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error((body && typeof body.detail === "string") ? body.detail : ("Packet build failed (" + res.status + ")"));
      this.setState({ roundtablePacket: body, roundtableBusy: false, roundtablePacketSavedId: body.saved_doc_id || null });
      if (save && body.saved_doc_id && typeof this._loadRealGenerations === "function") this._loadRealGenerations();
    } catch (err) {
      this.setState({ roundtableBusy: false, roundtableError: String((err && err.message) || err) });
    }
  }
  async _runRoundtable() {
    const cap = this.state.roundtableCapability;
    if (!cap || !cap.external_available) { return this._buildRoundtablePacket(false); }
    const question = (this.state.roundtableQuestion || "").trim();
    if (!question) { this.setState({ roundtableError: "Type the SITREP, question, or task first." }); return; }
    this.setState({ roundtableBusy: true, roundtableError: "", roundtableResult: null, roundtablePacket: null, roundtablePreview: null, roundtableApproved: false });
    const payload = this._roundtablePayload(question);
    try {
      const pre = await fetch("/agents/roundtable/external-processing-preview", { method: "POST", headers: this._apiHeaders({ "Content-Type": "application/json" }), body: JSON.stringify(payload) });
      const preview = await pre.json().catch(() => ({}));
      if (!pre.ok) throw new Error((preview && typeof preview.detail === "string") ? preview.detail : ("Preview failed (" + pre.status + ")"));
      if (preview && preview.required) { this.setState({ roundtablePreview: preview, roundtableBusy: false }); return; }
      await this._executeRoundtable(payload);
    } catch (err) {
      this.setState({ roundtableBusy: false, roundtableError: String((err && err.message) || err) });
    }
  }
  async _executeRoundtable(payload) {
    this.setState({ roundtableBusy: true, roundtableError: "" });
    try {
      const res = await fetch("/agents/roundtable", { method: "POST", headers: this._apiHeaders({ "Content-Type": "application/json" }), body: JSON.stringify(payload) });
      const body = await res.json().catch(() => ({}));
      if (res.status === 409) {
        const detail = (body && body.detail) || {};
        this.setState({ roundtablePreview: detail.preview || this.state.roundtablePreview, roundtableApproved: false });
        throw new Error((detail.reason || "Approval is required.") + " Review the refreshed preview and approve again.");
      }
      if (!res.ok) throw new Error((body && typeof body.detail === "string") ? body.detail : ("Round table failed (" + res.status + ")"));
      this.setState({ roundtableResult: body, roundtableBusy: false, roundtablePreview: null, roundtableApproved: false });
    } catch (err) {
      this.setState({ roundtableBusy: false, roundtableError: String((err && err.message) || err) });
    }
  }
  _approveRoundtable() {
    const preview = this.state.roundtablePreview;
    if (!preview || !this.state.roundtableApproved) return;
    const payload = this._roundtablePayload((this.state.roundtableQuestion || "").trim());
    payload.external_processing_approval = {
      disclosure_mode: this.state.roundtableDisclosure || "sanitized",
      approval_digest: preview.approval_digest,
      acknowledged: true,
      acknowledged_finding_categories: preview.finding_categories || [],
    };
    this._executeRoundtable(payload);
  }
  async _runCombo(combo) {
    const question = (this.state.comboQuestion || "").trim();
    if (!question) { window.alert("Describe what you want the chain to work on first (the box above the combos)."); return; }
    this.setState({ comboBusy: combo.title });
    const payload = { scenario: question, agents: combo.chain, kind: "chain", include_role_notes: true, save: false, title: combo.title, user_key: this.userKey };
    try {
      const res = await fetch("/agents/roundtable/packet", { method: "POST", headers: this._apiHeaders({ "Content-Type": "application/json" }), body: JSON.stringify(payload) });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error((body && typeof body.detail === "string") ? body.detail : ("Packet build failed (" + res.status + ")"));
      this.setState({ comboBusy: "", comboResults: { ...(this.state.comboResults || {}), [combo.title]: body.packet_markdown || "" } });
    } catch (err) {
      this.setState({ comboBusy: "" });
      window.alert("Could not build this chain packet: " + String((err && err.message) || err));
    }
  }
  _roundtableVals() {
    const bind = (key) => (e) => this.setState({ [key]: e.target.value });
    if (!this._roundtableCapabilityRequested) { this._roundtableCapabilityRequested = true; this._loadRoundtableCapability(); }
    const cap = this.state.roundtableCapability || null;
    const external = !!(cap && cap.external_available);
    const nameById = {};
    Component.AGENTS_CATALOG.forEach((a) => { nameById[a.id] = a.name; });
    const result = this.state.roundtableResult;
    const lastRound = result && result.rounds && result.rounds.length ? result.rounds[result.rounds.length - 1] : null;
    const entries = lastRound ? lastRound.entries.map((e) => ({
      id: e.agent_id, name: nameById[e.agent_id] || e.agent_id, answer: e.answer || "",
      confidence: e.confidence || "low",
      questions: (e.follow_up_questions || []).map((q) => ({ text: q })),
      hasQuestions: !!(e.follow_up_questions && e.follow_up_questions.length),
    })) : [];
    const warnings = result ? (result.warnings || []).map((w) => ({ text: w })) : [];
    const synthesis = result && result.synthesis ? (result.synthesis.answer || "") : "";
    const transcript = result ? [
      "ROUND TABLE — " + result.scenario, "",
      ...(synthesis ? ["== Chief of Staff synthesis ==", synthesis, ""] : []),
      ...entries.flatMap((e) => ["== " + e.name + " ==", e.answer, ""]),
    ].join("\n") : "";
    const packet = this.state.roundtablePacket || null;
    const preview = this.state.roundtablePreview || null;
    const userMsg = preview && preview.sanitized_preview ? (preview.sanitized_preview.find((m) => m.role === "user") || {}).content : "";
    const findings = preview ? (preview.findings || []).map((f) => ({ text: (f.severity || "").toUpperCase() + " · " + (f.category || "") + " — " + (f.message || "") })) : [];
    const copy = (text, flag) => { navigator.clipboard && navigator.clipboard.writeText(text || ""); this.setState({ [flag]: true }); clearTimeout(this["_" + flag + "Timer"]); this["_" + flag + "Timer"] = setTimeout(() => this.setState({ [flag]: false }), 1500); };
    return {
      roundtableCapabilityKnown: !!cap, roundtableExternal: external, roundtablePacketMode: !!cap && !external,
      roundtableCapabilityNote: cap ? (cap.note || "") : "Checking whether an external AI is configured…",
      roundtableModel: cap && cap.model ? cap.model : "",
      roundtableQuestion: this.state.roundtableQuestion || "", onRoundtableQuestion: bind("roundtableQuestion"),
      roundtablePreset: this.state.roundtablePreset || "full_staff", onRoundtablePreset: bind("roundtablePreset"),
      roundtableRounds: String(this.state.roundtableRounds || 1), onRoundtableRounds: bind("roundtableRounds"),
      roundtableRoleNotes: this.state.roundtableRoleNotes !== false, onRoundtableRoleNotes: (e) => this.setState({ roundtableRoleNotes: !!e.target.checked }),
      roundtableRunLabel: this.state.roundtableBusy
        ? (external ? "Convening the staff…" : "Building packet…")
        : (external ? "Convene with AI (preview first)" : "Build staff call packet"),
      onRoundtableRun: (e) => { if (e) e.preventDefault(); this._runRoundtable(); },
      onRoundtablePacketOnly: () => this._buildRoundtablePacket(false),
      roundtableHasError: !!this.state.roundtableError, roundtableError: this.state.roundtableError || "",
      roundtableHasPacket: !!packet,
      roundtablePacketText: packet ? (packet.packet_markdown || "") : "",
      roundtablePacketSeats: packet ? (packet.participant_names || []).join(" · ") : "",
      roundtablePacketNote: packet ? (packet.note || "") : "",
      roundtablePacketCopyLabel: this.state.roundtablePacketCopied ? "Copied" : "Copy packet",
      onRoundtablePacketCopy: () => copy(packet ? packet.packet_markdown : "", "roundtablePacketCopied"),
      roundtablePacketSaveLabel: this.state.roundtablePacketSavedId ? "Saved to Drafted files (Workflows lane)" : "Save packet to my files",
      roundtablePacketSaved: !!this.state.roundtablePacketSavedId,
      onRoundtablePacketSave: () => this._buildRoundtablePacket(true),
      roundtablePreviewRequired: !!preview,
      roundtablePreviewCalls: preview ? String(preview.expected_call_count || 0) : "0",
      roundtablePreviewModel: preview ? ((preview.model || "") + (preview.provider ? " · " + preview.provider : "")) : "",
      roundtablePreviewUserText: userMsg || "",
      roundtablePreviewFindings: findings, roundtableHasFindings: findings.length > 0,
      roundtableRedactedCount: preview ? String((preview.redacted_fields || []).length) : "0",
      roundtableDisclosure: this.state.roundtableDisclosure || "sanitized", onRoundtableDisclosure: bind("roundtableDisclosure"),
      roundtableApproved: !!this.state.roundtableApproved, onRoundtableApproval: (e) => this.setState({ roundtableApproved: !!e.target.checked }),
      onRoundtableApprove: () => this._approveRoundtable(),
      onRoundtableCancelPreview: () => this.setState({ roundtablePreview: null, roundtableApproved: false }),
      roundtableHasResult: !!result, roundtableEntries: entries, roundtableEntryCount: entries.length,
      roundtableHasSynthesis: !!synthesis, roundtableSynthesis: synthesis,
      roundtableParticipantsLabel: result ? (result.participants || []).map((id) => nameById[id] || id).join(" · ") : "",
      roundtableHasWarnings: warnings.length > 0, roundtableWarnings: warnings, roundtableWarningCount: warnings.length,
      roundtableCopyLabel: this.state.roundtableCopied ? "Copied" : "Copy transcript",
      onRoundtableCopy: () => copy(transcript, "roundtableCopied"),
      comboQuestion: this.state.comboQuestion || "", onComboQuestion: bind("comboQuestion"),
    };
  }
  // --- Automations tab: user-built automations. The app stores them and renders a
  // portable standing-instruction block (like the Chief of Staff block) plus a
  // run packet; the user's own AI executes them. Nothing runs in the app.
  async _loadRealAutomations() {
    const requestKey = this.userKey || this._resolveUserKey();
    const modeVersion = this._modeVersion;
    try {
      if (!this.state.automationTemplates || !this.state.automationTemplates.length) {
        const tRes = await fetch("/automations/templates", { headers: this._apiHeaders() });
        if (tRes.ok) { const templates = await tRes.json(); if (requestKey === this.userKey && modeVersion === this._modeVersion) this.setState({ automationTemplates: templates }); }
      }
      const res = await fetch("/automations/" + encodeURIComponent(requestKey), { headers: this._apiHeaders() });
      if (!res.ok) throw new Error("automations load failed");
      const data = await res.json();
      if (requestKey !== this.userKey || modeVersion !== this._modeVersion) return;
      this.setState({ automations: data.automations || [], automationsLoaded: true });
    } catch (err) {
      if (requestKey !== this.userKey || modeVersion !== this._modeVersion) return;
      this.setState({ automations: [], automationsLoaded: true, autoError: "Could not load your automations from the server." });
    }
  }
  _automationForm() {
    const splitLines = (t) => (t || "").split("\n").map((x) => x.trim()).filter(Boolean);
    const agents = Object.keys(this.state.autoAgents || {}).filter((id) => this.state.autoAgents[id]);
    return {
      name: (this.state.autoName || "").trim(), purpose: this.state.autoPurpose || "", trigger: this.state.autoTrigger || "",
      cadence: this.state.autoCadence || "", agents, steps: splitLines(this.state.autoSteps), inputs_needed: splitLines(this.state.autoInputs),
      output_format: this.state.autoFormat || "Bullet summary with a table of actions", tone: this.state.autoTone || "Direct and professional",
      standing_notes: this.state.autoNotes || "", template_key: this.state.autoTemplate || null,
    };
  }
  _resetAutomationForm() {
    this.setState({ autoEditingId: null, autoName: "", autoPurpose: "", autoTrigger: "", autoCadence: "", autoSteps: "", autoInputs: "", autoFormat: "Bullet summary with a table of actions", autoTone: "Direct and professional", autoNotes: "", autoAgents: {}, autoTemplate: "", autoError: "" });
  }
  _applyAutomationTemplate(key) {
    const t = (this.state.automationTemplates || []).find((item) => item.key === key);
    if (!t) { this.setState({ autoTemplate: key }); return; }
    const agents = {}; (t.agents || []).forEach((id) => { agents[id] = true; });
    this.setState({ autoTemplate: key, autoName: t.name, autoPurpose: t.purpose, autoTrigger: t.trigger, autoCadence: t.cadence, autoSteps: (t.steps || []).join("\n"), autoInputs: (t.inputs_needed || []).join("\n"), autoFormat: t.output_format, autoAgents: agents, autoError: "" });
  }
  _editAutomation(item) {
    const a = item.automation; const agents = {}; (a.agents || []).forEach((id) => { agents[id] = true; });
    this.setState({ autoEditingId: a.id, autoName: a.name, autoPurpose: a.purpose, autoTrigger: a.trigger, autoCadence: a.cadence, autoSteps: (a.steps || []).join("\n"), autoInputs: (a.inputs_needed || []).join("\n"), autoFormat: a.output_format, autoTone: a.tone, autoNotes: a.standing_notes, autoAgents: agents, autoTemplate: a.template_key || "", autoError: "" });
  }
  async _saveAutomation() {
    const form = this._automationForm();
    if (!form.name) { this.setState({ autoError: "Give the automation a name." }); return; }
    if (!form.agents.length) { this.setState({ autoError: "Pick at least one staff seat to consult." }); return; }
    const userKey = this.userKey || this._resolveUserKey();
    const editing = this.state.autoEditingId;
    const url = "/automations/" + encodeURIComponent(userKey) + (editing ? "/" + encodeURIComponent(editing) : "");
    this.setState({ autoSaving: true, autoError: "" });
    try {
      const res = await fetch(url, { method: editing ? "PUT" : "POST", headers: this._apiHeaders({ "Content-Type": "application/json" }), body: JSON.stringify(form) });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error((body && typeof body.detail === "string") ? body.detail : ("Save failed (" + res.status + ")"));
      const others = (this.state.automations || []).filter((item) => item.automation.id !== body.automation.id);
      this.setState({ automations: [...others, body], autoSaving: false, autoSaved: true });
      clearTimeout(this._autoSavedTimer); this._autoSavedTimer = setTimeout(() => this.setState({ autoSaved: false }), 2000);
      this._resetAutomationForm();
    } catch (err) {
      this.setState({ autoSaving: false, autoError: String((err && err.message) || err) });
    }
  }
  async _deleteAutomation(item) {
    if (!window.confirm('Delete the "' + item.automation.name + '" automation?')) return;
    const userKey = this.userKey || this._resolveUserKey();
    try {
      const res = await fetch("/automations/" + encodeURIComponent(userKey) + "/" + encodeURIComponent(item.automation.id), { method: "DELETE", headers: this._apiHeaders() });
      if (!res.ok && res.status !== 404) throw new Error("delete failed");
      this.setState({ automations: (this.state.automations || []).filter((x) => x.automation.id !== item.automation.id) });
      if (this.state.autoEditingId === item.automation.id) this._resetAutomationForm();
    } catch (err) { window.alert("Could not delete this automation."); }
  }
  async _buildAutomationPacket(item, save) {
    const id = item.automation.id;
    const input = ((this.state.autoRunInput || {})[id] || "").trim();
    if (!input) { window.alert("Paste this run's input first (the box under the automation)."); return; }
    const userKey = this.userKey || this._resolveUserKey();
    this.setState({ autoBusy: id });
    try {
      const res = await fetch("/automations/" + encodeURIComponent(userKey) + "/" + encodeURIComponent(id) + "/packet", { method: "POST", headers: this._apiHeaders({ "Content-Type": "application/json" }), body: JSON.stringify({ input, save: !!save, include_role_notes: true }) });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error((body && typeof body.detail === "string") ? body.detail : ("Packet build failed (" + res.status + ")"));
      this.setState({ autoBusy: "", autoRunResult: { ...(this.state.autoRunResult || {}), [id]: body } });
      if (save && body.saved_doc_id && typeof this._loadRealGenerations === "function") this._loadRealGenerations();
    } catch (err) {
      this.setState({ autoBusy: "" });
      window.alert("Could not build the run packet: " + String((err && err.message) || err));
    }
  }
  _automationVals() {
    const bind = (key) => (e) => this.setState({ [key]: e.target.value });
    if (!this._automationsRequestedFor || this._automationsRequestedFor !== this.userKey) { this._automationsRequestedFor = this.userKey; this._loadRealAutomations(); }
    const catalog = Component.AGENTS_CATALOG || [];
    const picked = this.state.autoAgents || {};
    const seatOptions = catalog.map((a) => ({
      id: a.id, name: a.name, category: a.category || "", checked: !!picked[a.id],
      onToggle: (e) => { const next = { ...(this.state.autoAgents || {}) }; if (e.target.checked) next[a.id] = true; else delete next[a.id]; this.setState({ autoAgents: next }); },
    }));
    const templates = (this.state.automationTemplates || []).map((t) => ({ value: t.key, label: t.name + " — " + t.trigger }));
    const runInput = this.state.autoRunInput || {};
    const runResult = this.state.autoRunResult || {};
    const automationsRendered = (this.state.automations || []).map((item) => {
      const a = item.automation; const result = runResult[a.id] || null;
      return {
        id: a.id, name: a.name, purpose: a.purpose || "", trigger: a.trigger || "", cadence: a.cadence || "",
        when: [a.trigger, a.cadence].filter(Boolean).join(" · ") || "On demand",
        seats: (item.agent_names || []).join(" · "), block: item.block || "",
        stepCount: (a.steps || []).length, hasPurpose: !!a.purpose,
        onEdit: () => this._editAutomation(item), onDelete: () => this._deleteAutomation(item),
        copyLabel: this.state.autoCopiedId === a.id ? "Copied" : "Copy block",
        onCopy: () => { navigator.clipboard && navigator.clipboard.writeText(item.block || ""); this.setState({ autoCopiedId: a.id }); clearTimeout(this._autoCopyTimer); this._autoCopyTimer = setTimeout(() => this.setState({ autoCopiedId: null }), 1500); },
        runInput: runInput[a.id] || "",
        onRunInput: (e) => { const v = e.target.value; this.setState({ autoRunInput: { ...(this.state.autoRunInput || {}), [a.id]: v } }); },
        runLabel: this.state.autoBusy === a.id ? "Building…" : "Build run packet",
        onRun: () => this._buildAutomationPacket(item, false),
        onRunSave: () => this._buildAutomationPacket(item, true),
        hasResult: !!result, resultPacket: result ? (result.packet_markdown || "") : "",
        resultSaved: !!(result && result.saved_doc_id),
        resultCopyLabel: this.state.autoResultCopiedId === a.id ? "Copied" : "Copy run packet",
        onResultCopy: () => { navigator.clipboard && navigator.clipboard.writeText(result ? result.packet_markdown : ""); this.setState({ autoResultCopiedId: a.id }); clearTimeout(this._autoResultCopyTimer); this._autoResultCopyTimer = setTimeout(() => this.setState({ autoResultCopiedId: null }), 1500); },
      };
    });
    return {
      automationsRendered, hasAutomations: automationsRendered.length > 0, automationsLoaded: !!this.state.automationsLoaded,
      automationTemplateOptions: templates, autoTemplate: this.state.autoTemplate || "",
      onAutoTemplate: (e) => this._applyAutomationTemplate(e.target.value),
      autoName: this.state.autoName || "", onAutoName: bind("autoName"),
      autoPurpose: this.state.autoPurpose || "", onAutoPurpose: bind("autoPurpose"),
      autoTrigger: this.state.autoTrigger || "", onAutoTrigger: bind("autoTrigger"),
      autoCadence: this.state.autoCadence || "", onAutoCadence: bind("autoCadence"),
      autoSteps: this.state.autoSteps || "", onAutoSteps: bind("autoSteps"),
      autoInputs: this.state.autoInputs || "", onAutoInputs: bind("autoInputs"),
      autoFormat: this.state.autoFormat || "Bullet summary with a table of actions", onAutoFormat: bind("autoFormat"),
      autoTone: this.state.autoTone || "Direct and professional", onAutoTone: bind("autoTone"),
      autoNotes: this.state.autoNotes || "", onAutoNotes: bind("autoNotes"),
      autoSeatOptions: seatOptions,
      autoEditing: !!this.state.autoEditingId,
      autoFormTitle: this.state.autoEditingId ? "Edit automation" : "Build a new automation",
      autoSaveLabel: this.state.autoSaving ? "Saving…" : (this.state.autoSaved ? "Saved ✓" : (this.state.autoEditingId ? "Save changes" : "Save automation")),
      onAutoSave: (e) => { if (e) e.preventDefault(); this._saveAutomation(); },
      onAutoCancel: () => this._resetAutomationForm(),
      autoHasError: !!this.state.autoError, autoError: this.state.autoError || "",
    };
  }
