import os
from fastapi import UploadFile

UPLOAD_DIR = "uploaded_files"
SUPPORTED_EXTENSIONS = {".json", ".xml", ".aasx"}

def get_unique_filename(directory: str, filename: str) -> str:
    """중복되지 않는 파일명을 생성 (_숫자 붙이기)"""
    base, ext = os.path.splitext(filename)
    counter = 2
    new_filename = filename
    while os.path.exists(os.path.join(directory, new_filename)):
        new_filename = f"{base}_{counter}{ext}"
        counter += 1
    return os.path.join(directory, new_filename)

def save_uploaded_file(file: UploadFile) -> str:
    """업로드된 파일을 저장하고 중복 시 _숫자 추가"""
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    file_path = get_unique_filename(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        buffer.write(file.file.read())

    return file_path