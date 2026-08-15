# SellAuth 입양하세요 계정 자동 중개 봇 (Dropship Bridge)

요청하신 **3가지 상품**만 정확히 매핑하여 업자에게서 실시간으로 계정을 땡겨오는 자동화 서버입니다.

---

## 📦 등록된 3가지 상품 매핑 표

| 내 상품 번호 | 단축 코드 (`item`) | 업자 상품 슬러그 (ID) |
|---|---|---|
| **1번 상품** | `potion350` 또는 `item1` | `326-350-potions-249k-273l-bucks` |
| **2번 상품** | `potion850` 또는 `item2` | `826-850-potions-473k-568k-bucks` |
| **3번 상품** | `potion1300` 또는 `item3` | `1276-1300-potions-759k-869k-bucks` |

---

## 🚀 로컬 테스트 방법 (컴퓨터에서 바로 돌려보기)

1. **가상환경 생성 및 패키지 설치:**
   ```bash
   pip install -r requirements.txt
   ```

2. **환경설정 파일 생성:**
   `.env.example` 파일을 복사하여 `.env` 로 이름을 바꿉니다.
   - 처음 테스트할 때는 `TEST_MODE=True` 로 두고 테스트하면 결제 없이 가짜 계정 반환을 테스트할 수 있습니다.

3. **서버 실행:**
   ```bash
   python main.py
   ```
   서버가 `http://127.0.0.1:8000` 에서 시작됩니다.

4. **브라우저나 주소창에서 테스트해보기:**
   - 1번 상품 테스트: `http://127.0.0.1:8000/deliver?item=potion350`
   - 2번 상품 테스트: `http://127.0.0.1:8000/deliver?item=potion850`
   - 3번 상품 테스트: `http://127.0.0.1:8000/deliver?item=potion1300`
   👉 화면에 계정(`아이디:비밀번호`)이 정상적으로 뜨는지 확인합니다!

---

## 🌐 24시간 무료 서버 배포 (Render.com)

1. 이 폴더의 파일들을 **GitHub** 새 리포지토리에 올립니다.
2. [Render.com](https://render.com) 에 가입 후 **New Web Service**를 누르고 깃허브 리포지토리를 연결합니다.
3. 설정:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. 배포가 완료되면 생성된 고유 URL을 받습니다 (예: `https://my-roblox-bridge.onrender.com`).

---

## 🛒 내 SellAuth 상품에 Dynamic URL 연결하기

SellAuth 대시보드에서 3가지 상품을 만들고, **Deliverable Type**을 **`Dynamic`**으로 설정한 후 아래 URL을 각각 넣어주면 끝입니다!

- **1번 상품 (326-350 포션)**:
  `https://내서버주소.onrender.com/deliver?item=potion350`
- **2번 상품 (826-850 포션)**:
  `https://내서버주소.onrender.com/deliver?item=potion850`
- **3번 상품 (1276-1300 포션)**:
  `https://내서버주소.onrender.com/deliver?item=potion1300`
