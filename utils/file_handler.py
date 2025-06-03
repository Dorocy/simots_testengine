import os, re, json, zipfile
import xml.etree.ElementTree as ET
from fastapi import UploadFile

UPLOAD_DIR = "uploaded_files"
SUPPORTED_EXTENSIONS = {".json", ".xml", ".aasx"}


def remove_ansi_codes(text):
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    return ansi_escape.sub("", text)


def get_grouped_filename(
    directory: str, base_name: str, ext: str, existing_names: dict
) -> str:
    # 같은 base_name 그룹 내에서 중복되지 않는 파일명을 생성
    if base_name not in existing_names:
        existing_names[base_name] = 1
        new_filename = f"{base_name}{ext}"
    else:
        existing_names[base_name] += 1
        new_filename = f"{base_name}_{existing_names[base_name]}{ext}"

    return os.path.join(directory, new_filename)


def save_uploaded_file(file: UploadFile, existing_names: dict) -> str:
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    base_name, ext = os.path.splitext(file.filename)
    file_path = get_grouped_filename(UPLOAD_DIR, base_name, ext, existing_names)

    with open(file_path, "wb") as buffer:
        buffer.write(file.file.read())  # 파일 저장

    # ID 추출 및 저장 (JSON, XML, AASX 파일만 해당)
    if ext.lower() in SUPPORTED_EXTENSIONS:
        extract_and_save_id(file_path, existing_names)

    return file_path


def extract_and_save_id(file_path: str, existing_names: dict):
    ext = os.path.splitext(file_path)[1].lower()
    extracted_id = None
    if ext == ".json":
        extracted_id = extract_id_from_json(file_path)
    elif ext == ".xml":
        extracted_id = extract_id_from_xml(file_path)
    elif ext == ".aasx":
        extracted_id = extract_id_from_aasx(file_path)

    if extracted_id:
        save_id_to_file(file_path, extracted_id, existing_names)


def save_id_to_file(file_path: str, extracted_id: str, existing_names: dict):
    base_name, _ = os.path.splitext(os.path.basename(file_path))
    id_file_path = get_grouped_filename(
        UPLOAD_DIR, f"{base_name}_id", ".txt", existing_names
    )

    with open(id_file_path, "w", encoding="utf-8") as f:
        f.write(extracted_id)


def extract_id_from_json(file_path: str) -> str:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if "assetAdministrationShells" in data and isinstance(
            data["assetAdministrationShells"], list
        ):
            first_shell = data["assetAdministrationShells"][0]
            return first_shell.get("id")
    except Exception as e:
        return f"Error extracting ID: {str(e)}"
    return None


def extract_id_from_aasx(file_path: str) -> str:
    try:
        with zipfile.ZipFile(file_path, "r") as zip_ref:
            file_list = zip_ref.namelist()
            xml_file = next((f for f in file_list if f.endswith(".xml")), None)
            if xml_file:
                with zip_ref.open(xml_file) as f:
                    return extract_id_from_xml(f)
    except Exception as e:
        return f"Error extracting ID: {str(e)}"
    return None


def extract_id_from_xml(file) -> str:
    try:
        if isinstance(file, str):
            tree = ET.parse(file)
        else:
            tree = ET.parse(file)

        root = tree.getroot()
        namespace_uri = root.tag[root.tag.find("{") + 1 : root.tag.find("}")]
        namespace = {"aas": namespace_uri}
        id_element = root.find(".//aas:assetAdministrationShell/aas:id", namespace)
        if id_element is not None:
            return id_element.text
    except Exception as e:
        return f"Error extracting ID: {str(e)}"
    return None
