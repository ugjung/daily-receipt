"""오늘(또는 지정 날짜)의 Claude Code 기록을 세션 단위로 요약해 JSON으로 출력한다.

사용: python collect.py [YYYY-MM-DD]
"""
import collections
import datetime as dt
import glob
import json
import os
import re
import sys

KST = dt.timezone(dt.timedelta(hours=9))
HOME = os.path.expanduser("~")
PROJECTS = os.path.join(HOME, ".claude", "projects")
EDIT_TOOLS = {"Write", "Edit", "NotebookEdit"}
GAP_CAP_MIN = 5  # 이 이상 비면 자리를 비운 것으로 보고 최대 5분만 인정
SKIP_PREFIX = ("<command-", "<local-command", "<system-reminder>", "Caveat:", "[Request interrupted",
               "<task-notification>", "<ide_opened_file>", "<ide_selection>",
               "This session is being continued")


def to_kst(ts):
    return dt.datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(KST)


# 영수증에 필요 없는 민감 정보는 수집 단계에서 가린다
REDACT = [
    (re.compile(r"(?i)(api[_-]?key|secret|token|password|passwd|pwd|비밀번호|비번|client[_-]?(id|secret))(\W{0,5})\S+"), r"[가림]"),
    (re.compile(r"(sk|pk|xox[abp]|ghp|gho|AKIA|AIza)[A-Za-z0-9_\-]{10,}"), "[키 가림]"),
    (re.compile(r"[A-Za-z0-9_\-]{32,}"), "[긴 문자열 가림]"),
    (re.compile(r"https?://\S+"), "[링크]"),
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"), "[이메일]"),
    (re.compile(r"\d{1,3}(\.\d{1,3}){3}(:\d+)?"), "[IP]"),
    (re.compile(r"01\d-?\d{3,4}-?\d{4}"), "[전화]"),
]


def redact(text):
    for pat, rep in REDACT:
        text = pat.sub(rep, text)
    return text


def clean_prompt(text):
    text = re.sub(r"<pasted_content[^>]*>(.*?)</pasted_content[^>]*>",
                  lambda m: f"[붙여넣기 {len(m.group(1))}자: {m.group(1).strip()[:60]}]", text, flags=re.S)
    text = re.sub(r"<system-reminder>.*?</system-reminder>", "", text, flags=re.S)
    text = re.sub(r"\[Image: source:[^\]]*\]", "[이미지]", text)
    return redact(re.sub(r"\s+", " ", text).strip())[:220]


def user_text(msg):
    c = msg.get("content")
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        return " ".join(x.get("text", "") for x in c if isinstance(x, dict) and x.get("type") == "text")
    return ""


def scan(path, day):
    """세션 하나를 읽어 요청(segment) 단위로 시간과 수정 파일을 나눈다."""
    custom_title = ai_title = None
    cwd = None
    segs, files, times = [], [], []
    tools = collections.Counter()
    models = collections.Counter()
    prev = None
    with open(path, encoding="utf-8") as f:
        for line in f:
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            t = d.get("type")
            if t == "custom-title" and d.get("customTitle"):
                custom_title = d["customTitle"]
            elif t == "ai-title" and d.get("aiTitle"):
                ai_title = d["aiTitle"]
            ts = d.get("timestamp")
            if not ts or t not in ("user", "assistant"):
                continue
            k = to_kst(ts)
            if k.date() != day:
                continue
            times.append(k)
            cwd = d.get("cwd") or cwd
            msg = d.get("message") or {}
            if prev and segs and k > prev:
                # 이 요청이 차지한 시간 구간. 5분 넘게 비면 5분까지만 인정한다.
                end = min(k, prev + dt.timedelta(minutes=GAP_CAP_MIN))
                segs[-1]["iv"].append((prev, end))
            prev = k
            if t == "user" and not d.get("isMeta"):
                raw = user_text(msg).strip()
                if raw and not raw.startswith(SKIP_PREFIX):
                    p = clean_prompt(raw)
                    if p:
                        segs.append({"time": f"{k:%H:%M}", "min": 0.0, "text": p, "files": [], "iv": []})
            elif t == "assistant":
                if msg.get("model") and not msg["model"].startswith("<"):
                    models[msg["model"]] += 1
                for c in msg.get("content") or []:
                    if isinstance(c, dict) and c.get("type") == "tool_use":
                        name = c.get("name", "")
                        tools[name.split("__")[-1]] += 1
                        fp = (c.get("input") or {}).get("file_path")
                        if name in EDIT_TOOLS and fp and "Temp" not in fp.split(os.sep) and "/tmp/" not in fp:
                            fp = fp.replace(HOME, "~")
                            if fp not in files:
                                files.append(fp)
                            if segs and os.path.basename(fp) not in segs[-1]["files"]:
                                segs[-1]["files"].append(os.path.basename(fp))
    if not segs:
        return None
    if all("daily-receipt" in s["text"] or "영수증" in s["text"] for s in segs) and any("daily-receipt" in s["text"] for s in segs):
        return None  # 영수증 생성 세션 자체는 제외
    for s in segs:
        if not s["files"]:
            del s["files"]
    times.sort()
    return {
        "session": os.path.basename(path)[:8],
        "title": custom_title or ai_title,
        "cwd": cwd.replace(HOME, "~") if cwd else None,
        "start": f"{times[0]:%H:%M}",
        "end": f"{times[-1]:%H:%M}",
        "active_min": 0,
        "turns": len(segs),
        "prompts": segs,
        "files_edited": files[:40],
        "tools": dict(tools.most_common(8)),
        "models": dict(models),
    }


