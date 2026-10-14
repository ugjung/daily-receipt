# 오늘 한 일 영수증 (daily-receipt)

그날 Claude Code로 한 일을 한국어 영수증 한 장으로 정리해 주는 Claude Code 플러그인입니다.
정해 둔 시각(기본 평일 18:00)에 자동으로 만들어서 브라우저에 띄워 줍니다.

## 설치 (2분)

터미널에서 두 줄을 실행합니다.

```
claude plugin marketplace add <GitHub 저장소 주소>
claude plugin install daily-receipt@mobidays-ax
```

그다음 Claude Code 세션을 새로 열고 이렇게 말합니다.

```
/daily-receipt:setup
```

이름, 상호(팀), 자동 실행 시각을 물어보면 답하면 끝입니다.

## 쓰는 법

| 하고 싶은 것 | 이렇게 말하기 |
|---|---|
| 지금 영수증 뽑기 | `/daily-receipt:receipt` 또는 "오늘 한 일 영수증 뽑아줘" |
| 지난 날짜 영수증 | "10월 13일 영수증 뽑아줘" |
| 시각 바꾸기 | "영수증 자동 실행 17시로 바꿔줘" |
| 자동 실행 끄기 | "영수증 자동 실행 꺼줘" |

영수증 아래 버튼으로 **이미지 저장**(PNG)이나 **텍스트 복사**(Slack에 바로 붙여 넣기)를 할 수 있습니다.

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
- **가볍습니다.** 플러그인 24KB, 영수증 하루 약 8KB. 다만 자동 실행 때마다 Claude 사용량이 조금(1분 남짓) 듭니다.

## 지우기

```
"영수증 자동 실행 꺼줘"          ← 작업 스케줄러에서 제거
claude plugin uninstall daily-receipt
```

설정은 `~/.claude/daily-receipt/`, 영수증은 `~/Documents/claude-receipts/`에 남아 있으니 필요 없으면 지우면 됩니다.

## 지원 환경

- Windows: 설정부터 자동 실행까지 모두 지원
- macOS: 영수증 만들기 지원, 자동 실행은 crontab으로 등록(setup이 안내)
- Python 3, Claude Code 필요

문의: 모비데이즈 AX팀
