---
name: setup
description: 오늘 한 일 영수증(daily-receipt)의 첫 설정과 자동 실행 관리. 영수증에 찍힐 이름과 상호 설정, 매일 자동 실행 켜기, 시각 바꾸기, 끄기, 상태 확인에 사용한다. "영수증 설정", "영수증 자동 실행 켜줘/꺼줘", "영수증 시간 바꿔줘", "/daily-receipt:setup".
---

# 영수증 설정과 자동 실행

`<스킬폴더>`는 이 스킬을 불러올 때 표시되는 Base directory다.

## 사용자가 처음 설정할 때

필요한 것은 세 가지뿐이다. 이미 말한 것은 다시 묻지 않는다. 한 번에 묻는다.

1. **고객 이름**: 영수증 "고객" 칸 (예: 홍길동, gildong)
2. **상호**: 영수증 "상호" 칸. 보통 회사명과 팀 (예: 모비데이즈 AX팀)
3. **자동 실행 시각**: 기본 18:00, 평일만. 원하면 매일, 원하면 끄기.

## Windows

`<스킬폴더>/scripts/schedule.ps1`을 PowerShell로 실행한다.

```powershell
# 이름, 상호 저장 + 평일 18:00 자동 실행 켜기
powershell -NoProfile -ExecutionPolicy Bypass -File "<스킬폴더>/scripts/schedule.ps1" -Customer "홍길동" -Store "모비데이즈 AX팀" -Time 18:00

# 매일 실행:      -Time 18:00 -EveryDay
# 끝나고 창 안 띄움: -NoOpen
# 1시간마다:     -Hourly  (지난 실행 뒤 Claude 사용 기록이 없으면 그 시간은 건너뜀)
# 끄기:          -Off
# 상태 보기:      -Status
```

이 스크립트가 하는 일 (사용자가 물으면 이대로 설명한다):
- `~/.claude/daily-receipt/config.json`에 이름, 상호, 시각을 저장한다.
- `~/.claude/daily-receipt/run.ps1`을 만든다. 정해진 시각에 `claude -p "/daily-receipt:receipt"`를 돌리고, 다 되면 영수증을 브라우저로 연다.
- 작업 스케줄러에 `ClaudeDailyReceipt` 작업을 현재 사용자 권한으로 등록한다. 관리자 권한은 필요 없다. PC가 꺼져서 놓치면 다음에 켤 때 실행된다.
- 예약 실행 때 Claude에게 주는 권한은 python 스크립트 실행, 파일 읽기, `Documents/claude-receipts` 안에 쓰기뿐이다.
- 실행 기록은 `~/.claude/daily-receipt/logs/`에 남고 30일 지나면 지워진다.

## macOS

schedule.ps1 대신 crontab 한 줄로 등록한다(예: 평일 18:00). config.json은 직접 JSON으로 쓴다.

```
0 18 * * 1-5 cd ~ && $(which claude) -p "/daily-receipt:receipt scheduled-run" --allowedTools "Bash(python3 *)" Read Glob "Edit(~/Documents/claude-receipts/**)" >> ~/.claude/daily-receipt/logs/cron.log 2>&1
```

## 끝나고

- 결과를 한두 줄로 알려 준다: 켜졌는지, 다음 실행 시각, 이름과 상호.
- 바로 확인하고 싶다고 하면 `/daily-receipt:receipt`로 지금 한 장 뽑아 준다.

## 완전히 지우기

1. `schedule.ps1 -Off` (macOS는 crontab에서 줄 삭제)
2. `claude plugin uninstall daily-receipt`
3. 원하면 `~/.claude/daily-receipt/` 폴더와 `~/Documents/claude-receipts/` 폴더 삭제. 지우기 전에 사용자에게 확인한다.
