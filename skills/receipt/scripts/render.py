"""영수증 JSON을 한국어 영수증 HTML로 렌더링한다.

사용: python render.py receipt.json [출력경로]
출력 기본값: ~/Documents/claude-receipts/YYYY-MM-DD.html
"""
import datetime as dt
import html
import json
import os
import sys


CONFIG = os.path.join(os.path.expanduser("~"), ".claude", "daily-receipt", "config.json")


def load_config():
    try:
        with open(CONFIG, encoding="utf-8-sig") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def esc(s):
    return html.escape(str(s or ""))


def dur(m):
    h, m = divmod(m, 60)
    return f"{h}시간 {m:02d}분" if h else f"{m}분"


def model_name(mid):
    """claude-opus-5-5 -> Claude Opus 5.5"""
    parts = mid.split("-")
    if parts[0] != "claude" or len(parts) < 3:
        return mid
    nums = [p for p in parts[2:] if p.isdigit() and len(p) < 3]
    return f"Claude {parts[1].capitalize()} {'.'.join(nums)}".strip()


def render_items(items):
    """프로젝트(group)별로 묶고, 종류 태그, 점선, 시간 막대를 붙인다."""
    top = max(i["minutes"] for i in items)
    groups = {}
    for i in items:
        groups.setdefault(i.get("group") or "", []).append(i)
    out, n = [], 0
    for g, members in groups.items():
        boxed = bool(g) and len(members) > 1
        if boxed:
            sub = sum(i["minutes"] for i in members)
            out.append(f'<div class="group"><span class="gname">{esc(g)}</span>'
                       f'<span class="lead"></span><span class="gsum">소계 {dur(sub)}</span></div>')
        for i in members:
            n += 1
            name = i["name"]
            if boxed and name.startswith(g):
                name = name[len(g):].strip() or name
            kind = f'<span class="kind">{esc(i["kind"])}</span>' if i.get("kind") else ""
            main = '<span class="main">MAIN</span>' if i["minutes"] == top else ""
            pct = max(4, round(i["minutes"] / top * 100))
            out.append(f"""<div class="item{' in' if boxed else ''}">
  <div class="row"><span class="no">{n:02d}</span>{kind}<span class="name">{esc(name)}</span>{main}<span class="lead"></span><span class="amt">{dur(i['minutes'])}</span></div>
  <div class="done">{esc(i.get('done'))}</div>
  <div class="bar"><i style="width:{pct}%"></i></div>
</div>""")
    return "\n".join(out)


def plain_text(r, total):
    """Slack, 메신저에 붙여 넣기 좋은 텍스트 영수증."""
    lines = [f"🧾 오늘 한 일 영수증  {r['date']}({r['weekday']})",
             f"{r.get('store', '')} / {r.get('customer', '')}", "-" * 28]
    groups = {}
    for i in r["items"]:
        groups.setdefault(i.get("group") or "", []).append(i)
    n = 0
    for g, members in groups.items():
        if g and len(members) > 1:
            lines.append(f"■ {g}  ({dur(sum(i['minutes'] for i in members))})")
        for i in members:
            n += 1
            name = i["name"][len(g):].strip() if g and len(members) > 1 and i["name"].startswith(g) else i["name"]
            kind = f"[{i['kind']}] " if i.get("kind") else ""
            lines.append(f" {n:02d} {kind}{name} .. {dur(i['minutes'])}")
            if i.get("done"):
                lines.append(f"     ㄴ {i['done']}")
    lines += ["-" * 28, f"총 사용시간  {dur(total)}"]
    for c in r.get("carry_over") or []:
        lines.append(f"이월  {c}")
    if r.get("one_liner"):
        lines.append(f"\"{r['one_liner']}\"")
    return "\n".join(lines)


