# 🏋️ Iron Secretary (아이언 세크리터리)

**Iron Secretary**는 텔레그램을 통해 운동 일지를 간편하게 기록하고 관리하는 개인용 봇입니다.  
텍스트로 운동 내용을 보내면 **날짜를 자동으로 인식**하고, **버튼으로 운동 부위를 선택**하여 Markdown 파일로 체계적으로 저장해줍니다.

---

## 📂 프로젝트 구조 (Project Structure)

```text
iron-secretary/
├── README.md               # 📖 프로젝트 설명서 & 사용 가이드
├── config.ini              # ⚙️ 봇 설정 파일 (토큰, 경로 등)
├── requirements.txt        # 📦 필수 라이브러리 목록
├── run_bot.bat             # 윈도우용 실행 스크립트
├── manage_bot.sh           # 리눅스/맥용 실행/관리 스크립트
├── workout_db.md           # 🗂️ [Data] 전체 운동 기록 통합 파일 (Master)
├── recent_workouts.md      # 📅 [Data] 최근 7일간의 기록 요약
├── logs/                   # 📂 [Data] 월별 기록 저장소 (예: 2026-02.md)
└── src/                    # 💻 소스 코드
    ├── bot.py              # 🤖 봇 메인 실행 파일 (UI, 대화 흐름)
    ├── data_manager.py     # 💾 파일 저장, 날짜 정렬, 데이터 관리 로직
    └── workout_parser.py   # 📝 텍스트 날짜 파싱 모듈
```

---

## 🛠 주요 기능 (Features)

1.  **스마트 날짜 인식**: 메시지에 "2/9", "어제", "오늘" 등이 포함되면 자동으로 날짜를 인식합니다.
2.  **간편한 부위 태그**: 클릭 가능한 버튼으로 운동 부위(가슴, 등, 하체 등)를 쉽게 태그할 수 있습니다.
3.  **데이터 안전 관리**:
    *   **3중 저장**: `workout_db.md` (전체), `logs/YYYY-MM.md` (월별), `recent_workouts.md` (최근 7일)에 동시 저장됩니다.
    *   **중복 방지**: 같은 날짜에 기록이 있으면 **[이어쓰기]** 또는 **[덮어쓰기]**를 선택할 수 있습니다.
4.  **보안 기능**: `config.ini`에 등록된 주인(ALLOWED_ID)만 봇을 사용할 수 있습니다.

---

## ⚙️ 설정 가이드 (Configuration)

봇을 실행하기 위해 **`config.ini`** 파일 설정이 필수적입니다. 아래 내용을 참고하여 작성해주세요.

### `config.ini` 작성 예시

```ini
[TELEGRAM]
# 1. 봇 토큰: BotFather에게 발급받은 문자열
BOT_TOKEN = 123456789:ABCdefGHIjklMNOpqrsTUVwxyz

# 2. 허용 ID: 본인의 텔레그램 숫자 ID (userinfobot 등을 통해 확인)
ALLOWED_ID = 123456789

[PATHS]
# 3. 데이터 저장 경로 (선택 사항)
# 비워두면 프로젝트 폴더 내에 저장됩니다.
# 예시 (Windows): C:/Users/MyName/Documents/HealthLogs
DATA_DIR = 
```

> **주의**: `ALLOWED_ID`에 본인의 ID를 넣지 않으면 봇이 응답하지 않거나 권한 오류 메시지를 보냅니다.

---

## 🚀 설치 및 실행 (Installation & Run)

### 1단계: 필수 라이브러리 설치
터미널(또는 CMD)을 열고 다음 명령어를 입력합니다.

```bash
pip install -r requirements.txt
```

### 2단계: 봇 실행하기

#### 🐧 Linux / Mac
`manage_bot.sh` 스크립트를 사용하면 백그라운드에서 편리하게 관리할 수 있습니다.

```bash
# 실행 권한 부여 (최초 1회)
chmod +x manage_bot.sh

# 봇 시작 (백그라운드 실행)
./manage_bot.sh start

# 봇 상태 확인
./manage_bot.sh status

# 봇 재시작
./manage_bot.sh restart

# 봇 종료
./manage_bot.sh stop
```

#### 🪟 Windows
*   `run_bot.bat` 파일을 더블 클릭하면 실행됩니다.
*   또는 CMD에서 직접 실행: `python src/bot.py`

---

## 📝 사용 방법 (Usage)

1.  봇에게 운동 내용을 보냅니다.
    > 예: "오늘 스쿼트 100kg 5x5 했음"
2.  봇이 날짜를 인식하고 **운동 부위 선택 버튼**을 보여줍니다.
3.  해당하는 부위를 선택하고 **[완료]** 버튼을 누릅니다.
4.  날짜와 내용을 최종 확인하고 **[저장]**을 누르면 파일에 기록됩니다.

---

## 📦 배포 (Deployment)

배포 시 다음 파일들이 필요합니다. `src` 폴더와 `config.ini`, 그리고 실행 스크립트를 챙기세요.

*   `requirements.txt`
*   `config.ini`
*   `src/`
*   `manage_bot.sh` / `run_bot.bat`

---

## 📷 시연 영상 및 결과 (Demo)

**1. 시연 영상 (Demo Video)**
![Demo Video](https://imgur.com/XAao2mh)

**2. 최종 저장 결과 (Final Result)**
![Final Result](https://imgur.com/T1kr1aO.png)
