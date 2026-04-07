import os, re, tempfile, shutil
import xml.etree.ElementTree as ET
from fastapi import UploadFile

UPLOAD_DIR = "uploaded_files"
SUPPORTED_EXTENSIONS = {".json", ".xml", ".aasx"}
def remove_ansi_codes(text):
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    return ansi_escape.sub("", text)

def save_temp_file(file: UploadFile)->str:
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1])
    try:
        shutil.copyfileobj(file.file, tmp)
        return tmp.name
    finally:
        tmp.close()
