from http.client import HTTPException
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import datetime, json, re
from api.response_handler import ErrorCode, error_response, success_response
from typing import List

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


def connect_and_insert(original_data, result_schema):
    client = get_db_client()
    binary_data = result_schema.encode("utf-8")

    try:
        submodels = original_data.get("submodels", [])
        if not submodels:
            return error_response(
                400,
                ErrorCode.SUBMODEL_NOT_FOUND
                )

        semantic_id = extract_semantic_id(submodels[0])
        if not semantic_id:
            return error_response(
                400,
                ErrorCode.MISSING_PARAMETER,
                "semantic_id not found"
                )

        existing_submodel_ids = retrieve_schemas()

        if semantic_id not in existing_submodel_ids:
            version, revision = extract_version_revision(semantic_id)
            print(existing_submodel_ids)

            schema_data = {
                "submodel_id": semantic_id,
                "version": version,
                "revision": revision,
                "create_at": datetime.datetime.now(),
                "uploaded_by": "IDTA",
                "schema": binary_data
            }

            insert_result = client.aas.aas_schema.insert_one(schema_data)
            print(f"Data inserted with _id: {insert_result.inserted_id}")
            return success_response(
                "Schema API",
                "success",
                f"Schema '{semantic_id}' is extracted and stored."
                )

        else:
            return error_response(
                400,
                ErrorCode.ALREADY_EXISTS_SCHEMA,
                f"Schema '{semantic_id}' is already exists."
                )

    except Exception as e:
        return error_response(
            500,
            ErrorCode.DB_ERROR,
            str(e)
            )

# Schema 삭제
def delete_schema_by_semantic_id(semantic_id: str) -> bool:
    client = get_db_client()
    try:
        result = client.aas.aas_schema.delete_one({"submodel_id": semantic_id})
        return result.deleted_count > 0
    except Exception as e:
        return error_response(
            500,
            ErrorCode.DB_ERROR,
            str(e)
            )

# Schema 조회
def retrieve_schemas():
    client = get_db_client()
    try:
        collection = client.aas.aas_schema
        documents = collection.find({}, {"submodel_id": 1, "_id": 0})

        submodel_ids = [doc["submodel_id"] for doc in documents]
        return submodel_ids

    except Exception as e:
        return error_response(
            500,
            ErrorCode.DB_ERROR,
            str(e)
            )


def search_schema_with_semantic_id(semanticId: str):
    client = get_db_client()
    try:
        collection = client.aas.aas_schema

        query = {"submodel_id": semanticId}
        document = collection.find_one(query)

        return document
    except Exception as e:
        return error_response(
            500,
            ErrorCode.DB_ERROR,
            str(e)
            )


def search_schema_with_uploaded_by(uploadedBy: str):

    client = get_db_client()
    try:
        collection = client.aas.aas_schema

        query = {"uploaded_by": uploadedBy}
        documents = collection.find(query)

        return list(documents)

    except Exception as e:
        return error_response(
            500,
            ErrorCode.DB_ERROR,
            str(e)
            )


def search_schema_in_all_fields(semanticId: str, uploadedBy: str):
    client = get_db_client()
    try:
        collection = client.aas.aas_schema

        query = {"submodel_id": semanticId,
                "uploaded_by": uploadedBy}
        document = collection.find_one(query)

        return document

    except Exception as e:
        return error_response(
            500,
            ErrorCode.DB_ERROR,
            str(e)
            )


def export_schema_to_py_file(submodel_ids: List[str], file_path: str = "schema_files/test_schema.py") -> bool:
    client = get_db_client()
    try:
        collection = client.aas.aas_schema
        # 헤더
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("from enum import Enum\n"
                    "from typing import Optional, List\n"
                    "from dataclasses import dataclass, field\n"
                    "from aas_test_engines.test_cases.v3_0.parse_submodel import LangString\n"
                    "from aas_test_engines.test_cases.v3_0.submodel_templates import template\n\n")
            # RefType, File, Blob 등 정의하고 import하기

        for submodel_id in submodel_ids:
            document = collection.find_one({"submodel_id": submodel_id})
            if not document:
                print(f"[Warning] No schema found for submodel_id: {submodel_id}")
                continue

            binary_data = document["schema"]
            decoded_schema = binary_data.decode("utf-8")

            with open(file_path, "a", encoding="utf-8") as f:
                f.write(decoded_schema + "\n\n")

            print(f"Schema for {submodel_id} appended to {file_path}")

        return True

    except Exception as e:
        return error_response(
            500,
            ErrorCode.DB_ERROR,
            str(e)
            )


def alter_schema_put(semantic_id: str, binary_data: bytes, data: dict):
    client = get_db_client()
    collection = client.aas.aas_schema

    version, revision = extract_version_revision(semantic_id)

    new_document = {
        "submodel_id": semantic_id,
        "version": version,
        "revision": revision,
        "create_at": datetime.datetime.now(),
        "uploaded_by": "IDTA",
        "schema": binary_data
    }

    result = collection.replace_one(
        {"submodel_id": semantic_id},
        new_document,
        upsert=True  # 없으면 새로 만들기
    )
    return result.modified_count > 0 or result.upserted_id is not None


def alter_schema_patch(semantic_id: str, binary_data: bytes):
    client = get_db_client()
    collection = client.aas.aas_schema

    existing = collection.find_one({"submodel_id": semantic_id})
    if existing and existing.get("schema") == binary_data:
        return "same schema"

    result = collection.update_one(
        {"submodel_id": semantic_id},
        {"$set":
            {
                "time": datetime.datetime.now(),
                "schema": binary_data
            }}
    )
    return result.modified_count > 0