def memory_changes(day):
    out = []
    for p in glob.glob(os.path.join(PROJECTS, "*", "memory", "*.md")):
        m = dt.datetime.fromtimestamp(os.path.getmtime(p), KST)
        if m.date() == day and not p.endswith("MEMORY.md"):
            with open(p, encoding="utf-8") as f:
                head = f.read(600)
            desc = re.search(r"description:\s*(.+)", head)
            out.append({"file": os.path.basename(p), "description": desc.group(1).strip() if desc else ""})
    return out


def allocate(sessions):
    """여러 창이 동시에 돌던 시간은 한 번만 센다.

    겹친 구간은 그때 돌던 요청들끼리 똑같이 나눠 갖는다. 그래서 모든 요청의 분을 더하면
    그날 실제로 Claude를 쓴 시간(겹침 제거)과 같아진다.
    """
    events = []
    for si, s in enumerate(sessions):
        for gi, g in enumerate(s["prompts"]):
            for a, b in g.pop("iv"):
                events.append((a, 1, (si, gi)))
                events.append((b, -1, (si, gi)))
    events.sort(key=lambda e: (e[0], e[1]))
    active, last, union = {}, None, 0.0
    alloc = collections.defaultdict(float)
    for t, kind, key in events:
        if last is not None and active and t > last:
            span = (t - last).total_seconds() / 60
            union += span
            for k in active:
                alloc[k] += span / len(active)
        last = t
        if kind == 1:
            active[key] = active.get(key, 0) + 1
        else:
            active[key] -= 1
            if not active[key]:
                del active[key]
    raw = 0
    for si, s in enumerate(sessions):
        for gi, g in enumerate(s["prompts"]):
            g["min"] = round(alloc[(si, gi)])
        s["active_min"] = max(1, sum(g["min"] for g in s["prompts"]))
        s["prompts"] = s["prompts"][:80]
        raw += s["active_min"]
    return round(union)


def main():
    day = dt.date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else dt.datetime.now(KST).date()
    cutoff = dt.datetime.combine(day, dt.time(), KST).timestamp()
    sessions = []
    for p in glob.glob(os.path.join(PROJECTS, "*", "*.jsonl")):
        if os.path.getmtime(p) < cutoff:
            continue
        s = scan(p, day)
        if s:
            sessions.append(s)
    sessions.sort(key=lambda s: s["start"])
    total = allocate(sessions)
    result = {
        "date": day.isoformat(),
        "weekday": "월화수목금토일"[day.weekday()],
        "session_count": len(sessions),
        "total_active_min": total,  # 겹치는 시간은 한 번만 센 실제 사용시간
        "models": dict(sum((collections.Counter(s["models"]) for s in sessions), collections.Counter())),
        "memory_updates": memory_changes(day),
        "sessions": sessions,
    }
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