def render(r):
    cfg = load_config()
    r.setdefault("store", cfg.get("store") or "Claude 작업소")
    r.setdefault("customer", cfg.get("customer") or os.environ.get("USERNAME") or os.environ.get("USER") or "-")
    items = r["items"]
    total = sum(i["minutes"] for i in items)
    approval = dt.datetime.now().strftime("%Y%m%d%H%M%S")
    models = sorted((r.get("models") or {}).items(), key=lambda x: -x[1])
    pay = "\n".join(
        f'<div class="kv"><span>{"결제수단" if n == 0 else ""}</span><span>{esc(model_name(m))} / {c:,}회</span></div>'
        for n, (m, c) in enumerate(models)
    ) or '<div class="kv"><span>결제수단</span><span>Claude</span></div>'
    rows = render_items(items)
    text = json.dumps(plain_text(r, total), ensure_ascii=False).replace("</", "<\\/")
    carry = r.get("carry_over") or []
    carry_html = ""
    if carry:
        carry_html = '<div class="sec">** 내일로 이월 (적립 예정) **</div>' + "".join(
            f'<div class="carry">- {esc(c)}</div>' for c in carry
        ) + '<div class="hr"></div>'

    return f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>오늘 한 일 영수증 {esc(r['date'])}</title>
<link href="https://fonts.googleapis.com/css2?family=Nanum+Gothic+Coding:wght@400;700&display=swap" rel="stylesheet">
<style>
:root{{--bg:#f4f3ef;--paper:#fff;--ink:#1a1a1a;--sub:#777;--line:#999}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--ink);font-family:'Nanum Gothic Coding','D2Coding',monospace;display:flex;flex-direction:column;align-items:center;padding:40px 16px}}
.paper{{width:100%;max-width:400px;background:var(--paper);padding:28px 22px 20px;box-shadow:0 6px 24px rgba(0,0,0,.12);position:relative;font-size:13px;line-height:1.5}}
.paper:after{{content:"";position:absolute;left:0;right:0;bottom:-10px;height:10px;background:linear-gradient(-45deg,transparent 7px,var(--paper) 0),linear-gradient(45deg,transparent 7px,var(--paper) 0);background-size:14px 14px}}
h1{{text-align:center;font-size:24px;letter-spacing:.35em;margin:0 0 2px}}
.tag{{text-align:center;color:var(--sub);font-size:11px;letter-spacing:.2em;margin-bottom:14px}}
.hr{{border-top:1px dashed var(--line);margin:10px 0}}
.hr2{{border-top:2px solid var(--ink);margin:10px 0}}
.kv{{display:flex;justify-content:space-between}}
.kv span:first-child{{color:var(--sub)}}
.head{{display:flex;justify-content:space-between;font-weight:700;border-bottom:1px solid var(--ink);padding-bottom:4px;margin-bottom:12px}}
.row{{display:flex;align-items:baseline;gap:6px}}
.no{{color:var(--sub);font-size:11px}}
.kind{{font-size:10px;border:1px solid var(--ink);padding:0 4px;line-height:15px;white-space:nowrap;align-self:center}}
.name{{font-weight:700;word-break:keep-all;min-width:0}}
.main{{font-size:9px;background:var(--ink);color:var(--paper);padding:0 4px;line-height:14px;letter-spacing:.08em;align-self:center}}
.lead{{flex:1;border-bottom:1px dotted var(--line);min-width:12px;transform:translateY(-3px)}}
.amt{{white-space:nowrap;font-weight:700}}
.item{{margin-bottom:11px}}
.item.in{{padding-left:10px;border-left:2px solid var(--ink);margin-left:2px}}
.done{{color:#555;font-size:11.5px;padding-left:22px;word-break:keep-all;margin-top:1px}}
.bar{{margin:4px 0 0 22px;height:3px;background:repeating-linear-gradient(90deg,#ddd 0 2px,transparent 2px 4px)}}
.bar i{{display:block;height:100%;background:var(--ink)}}
.group{{display:flex;align-items:baseline;gap:6px;margin:16px 0 8px;font-size:12px}}
.group:first-child{{margin-top:0}}
.gname{{background:var(--ink);color:var(--paper);padding:1px 7px;font-weight:700}}
.gsum{{color:var(--sub);white-space:nowrap}}
.total{{display:flex;justify-content:space-between;font-size:18px;font-weight:700;margin:4px 0}}
.sec{{text-align:center;font-weight:700;margin:4px 0 6px}}
.carry{{font-size:12px;word-break:keep-all}}
.memo{{text-align:center;font-size:14px;font-weight:700;margin:8px 0;word-break:keep-all}}
.barcode{{height:46px;margin:14px 8px 4px;background:repeating-linear-gradient(90deg,var(--ink) 0 2px,transparent 2px 4px,var(--ink) 4px 5px,transparent 5px 8px,var(--ink) 8px 11px,transparent 11px 12px)}}
.code{{text-align:center;font-size:11px;letter-spacing:.3em}}
.foot{{text-align:center;color:var(--sub);font-size:11px;margin-top:10px}}
.actions{{display:flex;gap:8px;margin-top:28px}}
button{{font-family:inherit;border:1px solid var(--ink);background:var(--ink);color:#fff;padding:8px 16px;cursor:pointer}}
button.ghost{{background:transparent;color:var(--ink)}}
</style></head><body>
<div class="paper" id="receipt">
  <h1>영수증</h1>
  <div class="tag">오늘 한 일 / TODAY'S RECEIPT</div>
  <div class="kv"><span>상호</span><span>{esc(r['store'])}</span></div>
  <div class="kv"><span>고객</span><span>{esc(r['customer'])}</span></div>
  <div class="kv"><span>일시</span><span>{esc(r['date'])}({esc(r['weekday'])})</span></div>
  <div class="hr2"></div>
  <div class="head"><span>품명</span><span>사용시간</span></div>
  {rows}
  <div class="hr"></div>
  <div class="kv"><span>품목 수</span><span>{len(items)}</span></div>
  <div class="hr2"></div>
  <div class="total"><span>총 사용시간</span><span>{dur(total)}</span></div>
  {pay}
  <div class="kv"><span>승인번호</span><span>{approval}</span></div>
  <div class="hr"></div>
  {carry_html}
  <div class="memo">"{esc(r.get('one_liner', '오늘도 수고하셨습니다'))}"</div>
  <div class="barcode"></div>
  <div class="code">{approval}</div>
  <div class="foot">※ 사용시간은 Claude와 실제로 주고받은 시간 기준, 결제수단은 모델별 응답 수<br>교환 및 환불 불가. 오늘도 수고하셨습니다.</div>
</div>
<div class="actions"><button onclick="save()">이미지로 저장</button><button class="ghost" id="cp" onclick="copyText()">텍스트 복사</button></div>
<script>
const TEXT={text};
function copyText(){{
  const done=()=>{{const b=document.getElementById('cp');b.textContent='복사됨';setTimeout(()=>b.textContent='텍스트 복사',1500);}};
  if(navigator.clipboard)navigator.clipboard.writeText(TEXT).then(done,fallback);else fallback();
  function fallback(){{const t=document.createElement('textarea');t.value=TEXT;document.body.appendChild(t);t.select();document.execCommand('copy');t.remove();done();}}
}}
// 이미지 저장을 누를 때만 라이브러리를 불러온다. 열어 보기만 할 때는 외부 스크립트를 받지 않는다.
function save(){{
  const go=()=>html2canvas(document.getElementById('receipt'),{{scale:2,backgroundColor:null}}).then(c=>{{const a=document.createElement('a');a.download='영수증_{esc(r['date'])}.png';a.href=c.toDataURL();a.click();}});
  if(window.html2canvas)return go();
  const s=document.createElement('script');s.src='https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js';s.onload=go;document.head.appendChild(s);
}}
</script>
</body></html>"""


def main():
    src = sys.argv[1]
    with open(src, encoding="utf-8") as f:
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
