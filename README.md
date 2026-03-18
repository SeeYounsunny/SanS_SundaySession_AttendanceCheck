## Sans Sunday Session Attendance Bot (MVP)

모노레포 구성:

- `field_bot/`: 조(현장) 단체방용 출석 봇
- `admin_bot/`: 운영자 DM/운영자방용 운영 봇
- `shared/`: DB 모델/쿼리/공통 유틸

### MVP 목표(1개 조로 end-to-end)

1. 현장봇이 그룹에 초대되면 `pending` 그룹으로 자동 등록
2. 운영봇에서 해당 그룹을 `enable`
3. 현장 단체방에서 `/checkin`으로 출석 기록
4. 운영봇 DM에서 `/stats`로 주간/전체 통계 확인

### 정책(요청하신 최소 합의사항 반영)

- **등록 방식**: field 봇이 그룹에 들어오면 자동 `pending` 등록 → admin 봇에서 enable
- **출석 키(유니크)**: `(chat_id, week_date, user_id)` 유니크
- **운영 UI**: admin 봇 DM 명령(`/groups`, `/enable`, `/stats`) + 인라인 버튼(최소)

### 로컬 실행(개발용)

#### 1) 환경변수 준비

- `DATABASE_URL`: Postgres URL (두 봇 동일하게 사용)
- `FIELD_BOT_TOKEN`: BotFather 토큰
- `ADMIN_BOT_TOKEN`: BotFather 토큰
- `ADMIN_USER_IDS`: 운영자 텔레그램 user_id 목록(쉼표 구분). 예: `123,456`

#### 2) 의존성 설치

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

#### 3) DB 마이그레이션

```bash
alembic upgrade head
```

#### 4) 봇 실행

터미널 2개에서 각각 실행:

```bash
python -m field_bot
```

```bash
python -m admin_bot
```

### Railway 배포(요약)

- Project 1개
- Service 2개
  - field: start command `python -m field_bot`
  - admin: start command `python -m admin_bot`
- Postgres 1개
  - 두 서비스에 같은 `DATABASE_URL` 환경변수로 연결

