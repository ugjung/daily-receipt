# 오늘 한 일 영수증 (daily-receipt)

그날 Claude(데스크톱 앱, Claude Code)로 한 일을 한국어 영수증 한 장으로 정리해 주는 플러그인입니다.
정해 둔 시각(기본 평일 18:00)에 자동으로 만들어서 브라우저에 띄워 줍니다.

## 설치 (2분)

> 공식 주소는 **github.com/ugjung/daily-receipt** 하나뿐입니다. 이름이 비슷한 다른 저장소에서는 설치하지 마세요.
> GitHub 계정은 필요 없습니다.

### Claude 데스크톱 앱

1. **Customize > Plugins**에서 Personal plugins 옆 **+**를 누릅니다.
2. **Add marketplace > Add from a repository**를 고르고 `ugjung/daily-receipt`를 입력합니다.
3. **Discover**에서 **daily-receipt**를 찾아 **Add**를 누릅니다.
4. Cowork에서 "오늘 한 일 영수증"이라고 말하면 됩니다. 매일 받으려면 Cowork의 반복 작업에 "매일 18시 오늘 한 일 영수증"을 등록하세요.

### Claude Code (터미널)

```
claude plugin marketplace add ugjung/daily-receipt
claude plugin install daily-receipt@mobidays-ax
```

그다음 Claude Code 세션을 새로 열고 `/daily-receipt:setup`을 입력합니다. 이름, 상호(팀), 자동 실행 시각을 물어보면 답하면 끝입니다.

## 쓰는 법

| 하고 싶은 것 | 이렇게 말하기 |
|---|---|
| 지금 영수증 뽑기 | "오늘 한 일 영수증 뽑아줘" (Claude Code는 `/daily-receipt:receipt`도 가능) |
| 지난 날짜 영수증 | "10월 13일 영수증 뽑아줘" |
| 시각 바꾸기 | "영수증 자동 실행 17시로 바꿔줘" |
| 자동 실행 끄기 | "영수증 자동 실행 꺼줘" |

영수증을 열면 프린터가 나옵니다. **PRINT**를 누르면 영수증이 출력되고, 아래 **텍스트 복사**로 Slack에 바로 붙여 넣을 수 있습니다.

## 어떻게 만들어지나

1. 내 PC의 Claude Code 대화 기록(`~/.claude/projects`)에서 그날 기록만 읽습니다.
2. Claude가 한 일을 프로젝트별로 묶고, 품목 5~10개로 추립니다.
3. `~/Documents/claude-receipts/날짜.html`로 저장합니다.

사용시간은 Claude와 실제로 주고받은 시간입니다. 5분 넘게 아무 기록이 없는 구간은 자리를 비운 것으로 보고 빼요.

## 안심하고 쓰세요

- **내 기록만, 읽기만.** 대화 기록과 메모리는 읽기만 하고 고치지 않습니다. 파일을 쓰는 곳은 `Documents/claude-receipts` 한 곳뿐입니다.
- **밖으로 안 나갑니다.** 영수증은 내 PC에만 저장됩니다. Slack이나 Notion으로 자동으로 올리지 않습니다.
- **비밀 정보는 가립니다.** 채팅에 붙여 넣은 API 키, 비밀번호, URL, 이메일, 전화번호는 수집 단계에서 가려집니다. 영수증에는 동료 실명이나 금액을 쓰지 않습니다.
- **자동 실행 권한은 최소한으로.** 예약 실행 때 Claude는 python 스크립트 실행, 파일 읽기, 영수증 폴더에 쓰기만 할 수 있습니다.
- **설치본만 믿으세요.** 업데이트는 이 저장소 주인만 올릴 수 있습니다. 다른 사람은 저장소를 고칠 수 없고, 누가 설치했는지도 알 수 없습니다.
- **가볍습니다.** 플러그인 50KB 남짓, 영수증 하루 약 8KB. 다만 자동 실행 때마다 Claude 사용량이 조금(1분 남짓) 듭니다.

## 지우기

```
"영수증 자동 실행 꺼줘"          ← 작업 스케줄러에서 제거
claude plugin uninstall daily-receipt
```

설정은 `~/.claude/daily-receipt/`, 영수증은 `~/Documents/claude-receipts/`에 남아 있으니 필요 없으면 지우면 됩니다.

## 지원 환경

- Windows: 설정부터 자동 실행까지 모두 지원
- macOS: 영수증 만들기 지원, 자동 실행은 crontab으로 등록(setup이 안내)
- Python 3 필요 (없으면 setup이 설치를 도와줍니다)

문의: 모비데이즈 AX팀 (사내 메신저)
