from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import PlainTextResponse
import os
import save
import run

app = FastAPI()

existing_names = {}  # 파일 이름 중복 관리를 위한 딕셔너리 추가

def process_verification(file: UploadFile) -> dict:
    """파일 저장, ID 추출 및 AAS Test Engine 실행 후 결과 반환"""
    _, file_ext = os.path.splitext(file.filename)
    
    if file_ext not in save.SUPPORTED_EXTENSIONS:
        return {"status": "Unknown type", "details": f"지원하지 않는 파일 형식입니다. 허용된 확장자: {save.SUPPORTED_EXTENSIONS}"}

    try:
        file_path = save.save_uploaded_file(file, existing_names)  # 기존 파일명 관리 딕셔너리 전달

        # ID 추출 및 저장
        extracted_id = None
        if file_ext == ".json":
            extracted_id = save.extract_id_from_json(file_path)
        elif file_ext == ".xml":
            extracted_id = save.extract_id_from_xml(file_path)
        elif file_ext == ".aasx":
            extracted_id = save.extract_id_from_aasx(file_path)

        # 검증 실행
        result = run.run_test_engine(file_path, file_ext)

        response = {"file": os.path.basename(file_path), "verification": result}
        if extracted_id:
            response["extracted_id"] = extracted_id

        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"처리 중 오류가 발생: {str(e)}")

# 출력 TXT 형식으로 변경
def format_response_as_txt(response: dict) -> str:
    """딕셔너리를 TXT 형식으로 변환"""
    txt_output = []
    for key, value in response.items():
        if isinstance(value, dict):
            txt_output.append(f"{key}:")
            for sub_key, sub_value in value.items():
                txt_output.append(f"  {sub_key}: {sub_value}")
        else:
            txt_output.append(f"{key}: {value}")
    return "\n".join(txt_output)

# 공통된 API 엔드포인트
@app.post("/verification_0221/")
async def verification(file: UploadFile = File(...)):
    response = process_verification(file)
    return PlainTextResponse(content=format_response_as_txt(response), media_type="text/plain")

@app.post("/verification_SM_0124/")
async def verification_sm(file: UploadFile = File(...)):
    response = process_verification(file)
    return PlainTextResponse(content=format_response_as_txt(response), media_type="text/plain")

@app.post("/verification_CD_0124/")
async def verification_cd(file: UploadFile = File(...)):
    response = process_verification(file)
    return PlainTextResponse(content=format_response_as_txt(response), media_type="text/plain")
