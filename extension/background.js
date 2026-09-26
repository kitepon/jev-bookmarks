const HOST = "ai.jevbookmarks.history";
const PAGE_SIZE = 5000;
const CANDIDATE_LIMIT = 80;
let port = null;
let retryDelay = 1000;

async function readHistory(startTime = 0, endTime = Date.now() + 1) {
  const entries = await chrome.history.search({
    text: "",
    startTime,
    endTime,
    maxResults: PAGE_SIZE,
  });
  if (entries.length < PAGE_SIZE) return entries;
  if (endTime - startTime < 2) throw new Error("HISTORY_DENSE_WINDOW");
  const middle = Math.floor((startTime + endTime) / 2);
  const [older, newer] = await Promise.all([
    readHistory(startTime, middle),
    readHistory(middle, endTime),
  ]);
  const byUrl = new Map();
  for (const entry of [...older, ...newer]) {
    const previous = byUrl.get(entry.url);
    if (!previous || (entry.lastVisitTime || 0) > (previous.lastVisitTime || 0)) {
      byUrl.set(entry.url, entry);
    }
  }
  return [...byUrl.values()];
}

function terms(goal) {
  const normalized = goal.normalize("NFKC").toLowerCase();
  const segmenter = new Intl.Segmenter("ja", { granularity: "word" });
  const words = [...segmenter.segment(normalized)]
    .filter((part) => part.isWordLike)
    .map((part) => part.segment)
    .filter((part) => part.length >= 2);
  return [...new Set(words)];
}

function candidates(goal, entries) {
  const words = terms(goal);
  const now = Date.now();
  const byPage = new Map();
  for (const entry of entries) {
    if (!entry.url) continue;
    let url;
    try {
      url = new URL(entry.url);
    } catch {
      continue;
    }
    if (url.protocol !== "http:" && url.protocol !== "https:") continue;
    const pageKey = url.origin + url.pathname;
    const previous = byPage.get(pageKey);
    if (previous && (previous.lastVisitTime || 0) >= (entry.lastVisitTime || 0)) continue;
    byPage.set(pageKey, entry);
  }
  const ranked = [...byPage.values()].map((entry) => {
    const url = new URL(entry.url);
    const text = `${entry.title || ""} ${url.hostname} ${url.pathname}`.normalize("NFKC").toLowerCase();
    const matches = words.reduce((total, word) => total + (text.includes(word) ? 1 : 0), 0);
    const ageDays = Math.max(0, (now - (entry.lastVisitTime || 0)) / 86400000);
    const score = matches * 20 + Math.log1p(entry.visitCount || 0) * 2 + 4 / (1 + ageDays / 30);
    return { entry, score };
  });
  ranked.sort((a, b) => b.score - a.score || (b.entry.lastVisitTime || 0) - (a.entry.lastVisitTime || 0));
  return ranked.slice(0, CANDIDATE_LIMIT).map(({ entry }) => ({
    url: entry.url,
    title: entry.title || "",
    visitCount: entry.visitCount || 0,
    lastVisitTime: entry.lastVisitTime || 0,
  }));
}

async function handle(message, nativePort) {
  if (message?.type !== "search" || typeof message.goal !== "string") return;
  try {
    const entries = await readHistory();
    nativePort.postMessage({ id: message.id, candidates: candidates(message.goal, entries) });
  } catch (error) {
    nativePort.postMessage({ id: message.id, error: String(error) });
  }
}

function connect() {
  if (port) return;
  const nativePort = chrome.runtime.connectNative(HOST);
  port = nativePort;
  nativePort.onMessage.addListener((message) => void handle(message, nativePort));
  nativePort.onDisconnect.addListener(() => {
    port = null;
    const delay = retryDelay;
    retryDelay = Math.min(retryDelay * 2, 60000);
    setTimeout(connect, delay);
  });
}

chrome.runtime.onStartup.addListener(connect);
chrome.runtime.onInstalled.addListener(connect);
connect();
