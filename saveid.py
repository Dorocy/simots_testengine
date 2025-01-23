import json
import zipfile
import xml.etree.ElementTree as ET
import os

def get_unique_id_filename(original_file_path: str) -> str:
    """중복되지 않는 ID 파일명을 생성 (_숫자 붙이기)"""
    base, ext = os.path.splitext(original_file_path)
    id_file_path = f"{base}_id.txt"
    counter = 1
    while os.path.exists(id_file_path):
        id_file_path = f"{base}_id_{counter}.txt"
        counter += 1
    return id_file_path

def extract_id_from_json(file_path: str) -> str:
    """JSON 파일에서 assetAdministrationShells 내부의 id 값을 추출"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if "assetAdministrationShells" in data and isinstance(data["assetAdministrationShells"], list):
            first_shell = data["assetAdministrationShells"][0]
            extracted_id = first_shell.get("id")

            if extracted_id:  # ID가 존재하는 경우만 저장
                save_id_to_file(file_path, extracted_id)
                return extracted_id
    except Exception as e:
        return f"Error extracting ID: {str(e)}"

def extract_id_from_aasx(file_path: str) -> str:
    """AASX (ZIP) 파일에서 XML 내부의 ID 추출"""
    try:
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            file_list = zip_ref.namelist()

            # XML 파일 찾기
            xml_file = next((f for f in file_list if f.endswith(".xml")), None)

            if xml_file:
                with zip_ref.open(xml_file) as f:
                    return extract_id_from_xml(f)  # 파일 객체를 넘김
    except Exception as e:
        return f"Error extracting ID: {str(e)}"


def extract_id_from_xml(file) -> str:
    """XML 파일에서 assetAdministrationShells 내부의 ID 값을 추출"""
    try:
        tree = ET.parse(file)  # ZipExtFile 또는 일반 파일 지원
        root = tree.getroot()

        namespace_uri = root.tag[root.tag.find("{")+1:root.tag.find("}")]
        namespace = {"aas": namespace_uri}

        id_element = root.find(".//aas:assetAdministrationShell/aas:id", namespace)
        if id_element is not None:
            extracted_id = id_element.text
            return extracted_id
    except Exception as e:
        return f"Error extracting ID: {str(e)}"


def save_id_to_file(file_path: str, extracted_id: str):
    """ID 값을 원본 파일과 같은 경로에 저장, 중복 방지"""
    id_file_path = get_unique_id_filename(file_path)
    with open(id_file_path, "w", encoding="utf-8") as f:
        f.write(extracted_id)