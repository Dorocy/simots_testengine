# 🛠️ AAS-Verify

[🖥️ 데모 바로 보기](http://te.amrc.kr/docs)

AAS-Verify는 Asset Administration Shell (AAS) 모델의 구조와 데이터를 자동으로 검증하는 FastAPI 기반 백엔드 도구입니다.  
산업용 디지털 트윈 표준인 AAS의 JSON 데이터를 받아 메타모델 스펙 준수 여부를 확인할 수 있습니다.

---

## 📁 폴더 구조 예시

```
aas-verify/
├── main.py                 # FastAPI 앱 진입점
├── validators/             # 검증 로직 모듈
├── schemas/                # Pydantic 모델 정의
├── tests/                  # 단위 테스트
├── requirements.txt
├── vercel.json             # Vercel 배포 설정
└── README.md
```

---

## ✨ Implemented AAS Specifications

- **AAS Part 1**: Metamodel v3.0 Specification
- **AAS Part 2**: APIs v3.0 Specification (..ing)

---

## ⚙️ 기술 스택 요약

| 항목       | 내용                                  |
| ---------- | ------------------------------------- |
| 언어       | Python 3.12.6                         |
| 프레임워크 | FastAPI                               |
| 검증도구   | aas-test-engines (AAS 공식 스펙 기반) |
| 서버       | Uvicorn (ASGI)                        |
| 기타       | python-multipart (파일 업로드 지원)   |

---

## ✅ 핵심 구현 포인트 (면접용 설명)

### 1. 검증 함수의 모듈화 설계

```python
def validate_id_short(model):
    if not model.idShort:
        raise ValueError("idShort is missing.")
```

> 개별 검증 항목을 함수로 분리하여 유지보수 및 확장성 확보

---

### 2. FastAPI 기반 REST API 설계

```python
@app.post("/validate")
def validate_model(data: Submodel):
    validate_id_short(data)
    return {"message": "Validation passed"}
```

> 클라이언트가 JSON을 업로드하면, 구조 유효성 검사를 수행하고 결과 반환

---

### 3. Pydantic 모델 정의 예시

```python
class Submodel(BaseModel):
    idShort: str
    semanticId: Optional[str]
    kind: Optional[str]
```

> AAS 구조를 타입 기반으로 정의하여 JSON 입력 시 자동 유효성 검사 처리

---

## 🚀 실행 가이드

### ✅ Step 0: 환경 요구사항

- Python 3.12.6
- pip 25.0.1 이상
- OS: Windows/Linux/macOS 모두 가능
- 가상환경 권장: `venv` 또는 `virtualenv`
- 포트 8000 사용 가능해야 함 (FastAPI 기본 포트)

### ✅ Step 1: 의존성 설치

```bash
pip install -r requirements.txt
```

> 필요 라이브러리 전체 한번에 설치!

### ✅ Step 2: 서버 실행

```bash
uvicorn main:app --reload
```

접속 주소:

- http://127.0.0.1:8000
- FastAPI Docs: http://127.0.0.1:8000/docs

---

## 🌐 배포 (Vercel)

- 배포 주소: `https://your-vercel-url.vercel.app`
- FastAPI가 Vercel에 배포되어 누구나 실시간으로 API를 테스트할 수 있음

---

## 📌 향후 개선 사항

- AAS XML 포맷 지원
- 정적 프론트 페이지 추가 (검증 결과 시각화)
- 사용자 정의 검증 규칙 로딩 기능
