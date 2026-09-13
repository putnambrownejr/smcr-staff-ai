"use strict";
const byId = (id) => document.getElementById(id);
const labels = { reference: "Reference", template: "Template", prompt_pack: "Prompt pack" };
let offset = 0;
let nextOffset = null;
let searchController = null;
let itemController = null;
let currentItem = null;
let downloadUrl = null;
let activeQuery = "";
let activeCategory = "";

async function getJson(url, signal) {
  const response = await fetch(url, { signal });
  if (!response.ok) throw new Error(`The library returned an error (${response.status}). Please try again.`);
  return response.json();
}

function makeText(tag, text, className) {
  const node = document.createElement(tag);
  node.textContent = text;
  if (className) node.className = className;
  return node;
}

async function search() {
  if (searchController) searchController.abort();
  searchController = new AbortController();
  const controller = searchController;
  byId("status").textContent = "Searching the collection…";
  byId("previous").disabled = true;
  byId("next").disabled = true;
  const params = new URLSearchParams({ q: activeQuery, limit: "8", offset: String(offset) });
  if (activeCategory) params.set("category", activeCategory);
  try {
    const result = await getJson(`/api/catalog?${params}`, controller.signal);
    if (controller !== searchController) return;
    nextOffset = result.next_offset;
    const cards = result.items.map((item) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "result";
      button.dataset.itemId = item.id;
      button.setAttribute("aria-pressed", String(currentItem?.id === item.id));
      button.append(makeText("span", labels[item.category], "category"), makeText("span", item.title, "title"),
        makeText("span", item.summary, "summary"), makeText("span", "Open item →", "open"));
      button.addEventListener("click", () => openItem(item.id));
      return button;
    });
    byId("results").replaceChildren(...cards);
    byId("count").textContent = `${result.total} items`;
    byId("status").textContent = result.total ? "Select an item to read it and see its sources." : "No matches. Try a shorter search or a different category.";
    byId("page-label").textContent = result.total ? `${offset + 1}–${offset + result.items.length} of ${result.total}` : "";
    byId("previous").disabled = offset === 0;
    byId("next").disabled = nextOffset === null;
  } catch (error) {
    if (error.name === "AbortError") return;
    byId("status").textContent = error.message;
    byId("results").replaceChildren();
    byId("page-label").textContent = "";
    byId("count").textContent = "";
  }
}

async function openItem(id) {
  if (itemController) itemController.abort();
  itemController = new AbortController();
  const controller = itemController;
  byId("status").textContent = "Opening item…";
  try {
    const item = await getJson(`/api/items/${encodeURIComponent(id)}`, controller.signal);
    if (controller !== itemController) return;
    currentItem = item;
    byId("item-title").textContent = item.title;
    byId("item-category").textContent = labels[item.category];
    byId("item-body").textContent = item.content;
    byId("item-provenance").textContent = `Source file: ${item.source_file}. Snapshot fingerprint: ${item.source_sha256.slice(0, 12)}. This is not a verification date.`;
    byId("item-sources").replaceChildren(...item.sources.map((source) => {
      const row = document.createElement("li");
      const link = makeText("a", source.title);
      const url = new URL(source.url);
      if (url.protocol !== "https:" || url.username || url.password) return makeText("li", source.title);
      link.href = url.href;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      row.append(link);
      return row;
    }));
    if (downloadUrl) URL.revokeObjectURL(downloadUrl);
    downloadUrl = URL.createObjectURL(new Blob([copyText(item)], { type: "text/markdown;charset=utf-8" }));
    byId("download-item").href = downloadUrl;
    byId("download-item").download = `${item.id}.md`;
    byId("reader-empty").hidden = true;
    byId("reader-content").hidden = false;
    byId("copy-status").textContent = "";
    byId("status").textContent = "Item opened. Confirm the current source before using policy or procedure.";
    document.querySelectorAll(".result").forEach((node) => node.setAttribute("aria-pressed", String(node.dataset.itemId === id)));
    byId("item-title").focus({ preventScroll: true });
    if (window.matchMedia("(max-width: 600px)").matches) byId("reader-content").scrollIntoView({ block: "start" });
  } catch (error) {
    if (error.name !== "AbortError") byId("status").textContent = error.message;
  }
}

function copyText(item) {
  return `${item.content}\n\nSources:\n${item.sources.map((s) => `${s.title}: ${s.url}`).join("\n")}\n\nCurrent status has not been live verified.\n${item.notice}\n`;
}

async function copy(text, statusId) {
  try {
    await navigator.clipboard.writeText(text);
    byId(statusId).textContent = "Copied. Paste it into your preferred AI chat.";
  } catch {
    byId(statusId).textContent = "Clipboard unavailable. Select and copy the text, or download the item.";
  }
}

byId("search-form").addEventListener("submit", (event) => {
  event.preventDefault();
  activeQuery = byId("query").value.trim();
  activeCategory = byId("category").value;
  offset = 0;
  search();
});
byId("category").addEventListener("change", () => byId("search-form").requestSubmit());
byId("previous").addEventListener("click", () => { offset = Math.max(0, offset - 8); search(); });
byId("next").addEventListener("click", () => { if (nextOffset !== null) { offset = nextOffset; search(); } });
byId("copy-item").addEventListener("click", () => { if (currentItem) copy(copyText(currentItem), "copy-status"); });
byId("close-item").addEventListener("click", () => {
  if (itemController) itemController.abort();
  const activeId = currentItem?.id;
  currentItem = null;
  byId("reader-content").hidden = true;
  byId("reader-empty").hidden = false;
  document.querySelectorAll(".result").forEach((node) => {
    node.setAttribute("aria-pressed", "false");
    if (node.dataset.itemId === activeId) node.focus();
  });
});
byId("copy-url").addEventListener("click", () => copy(byId("mcp-url").value, "connection-status"));
getJson("/api/connection").then((connection) => { byId("mcp-url").value = connection.url; }).catch((error) => {
  byId("connection-status").textContent = error.message;
  byId("copy-url").disabled = true;
});
search();
