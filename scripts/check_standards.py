#!/usr/bin/env python3
"""
Monitor ai-act-standards.com for changes in EU AI Act harmonised standards.
Compares current state with previously saved snapshot and outputs a diff report.
"""

import json
import re
import sys
import hashlib
from datetime import datetime, timezone
from pathlib import Path

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("Installing dependencies...")
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "requests", "beautifulsoup4"], check=True)
    import requests
    from bs4 import BeautifulSoup

URL = "https://ai-act-standards.com/"
SNAPSHOT_FILE = Path("snapshots/standards_snapshot.json")


def fetch_page():
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }
    resp = requests.get(URL, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.text


def parse_standards(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    data = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "stage_counts": {},
        "changelog": [],
        "page_hash": hashlib.sha256(html.encode()).hexdigest()[:16],
    }

    # --- Stage summary counts ---
    # The page shows summary stats like "2 Stage 10-10.99 Drafting" etc.
    full_text = soup.get_text(" ", strip=True)

    stage_patterns = [
        ("stage_10", r"(\d+)\s+Stage 10"),
        ("stage_20", r"(\d+)\s+Stage 20"),
        ("stage_40", r"(\d+)\s+Stage 40"),
        ("stage_50", r"(\d+)\s+Stage 50"),
        ("stage_60_published", r"(\d+)\s+Stage 60"),
        ("cited_ojeu", r"(\d+)\s+Cited in the OJEU"),
        ("total_standards", r"(\d+)\s+Total Standards"),
    ]
    for key, pattern in stage_patterns:
        m = re.search(pattern, full_text)
        data["stage_counts"][key] = int(m.group(1)) if m else None

    # --- Changelog table ---
    changelog_table = None
    for table in soup.find_all("table"):
        headers = [th.get_text(strip=True).lower() for th in table.find_all("th")]
        if "date" in headers and "standard" in headers:
            changelog_table = table
            break

    if changelog_table:
        rows = changelog_table.find_all("tr")[1:]  # skip header
        for row in rows:
            cells = [td.get_text(strip=True) for td in row.find_all("td")]
            if len(cells) >= 3 and any(cells):
                data["changelog"].append({
                    "date": cells[0],
                    "standard": cells[1],
                    "change": cells[2],
                })

    # --- Individual standard cards/items ---
    # Capture all visible stage badge text + associated standard names
    standards_found = []
    # Try to grab standard identifiers (like prEN 18286, EN ISO/IEC etc.)
    standard_refs = re.findall(
        r'\b(?:pr)?(?:EN|ISO|IEC|CEN|CENELEC)[\s/\-][\w\s/\-\.]{3,40}',
        full_text
    )
    seen = set()
    for ref in standard_refs:
        cleaned = ref.strip()
        if cleaned not in seen:
            seen.add(cleaned)
            standards_found.append(cleaned)

    data["standards_mentioned"] = standards_found
    return data


def load_snapshot() -> dict | None:
    if SNAPSHOT_FILE.exists():
        with open(SNAPSHOT_FILE) as f:
            return json.load(f)
    return None


def save_snapshot(data: dict):
    SNAPSHOT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SNAPSHOT_FILE, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def compare(old: dict, new: dict) -> list[str]:
    changes = []

    # Compare stage counts
    old_counts = old.get("stage_counts", {})
    new_counts = new.get("stage_counts", {})

    stage_labels = {
        "total_standards": "总标准数量",
        "stage_10": "Stage 10（起草中）",
        "stage_20": "Stage 20（工作草案/委员会草案）",
        "stage_40": "Stage 40（公开征询/DIS）",
        "stage_50": "Stage 50（正式投票/FDIS）",
        "stage_60_published": "Stage 60（已发布）",
        "cited_ojeu": "已在OJEU引用（产生符合性推定）",
    }

    for key, label in stage_labels.items():
        old_val = old_counts.get(key)
        new_val = new_counts.get(key)
        if old_val != new_val:
            changes.append(f"📊 **{label}**：{old_val} → {new_val}")

    # Compare changelog entries
    old_log = {(e["date"], e["standard"], e["change"]) for e in old.get("changelog", [])}
    new_log = {(e["date"], e["standard"], e["change"]) for e in new.get("changelog", [])}
    added_entries = new_log - old_log

    for date, std, change in sorted(added_entries):
        changes.append(f"📋 **变更日志新增**：[{date}] {std} — {change}")

    # Compare standards mentioned
    old_stds = set(old.get("standards_mentioned", []))
    new_stds = set(new.get("standards_mentioned", []))
    for s in new_stds - old_stds:
        changes.append(f"🆕 **新标准出现**：{s}")
    for s in old_stds - new_stds:
        changes.append(f"❌ **标准消失**：{s}")

    return changes


def build_email_body(changes: list[str], old: dict, new: dict) -> str:
    now = new["fetched_at"]
    counts = new["stage_counts"]

    lines = [
        "# 🔔 EU AI Act 协调标准状态变化通知",
        "",
        f"**检测时间**：{now}",
        f"**监控网址**：{URL}",
        "",
        "---",
        "",
        "## 📌 当前标准总览",
        "",
        f"- 总标准数：**{counts.get('total_standards', 'N/A')}**",
        f"- Stage 10（起草）：{counts.get('stage_10', 'N/A')}",
        f"- Stage 20（工作/委员会草案）：{counts.get('stage_20', 'N/A')}",
        f"- Stage 40（公开征询）：{counts.get('stage_40', 'N/A')}",
        f"- Stage 50（正式投票）：{counts.get('stage_50', 'N/A')}",
        f"- Stage 60（已发布）：{counts.get('stage_60_published', 'N/A')}",
        f"- 已在OJEU引用：{counts.get('cited_ojeu', 'N/A')}",
        "",
        "---",
        "",
        "## 🔄 本次检测到的变化",
        "",
    ]

    if changes:
        for c in changes:
            lines.append(f"- {c}")
    else:
        lines.append("*（无变化——本邮件不应被发送，请检查触发逻辑）*")

    lines += [
        "",
        "---",
        "",
        f"[查看完整标准地图 →]({URL})",
        "",
        "*此邮件由 GitHub Actions 自动发送，每6小时检查一次。*",
    ]

    return "\n".join(lines)


def main():
    print(f"Fetching {URL} ...")
    html = fetch_page()
    new_data = parse_standards(html)
    print(f"Page fetched. Stage counts: {new_data['stage_counts']}")

    old_data = load_snapshot()

    if old_data is None:
        print("No previous snapshot found. Saving baseline snapshot.")
        save_snapshot(new_data)
        # Write empty result so workflow knows no notification needed
        Path("check_result.json").write_text(json.dumps({
            "has_changes": False,
            "reason": "first_run",
            "email_subject": "",
            "email_body": "",
        }))
        return

    changes = compare(old_data, new_data)

    if changes:
        print(f"CHANGES DETECTED ({len(changes)} items):")
        for c in changes:
            print(f"  {c}")

        subject = f"[AI Act标准监控] 检测到 {len(changes)} 项变化 — {new_data['fetched_at'][:10]}"
        body = build_email_body(changes, old_data, new_data)

        # Save updated snapshot only when changes are confirmed
        save_snapshot(new_data)

        Path("check_result.json").write_text(json.dumps({
            "has_changes": True,
            "change_count": len(changes),
            "email_subject": subject,
            "email_body": body,
        }, ensure_ascii=False))
    else:
        print("No changes detected.")
        # Still update the snapshot (page_hash may differ due to timestamps etc.)
        save_snapshot(new_data)
        Path("check_result.json").write_text(json.dumps({
            "has_changes": False,
            "reason": "no_changes",
            "email_subject": "",
            "email_body": "",
        }))


if __name__ == "__main__":
    main()
