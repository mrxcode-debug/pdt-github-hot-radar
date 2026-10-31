#!/usr/bin/env python3
"""PDT GitHub radar: official public metadata; never executes untrusted repos."""
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VN = timezone(timedelta(hours=7))
STATE = ROOT / "data/state.json"
REPORT = ROOT / "reports/latest.md"
JSON_REPORT = ROOT / "reports/latest.json"
PENDING = ROOT / "reports/pending_issue.md"

GROUPS = [
    ("AI agents", ["agent", "mcp", "llm", "multimodal"], "Đánh giá hỗ trợ agent, coding và điều phối SOL."),
    ("Automation", ["automation", "workflow", "webhook", "n8n", "integration"], "Thử giảm thao tác thủ công trong PDT OPS/API."),
    ("Web and QA", ["playwright", "testing", "e2e", "browser", "qa", "react", "next.js"], "Đánh giá kiểm thử web, frontend và QA."),
    ("Content and marketing", ["seo", "marketing", "content", "social media", "copywriting"], "Thử hỗ trợ SEO, content hoặc dịch vụ khách."),
    ("Data and documents", ["pdf", "excel", "spreadsheet", "document", "dataset"], "Đánh giá luồng xử lý tài liệu và dữ liệu."),
    ("Media", ["video", "image", "audio", "music", "subtitle", "photo", "talking-head", "digital-human"], "Thử hỗ trợ quy trình sáng tạo nội dung."),
    ("Developer tools", ["cli", "developer", "typescript", "python", "debug"], "Kiểm tra giá trị tăng tốc lập trình."),
]
BLOCKED = ["credential stealer", "phishing kit", "ransomware builder", "crypto drainer",
           "token grabber", "password stealer", "pirated software", "adversarial defense shield", "poison -> exhaust", "reverse-engineering agents"]


