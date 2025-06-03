from http.client import HTTPException
from fastapi import HTTPException
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import datetime, json, re

# DB 연결
def get_db_client():
    uri = 'mongodb+srv://yulmoocha2001:smic12#$@testengine.sa2ir6w.mongodb.net/?retryWrites=true&w=majority&appName=testEngine'
    return MongoClient(uri, server_api = ServerApi("1"))

def extract_semantic_id(submodel: dict) -> str:
    keys = submodel.get("semanticId", {}).get("keys", [])
    return keys[0].get("value") if keys else None

def extract_version_revision(semantic_id):
    match = re.search(r"(\d+)/(\d+)", semantic_id)
    if match:
        version, revision = match.groups()
        return version, revision
    else:
        return None, None

# Schema 저장
def connect_and_insert(original_data, result_schema):
    client = get_db_client()
    binary_data = result_schema.encode("utf-8")

    # 연결 확인
    try:
        client.admin.command("ping")

        for submodel in original_data.get("submodels", []):
            semantic_id = extract_semantic_id(submodel)
            if not semantic_id:
                continue  # 저장 불가

            version, revision = extract_version_revision(semantic_id)

            schema_data = {
                "submodel_id": semantic_id,
                "version": version,
                "revision": revision,
                "create_at": datetime.datetime.now(),
                # "create_at": datetime.datetime.now.strftime("%Y-%m-%d %H:%M:%S"),
                "uploaded_by": "IDTA",  # 나중에 동적으로 바꿔도 됨
                "schema": binary_data
            }
            insert_result = client.aas.aas_schema.insert_one(schema_data)
            print(f"Data inserted with _id: {insert_result.inserted_id}")
        return insert_result

    except Exception as e:
        print(f"Error occurred: {e}")

# Schema 삭제
def delete_schema_by_semantic_id(semantic_id: str) -> bool:
    print("삭제 부분 연결 성공")
    client = get_db_client()
    try:
        client.admin.command("ping")
        result = client.aas.aas_schema.delete_one({"submodel_id": semantic_id})
        # print("Delete Result: ", client.aas.aas_schema.DeleteResult)
        return result.deleted_count > 0
    except Exception as e:
        print(f"Error occurred: {e}")

# Schema 조회
def retrieve_schemas():
    client = get_db_client()
    try:
        client.admin.command("ping")
        collection = client.aas.aas_schema
        documents = collection.find({}, {"submodel_id": 1, "_id": 0})

        submodel_ids = [doc["submodel_id"] for doc in documents]
        return submodel_ids

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB check schema error: {e}")
    
    
def search_schema_in_all_fields(value: str):
    client = get_db_client()
    try:
        client.admin.command("ping")
        collection = client.aas.aas_schema
        # 모든 주요 필드에 대해 or 조건으로 검색
        query = {
            "$or": [
                {"submodel_id": value},
                {"uploaded_by": value},
                {"version": value},
                {"revision": value}
            ]
        }
        document = collection.find(query)
        return list(document)
    except Exception as e:
        print(f"[DB Error] {e}")
        return None
# def export_schema_to_py_file(submodel_id: str, file_path: str = "schema_files/test_schema.py") -> bool:
#     client = get_db_client()
#     try:
#         client.admin.command("ping")
#         collection = client.aas.aas_schema
#         document = collection.find_one({"submodel_id": submodel_id})
#         if not document:
#             print(f"No schema found for submodel_id: {submodel_id}")
#             return False
#         binary_data = document["schema"]
#         decoded_schema = binary_data.decode("utf-8")
#         with open(file_path, "w", encoding="utf-8") as f:
#             f.write("from enum import Enum\n"
#                     "from typing import Optional, List\n"
#                     "from dataclasses import dataclass, field\n"
#                     "from aas_test_engines.test_cases.v3_0.parse_submodel import LangString\n"
#                     "from aas_test_engines.test_cases.v3_0.submodel_templates import template\n")
#             f.write(decoded_schema)
#         print(f"Schema for {submodel_id} written to {file_path}")
#         return True
#     except Exception as e:
#         print(f"[Export Error] {e}")
#         return False