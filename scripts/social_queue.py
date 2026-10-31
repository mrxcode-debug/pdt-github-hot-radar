#!/usr/bin/env python3
"""Generate social research briefs, NEVER publish to a social platform."""
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "reports/latest.json"
STATE = ROOT / "data/state.json"
OUTPUT = ROOT / "reports/social_queue.md"
ALLOWED_LICENSES = {"MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "ISC", "MPL-2.0"}
HOOKS = {
    "AI agents": "AI agent moi nay lam duoc gi, va co an toan khong?",
    "Automation": "Workflow nay co thuc su bot thao tac thu cong?",
    "Web and QA": "Cong cu QA moi nay co gi de thu nghiem?",
    "Media": "AI video/hinh anh: tiet kiem thoi gian hay tang chi phi?",
    "Developer tools": "Tool coding nay co giam thoi gian lam that?",
}

def choose(data, state, limit=3):
    seen = set(state.get("social_seen", []))
    candidates = data.get("high_signal", []) + data.get("watchlist", [])
    result = []
    handled = set()
    for repo in candidates:
        name = repo.get("name") or ""
        if not name or name in handled:
            continue
        handled.add(name)
        if name in seen or repo.get("license") not in ALLOWED_LICENSES:
            continue
        if int(repo.get("score", 0)) < 61:
            continue
        if not (repo.get("url", "").startswith("https://github.com/")):
            continue
        result.append(repo)
        if len(result) >= limit:
            break
    return result

def main():
    data = json.loads(SOURCE.read_text(encoding="utf-8-sig"))
    state = json.loads(STATE.read_text(encoding="utf-8-sig"))
    selected = choose(data, state)
    lines = [
        "# PDT AI Radar / social candidate inbox",
        "",
        "Generated from public GitHub metadata at " + datetime.now(timezone.utc).isoformat(),
        "",
        "**DRAFT LEADS ONLY. NOT fact-checked posts. NOT published.**",
        "Source counts/author summaries are not tests, warranties, or proof of commercial use.",
        "A human researcher must review README, security, licence details and primary sources;",
        "then write original Vietnamese page copy and a different group discussion version.",
        "",
    ]
    if not selected:
        lines += ["NO_UPDATE — no unseen candidate met the social screening gates.", ""]
    for idx, repo in enumerate(selected, 1):
        lines += [
            f"## {idx}. {repo['name']}",
            "",
            f"- Original URL: {repo['url']}",
            f"- Declared topic: {repo.get('category', 'Unknown')}",
            f"- Author description: {repo.get('description', 'Unknown')}",
            f"- Stars (total, not daily growth): {repo.get('stars', 'UNKNOWN')}",
            f"- Licence metadata: {repo.get('license', 'UNKNOWN')}",
            f"- Suggested hook idea: {HOOKS.get(repo.get('category'), 'Tool nay co gi dang thu?')}",
            f"- PDT test idea: {repo.get('use_for_pdt', 'Research practical value')}",
            "- BEFORE PUBLISH: re-open source, test claims, screen rights/risks,",
            "  edit hook, add tangible use and limitations, check Page/Group rules, owner approval.",
            "- State: RESEARCH_ONLY — DO NOT AUTO-POST",
            "",
        ]
    OUTPUT.write_text("\n".join(lines), encoding="utf-8")
    state["social_seen"] = list(dict.fromkeys(state.get("social_seen", []) +
                                                 [r["name"] for r in selected]))[-800:]
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"social_candidates": len(selected),
                      "names": [r["name"] for r in selected]}, ensure_ascii=False))

if __name__ == "__main__":
    main()
