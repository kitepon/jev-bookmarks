import os
import re
from urllib.parse import urlsplit

import httpx


class TypeSafeError(RuntimeError):
    pass


def _evaluate(state: dict, questions: dict) -> dict:
    key = os.environ.get("TYPESAFE_API_KEY")
    if not key:
        raise TypeSafeError("TYPESAFE_API_KEY がありません")
    try:
        response = httpx.post(
            "https://api.typesafe.ai/v1/systemone",
            headers={"Authorization": f"Bearer {key}"},
            json={"model": "jev-latest", "state": state, "questions": questions},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()["answers"]
    except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
        raise TypeSafeError(f"TypeSafeの判定に失敗しました: {exc}") from exc


def _display_url(url: str) -> str:
    parsed = urlsplit(url)
    return f"{parsed.netloc}{parsed.path or '/'}"[:180]


ENTRY_INSTRUCTIONS = (
    "ブラウザ操作エージェントがこのページから操作を始めて、目的を果たせるページまで数回のクリックでたどり着けるかで選ぶ。"
    "目的のページそのものが候補にあればそれを選ぶ。"
    "無くても、同じサイトやサービスの入口（トップ、ドキュメントの目次や導入ページ、ダッシュボード）があればそれを選ぶ。"
    "目的と関係するサイトやサービスの候補が一つも無い時だけnoneを選ぶ。"
)


def choose(goal: str, candidates: list[dict]) -> dict | None:
    if not candidates:
        return None
    if len(candidates) > 80:
        raise ValueError("Jevへ渡す候補は80件以下にしてください")
    criteria = {
        f"c{index}": f"{candidate.get('title') or '無題'} | {_display_url(candidate['url'])}"
        for index, candidate in enumerate(candidates)
    }
    criteria["none"] = "どの候補も、目的と関係するサイトやサービスのページではない"
    # 入口は目的のページそのものでなくてよい。そこから上流の操作でたどれれば足りる。
    answers = _evaluate(
        {"goal": goal},
        {
            "page": {
                "type": "choice",
                "instructions": ENTRY_INSTRUCTIONS,
                "criteria": criteria,
            }
        },
    )
    try:
        selected = answers["page"]["choice"]
        if selected == "none":
            return None
        index = int(selected.removeprefix("c"))
        if selected != f"c{index}" or not 0 <= index < len(candidates):
            raise ValueError("候補IDが不正です")
        return candidates[index]
    except (KeyError, TypeError, ValueError) as exc:
        raise TypeSafeError("TypeSafeが候補外のURLを選びました") from exc


def usefulness(goal: str, page: dict) -> tuple[bool, float]:
    visible = page.get("text", "")
    visible = re.sub(r"[\w.+-]+@[\w.-]+", "[メール]", visible)
    visible = re.sub(r"(?<!\w)\d[\d,\.\s]{3,}\d(?!\w)", "[数値]", visible)
    visible = visible[:1800]
    answers = _evaluate(
        {
            "goal": goal,
            "page": {
                "url": _display_url(page["url"]),
                "title": page.get("title", ""),
                "visible_text": visible,
            },
        },
        {
            "useful": {
                "type": "noul",
                "instructions": "現在のページは、ユーザーの目的を進めるために役立つページですか。",
                "criteria": {
                    "true": "表示された内容や操作先が目的に直接役立つ",
                    "false": "目的と無関係、エラー、ログイン待ち、または使える内容が見えない",
                },
            }
        },
    )
    try:
        probability = float(answers["useful"]["noul"])
        if not 0 <= probability <= 1:
            raise ValueError("確率が範囲外です")
    except (KeyError, TypeError, ValueError) as exc:
        raise TypeSafeError("TypeSafeの有用性判定が不正です") from exc
    return probability >= 0.75, probability
