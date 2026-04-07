# AAS-Verify

AAS 모델 검증과 수정 UI를 `frontend`, FastAPI API 서버를 `backend`로 분리한 구조입니다.

## 구조

```text
aas-verify/
├── backend/      # FastAPI, 검증/수정 API, Python 서비스 코드
├── frontend/     # Next.js UI
├── .venv/        # 로컬 Python 가상환경
└── README.md
```

## 실행

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

접속 주소:

- `http://127.0.0.1:8000`
- `http://127.0.0.1:8000/docs`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

접속 주소:

- `http://localhost:3000`

## 환경 파일

- Next.js 환경 변수는 `frontend/.env.local`
- 예시 파일은 `frontend/.env.example`
- 백엔드가 별도 환경 변수를 쓴다면 `backend` 기준으로 추가해서 사용

## 주요 디렉토리

- `backend/api`: FastAPI 라우터
- `backend/services`: 검증/수정 서비스 로직
- `backend/utils`: 공통 유틸리티
- `frontend/app`: Next.js App Router 페이지
- `frontend/components`: UI 컴포넌트
- `frontend/lib`: API 클라이언트와 프론트 유틸리티
