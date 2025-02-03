import os
import json
import zipfile
import xml.etree.ElementTree as ET
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
    
    # ID 추출 및 저장 (JSON, XML, AASX 파일만 해당)
    ext = os.path.splitext(file.filename)[1].lower()
    if ext in SUPPORTED_EXTENSIONS:
        extract_and_save_id(file_path)
    
    return file_path

def get_unique_id_filename(original_file_path: str) -> str:
    """중복되지 않는 ID 파일명을 생성 (_숫자 붙이기)"""
    base, ext = os.path.splitext(original_file_path)
    id_file_path = f"{base}_id.txt"
    counter = 2
    while os.path.exists(id_file_path):
        id_file_path = f"{base}_id_{counter}.txt"
        counter += 1
    return id_file_path

def extract_and_save_id(file_path: str):
    """파일 형식에 따라 ID를 추출하고 저장"""
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".json":
        extracted_id = extract_id_from_json(file_path)
    elif ext == ".xml":
        extracted_id = extract_id_from_xml(file_path)
    elif ext == ".aasx":
        extracted_id = extract_id_from_aasx(file_path)
    else:
        return  # 지원되지 않는 형식
    
    if extracted_id:
        save_id_to_file(file_path, extracted_id)

def save_id_to_file(file_path: str, extracted_id: str):
    """ID 값을 원본 파일과 같은 경로에 저장, 중복 방지"""
    base, _ = os.path.splitext(file_path)
    id_file_path = f"{base}_id.txt"
    counter = 2
    while os.path.exists(id_file_path):
        id_file_path = f"{base}_id_{counter}.txt"
        counter += 1
    with open(id_file_path, "w", encoding="utf-8") as f:
        f.write(extracted_id)

def extract_id_from_json(file_path: str) -> str:
    """JSON 파일에서 assetAdministrationShells 내부의 id 값을 추출"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if "assetAdministrationShells" in data and isinstance(data["assetAdministrationShells"], list):
            first_shell = data["assetAdministrationShells"][0]
            return first_shell.get("id")
    except Exception as e:
        return f"Error extracting ID: {str(e)}"
    return None

def extract_id_from_aasx(file_path: str) -> str:
    """AASX (ZIP) 파일에서 XML 내부의 ID 추출"""
    try:
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            file_list = zip_ref.namelist()
            xml_file = next((f for f in file_list if f.endswith(".xml")), None)
            if xml_file:
                with zip_ref.open(xml_file) as f:
                    return extract_id_from_xml(f)
    except Exception as e:
        return f"Error extracting ID: {str(e)}"
    return None

def extract_id_from_xml(file) -> str:
    """XML 파일에서 assetAdministrationShells 내부의 ID 값을 추출"""
    try:
        tree = ET.parse(file)
        root = tree.getroot()
        namespace_uri = root.tag[root.tag.find("{")+1:root.tag.find("}")]
        namespace = {"aas": namespace_uri}
        id_element = root.find(".//aas:assetAdministrationShell/aas:id", namespace)
        if id_element is not None:
            return id_element.text
    except Exception as e:
        return f"Error extracting ID: {str(e)}"
    return None