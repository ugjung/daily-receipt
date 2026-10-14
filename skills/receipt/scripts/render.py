"""영수증 JSON을 assets/receipt-template.html에 넣어 HTML로 저장한다.

사용: python render.py receipt.json [출력경로]
출력 기본값: ~/Documents/claude-receipts/YYYY-MM-DD.html
디자인은 템플릿 하나에만 있다. 이 스크립트는 데이터만 채운다.
"""
import datetime as dt
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "..", "assets", "receipt-template.html")
CONFIG = os.path.join(os.path.expanduser("~"), ".claude", "daily-receipt", "config.json")


def load_config():
    try:
        with open(CONFIG, encoding="utf-8-sig") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def model_name(mid):
    """claude-opus-5-5 -> Claude Opus 5.5"""
    parts = mid.split("-")
    if parts[0] != "claude" or len(parts) < 3:
        return mid
    nums = [p for p in parts[2:] if p.isdigit() and len(p) < 3]
    return f"Claude {parts[1].capitalize()} {'.'.join(nums)}".strip()


def build_data(r):
    cfg = load_config()
    models = sorted((r.get("models") or {}).items(), key=lambda x: -x[1])
    return {
        "date": r["date"],
        "weekday": r["weekday"],
        "store": r.get("store") or cfg.get("store") or "",
        "customer": r.get("customer") or cfg.get("customer") or os.environ.get("USERNAME") or os.environ.get("USER") or "",
        "issued_at": dt.datetime.now().strftime("%Y%m%d%H%M%S"),
        "payments": r.get("payments") or [f"{model_name(m)} / {c:,}회" for m, c in models],
        "items": r["items"],
        "carry_over": r.get("carry_over") or [],
        "one_liner": r.get("one_liner") or "",
    }


def render(r):
    with open(TEMPLATE, encoding="utf-8") as f:
        tpl = f.read()
    data = json.dumps(build_data(r), ensure_ascii=False, indent=1).replace("</", "<\\/")
    html, n = re.subn(r'(<script type="application/json" id="data">).*?(</script>)',
                      lambda m: f"{m.group(1)}\n{data}\n{m.group(2)}", tpl, count=1, flags=re.S)
    if n != 1:
        raise SystemExit("템플릿에서 data 블록을 찾지 못했습니다")
    return html.replace("<title>오늘 한 일 영수증</title>", f"<title>오늘 한 일 영수증 {r['date']}</title>", 1)


def main():
    with open(sys.argv[1], encoding="utf-8") as f:
        r = json.load(f)
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(
        os.path.expanduser("~"), "Documents", "claude-receipts", f"{r['date']}.html")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(render(r))
    sys.stdout.reconfigure(encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
