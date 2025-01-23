from fastapi import FastAPI, UploadFile, File, HTTPException
import os
import saveid
import savefile
import run

app = FastAPI()

@app.post("/verification_rc2/")
async def verification(file: UploadFile = File(...)):
    """파일 업로드 후 ID 추출 및 AAS Test Engine 실행"""
    _, file_ext = os.path.splitext(file.filename)
    
    if file_ext not in savefile.SUPPORTED_EXTENSIONS:
        return {"status": "Unknown type", "details": f"지원하지 않는 파일 형식입니다. 허용된 확장자: {savefile.SUPPORTED_EXTENSIONS}"}

    try:
        file_path = savefile.save_uploaded_file(file)

        # ID 추출 및 저장
        extracted_id = None
        if file_ext == ".json":
            extracted_id = saveid.extract_id_from_json(file_path)
        elif file_ext == ".xml":
            extracted_id = saveid.extract_id_from_xml(file_path)
        elif file_ext == ".aasx":
            extracted_id = saveid.extract_id_from_aasx(file_path)

        # 검증 실행
        result = run.run_test_engine_returncode(file_path, file_ext)

        response = {"file": file_path, "verification": result}
        if extracted_id:
            response["extracted_id"] = extracted_id
            response["id_file_saved_at"] = saveid.get_unique_id_filename(file_path)

        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"처리 중 오류가 발생했습니다: {str(e)}")