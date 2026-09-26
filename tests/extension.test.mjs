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