def github_search(query):
    params = urllib.parse.urlencode({"q": query, "sort": "stars", "order": "desc", "per_page": 40})
    req = urllib.request.Request("https://api.github.com/search/repositories?" + params, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "PDT-Hot-GitHub-Radar",
        "X-GitHub-Api-Version": "2022-11-28",
        **({"Authorization": "Bearer " + (os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN"))}
           if (os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN")) else {}),
    })
    with urllib.request.urlopen(req, timeout=30) as res:
        return json.load(res).get("items", [])


def categorize(repo):
    body = " ".join([repo.get("name") or "", repo.get("description") or ""]
                    + (repo.get("topics") or [])).lower()
    best = ("General", "Cần đọc README để xác nhận giá trị cho PDT.", 0)
    for category, keywords, purpose in GROUPS:
        matches = sum(word in body for word in keywords)
        if matches > best[2]:
            best = (category, purpose, matches)
    return best


def evaluate(repo, old_stars, now):
    if repo.get("fork") or repo.get("archived") or repo.get("disabled"):
        return None
    url = repo.get("html_url") or ""
    if not re.fullmatch(r"https://github[.]com/[\w.-]+/[\w.-]+", url):
        return None
    desc = (repo.get("description") or "").strip()
    if not desc or any(term in (url + " " + desc).lower() for term in BLOCKED):
        return None
    created = repo.get("created_at") or ""
    try:
        age = max(0, (now - datetime.fromisoformat(created.replace("Z", "+00:00"))).days)
    except ValueError:
        return None
    stars = int(repo.get("stargazers_count") or 0)
    if age > 31 or stars < 40:
        return None
    name = repo["full_name"]
    delta = max(0, stars - int(old_stars[name])) if name in old_stars else None
    category, purpose, hits = categorize(repo)
    license_id = ((repo.get("license") or {}).get("spdx_id") or "UNKNOWN")
    if license_id == "NOASSERTION":
        license_id = "UNKNOWN"
    score = (min(25, 8 + 5 * hits) +
             (22 if stars >= 700 else 18 if stars >= 300 else 12 if stars >= 100 else 5) +
             (18 if age <= 7 else 12 if age <= 14 else 4) +
             (14 if delta is not None and delta >= 80 else
              8 if delta is not None and delta >= 25 else 0) +
             (8 if license_id != "UNKNOWN" else 0))
    return {
        "name": name, "url": url, "description": desc[:220],
        "stars": stars, "delta": delta, "score": score,
        "created": created[:10], "updated": (repo.get("updated_at") or "")[:10],
        "language": repo.get("language") or "UNKNOWN", "license": license_id,
        "category": category, "use_for_pdt": purpose,
        "action": "TEST_SANDBOX_ONLY" if license_id != "UNKNOWN" else "CHECK_LICENSE",
    }


def main():
    now = datetime.now(timezone.utc)
    today = now.astimezone(VN).strftime("%Y-%m-%d")
    old = json.loads(STATE.read_text(encoding="utf-8-sig")) if STATE.exists() else {}
    old_stars = old.get("stars", {})
    since14 = (now - timedelta(days=14)).strftime("%Y-%m-%d")
    since30 = (now - timedelta(days=30)).strftime("%Y-%m-%d")
    queries = [
        f"created:>={since14} stars:>=60 fork:false archived:false",
        f"topic:ai-agents created:>={since30} stars:>=40 fork:false archived:false",
        f"topic:automation created:>={since30} stars:>=40 fork:false archived:false",
        f"topic:developer-tools created:>={since30} stars:>=40 fork:false archived:false",
    ]
    found, errors = {}, []
    for query in queries:
        try:
            for item in github_search(query):
                found[item["full_name"]] = item
        except (urllib.error.URLError, ValueError, KeyError) as exc:
            errors.append(f"{type(exc).__name__}: {query}")
    if not found:
        raise RuntimeError("Không có dữ liệu GitHub Search; không phát báo cáo sai.")
    evaluated = [candidate for repo in found.values()
                 if (candidate := evaluate(repo, old_stars, now)) is not None]
    evaluated.sort(key=lambda item: (item["score"], item["stars"]), reverse=True)
    already = set(old.get("seen", []))
    selected = [r for r in evaluated if r["name"] not in already
                and r["score"] >= 64 and r["license"] != "UNKNOWN" and not r["license"].startswith("AGPL")][:3]
    result = {"schema_version": 1, "updated_at_utc": now.isoformat(timespec="seconds"),
              "day_vietnam": today, "method": "GitHub Search API: recently created repos, sorted by total stars, NOT official Trending",
              "found": len(found), "query_errors": errors,
              "high_signal": selected, "watchlist": evaluated[:12]}
    lines = ["# PDT GitHub Hot Radar — " + today, "",
             "Quét tự động bằng GitHub Actions. Đây là danh sách repo mới nổi qua GitHub Search, "
             "KHÔNG phải bảng GitHub Trending chính thức; stars tổng không đồng nghĩa stars tăng hôm nay.", ""]
    for idx, r in enumerate(selected, 1):
        growth = (f"+{r['delta']} stars từ snapshot trước" if r["delta"] is not None
                  else "chưa có baseline tăng trưởng")
        lines += [f"## {idx}. [{r['name']}]({r['url']}) — {r['category']}", "",
                  f"**Tác dụng (mô tả tác giả):** {r['description']}", "",
                  f"**PDT có thể dùng:** {r['use_for_pdt']}", "",
                  f"**Bằng chứng:** {r['stars']} stars; {growth}; tạo {r['created']}; "
                  f"ngôn ngữ {r['language']}; license {r['license']}; score {r['score']}/100.", "",
                  "**Quyết định:** đọc README và thử sandbox trước; CHƯA kiểm thử, "
                  "CHƯA chứng minh an toàn hoặc phù hợp dùng thương mại.", ""]
    if not selected:
        lines += ["**NO_UPDATE** — Chưa có repo mới vượt ngưỡng và xác minh được license.", ""]
    lines += ["---", f"Đã xem {len(found)} ứng viên; lỗi API: {len(errors)}. "
              "Không clone, không cài, không chạy code lạ, không tiết lộ dữ liệu PDT.", ""]
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    STATE.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    JSON_REPORT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if PENDING.exists():
        PENDING.unlink()
    if selected and old.get("last_issue_date") != today:
        issue = (f"[GitHub Radar] {today}: {len(selected)} repo đáng xem\n\n" +
                 "Đọc báo cáo: https://github.com/mrxcode-debug/pdt-github-hot-radar/blob/main/reports/latest.md\n\n" +
                 "\n".join(f"- {r['name']} — {r['use_for_pdt']} "
                           f"({r['stars']} stars, {r['license']}) {r['url']}"
                           for r in selected) + "\n")
        PENDING.write_text(issue, encoding="utf-8")
        old["last_issue_date"] = today
    old["seen"] = list(dict.fromkeys(old.get("seen", []) + [r["name"] for r in selected]))[-900:]
    old["stars"] = {r["name"]: r["stars"] for r in evaluated[:250]}
    old["updated_at"] = now.isoformat(timespec="seconds")
    old["version"] = 1
    STATE.write_text(json.dumps(old, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"date": today, "found": len(found), "reported": len(selected),
                      "names": [r["name"] for r in selected], "query_errors": errors},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
