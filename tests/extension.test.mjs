import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import vm from "node:vm";

const source = readFileSync(new URL("../extension/background.js", import.meta.url), "utf8");

function extension(history) {
  const port = {
    onMessage: { addListener() {} },
    onDisconnect: { addListener() {} },
  };
  const chrome = {
    runtime: {
      connectNative() { return port; },
      onStartup: { addListener() {} },
      onInstalled: { addListener() {} },
    },
    history: { search: history },
  };
  const context = vm.createContext({ chrome, Intl, URL, Date, Math, Map, Set, Promise, setTimeout });
  vm.runInContext(source, context);
  return context;
}

test("目的語に合う履歴URLを上位候補にし、クエリ違いをまとめる", () => {
  const context = extension(async () => []);
  const entries = [
    { url: "https://other.example/news", title: "ニュース", visitCount: 10, lastVisitTime: Date.now() },
    { url: "https://money.example/accounts?view=1", title: "登録済み口座一覧", visitCount: 2, lastVisitTime: Date.now() },
    { url: "https://money.example/accounts?view=2", title: "登録済み口座一覧", visitCount: 2, lastVisitTime: Date.now() - 1000 },
  ];
  const result = context.candidates("登録済み口座一覧を開く", entries);
  assert.equal(result[0].url, "https://money.example/accounts?view=1");
  assert.equal(result.filter((item) => item.url.includes("/accounts")).length, 1);
});

test("履歴検索で期間と件数を明示する", async () => {
  let query;
  const context = extension(async (value) => { query = value; return []; });
  await context.readHistory();
  assert.equal(query.startTime, 0);
  assert.equal(query.maxResults, 5000);
});

test("1万件超の履歴を分割取得し、古い一致ページも80候補へ残す", async () => {
  const now = Date.now();
  const entries = Array.from({ length: 10050 }, (_, index) => ({
    url: `https://example.com/page-${index}`,
    title: index === 10049 ? "特別な口座" : "一般ページ",
    visitCount: 1,
    lastVisitTime: now - index * 1000,
  }));
  let calls = 0;
  const context = extension(async ({ startTime, endTime, maxResults }) => {
    calls += 1;
    return entries
      .filter((entry) => entry.lastVisitTime >= startTime && entry.lastVisitTime < endTime)
      .slice(0, maxResults);
  });
  const history = await context.readHistory();
  const ranked = context.candidates("特別な口座", history);
  assert.equal(history.length, 10050);
  assert.ok(calls > 3);
  assert.equal(ranked.length, 80);
  assert.equal(ranked[0].url, "https://example.com/page-10049");
});
