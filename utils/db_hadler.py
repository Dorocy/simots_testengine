from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import datetime, json

# DB 연결
def get_db_client():
    print("DB 쪽 시작 !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    uri = 'mongodb+srv://yulmoocha2001:smic12#$@testengine.sa2ir6w.mongodb.net/?retryWrites=true&w=majority&appName=testEngine'
    return MongoClient(uri, server_api = ServerApi("1"))

def extract_semantic_id(submodel: dict) -> str | None:
    keys = submodel.get("semanticId", {}).get("keys", [])
    return keys[0].get("value") if keys else None

# Schema 저장
def connect_and_insert(original_data, result_schema):
    print("Connect And Insert 왔음")
    client = get_db_client()
    binary_data = result_schema.encode("utf-8")
    print("sceham bainary ver.: ", binary_data, "\n")

    # 연결 확인
    try:
        client.admin.command("ping")
        print("저장 부분 연결 성공")

        for submodel in original_data.get("submodels", []):
            semantic_id = extract_semantic_id(submodel)
            if not semantic_id:
                continue  # 저장 불가

            schema_data = {
                "submodel_id": semantic_id,
                "version": submodel.get("version"),
                "revision": submodel.get("revision"),
                "create_at": datetime.datetime.now(),
                "uploaded_by": "IDTA",  # 나중에 동적으로 바꿔도 됨
                "schema": binary_data
            }
            print("schema data: ", schema_data)
            insert_result = client.aas.aas_schema.insert_one(schema_data)
            print("저장됨")
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
        print("Delete Result: ", client.aas.aas_schema.DeleteResult)
        return result.deleted_count > 0
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB deletion error: {str(e)}")

# Schema 조회
# def retrive_schemas():
