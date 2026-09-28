from urllib.parse import urlparse

from . import history_bridge, phonebook, typesafe


class BrowserUseError(RuntimeError):
    pass


def _agent(url: str, goal: str):
    from jev_ultrafast import Agent

    return Agent(url, goal)


def _phonebook_candidates(goal: str) -> list[dict]:
    records = phonebook.read()
    needle = goal.casefold()
    records.sort(
        key=lambda item: (
            item["goal"].casefold() == needle,
            needle in item["goal"].casefold() or item["goal"].casefold() in needle,
            item.get("useful_at", ""),
        ),
        reverse=True,
    )
    return records[:80]


def _page_result(page: dict) -> dict:
    return {
        "url": page["url"],
        "title": page.get("title", ""),
        "visible_text": page.get("text", "")[:3000],
    }


def run(goal: str) -> dict:
    goal = goal.strip()
    if not goal:
        raise ValueError("目的を入力してください")

    source = "phonebook"
    selected = typesafe.choose(goal, _phonebook_candidates(goal))
    if selected is None:
        source = "history"
        selected = typesafe.choose(goal, history_bridge.search(goal))
    if selected is None:
        return {"status": "no_entry", "goal": goal, "saved": False}

    try:
        with _agent(selected["url"], goal) as agent:
            final_state = agent.snapshot()
            for final_state in agent.run():
                pass
            page = agent.browser.observe(screenshot=False)
    except Exception as exc:
        raise BrowserUseError(f"ブラウザ操作に失敗しました: {exc}") from exc

    useful, probability = typesafe.usefulness(goal, page)
    if useful:
        parsed = urlparse(page["url"])
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise phonebook.PhonebookError("観測ページのURLを電話帳へ保存できません")
        phonebook.remember(goal, page["url"], page.get("title", ""))
    return {
        "status": "completed",
        "goal": goal,
        "source": source,
        "selected_url": selected["url"],
        "page": _page_result(page),
        "operation_status": final_state["status"],
        "actions": len(final_state["history"]),
        "useful": useful,
        "usefulness_probability": probability,
        "saved": useful,
    }
