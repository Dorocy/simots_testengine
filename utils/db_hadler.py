from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import datetime

# def extract_semantic_id(submodel: dict) -> str | None:
#     keys = submodel.get("semanticId", {}).get("keys", [])
#     return keys[0].get("value") if keys else None

# def connect_and_insert(result_schema):
#     uri = 'mongodb+srv://keti:smic12#$@aas.dsisnmh.mongodb.net/?retryWrites=true&w=majority&appName=aas'
#     # MongoDB 클라이언트 생성 및 연결
#     client = MongoClient(uri, server_api=ServerApi("1"))
#     binary_data = result_schema.encode("utf-8")
#     # 연결 확인
#     # try:
#     #     print(3333)
#     #     client.admin.command("ping")
#     #     print("Pinged your deployment. You successfully connected to MongoDB!")
#     try:
#         print("STEP 2 - MongoDB 연결 시도")
#         client.admin.command("ping")
#         print("MongoDB 연결 성공")

#         # 이진 데이터 삽입
#         # insert_result = client.aas.aas_schema.insert_one({"binary_data": binary_data})
#         # print(f"Data inserted with _id: {insert_result.inserted_id}")

#         for submodel in result_schema.get("submodels", []):
#             semantic_id = extract_semantic_id(submodel)
#             if not semantic_id:
#                 continue  # 저장 불가

#             schema_data = {
#                 "submodel_id": semantic_id,
#                 "version": submodel.get("version"),
#                 "revision": submodel.get("revision"),
#                 "create_at": datetime.now(),
#                 "uploaded_by": "IDTA",  # 나중에 동적으로 바꿔도 됨
#                 "schema": binary_data
#             }

#             insert_result = client.aas.aas_schema.insert_one(schema_data)
#         return insert_result

#     except Exception as e:
#         print(f"Error occurred: {e}")


def connect_and_insert(original_data, result_schema):
    print("STEP 1 - connect_and_insert() 호출됨")

    uri = 'mongodb+srv://keti:smic12#$@testengine.sa2ir6w.mongodb.net/?retryWrites=true&w=majority&appName=testEngine'
    client = MongoClient(uri, server_api=ServerApi("1"))
    binary_data = result_schema.encode("utf-8")
    print(binary_data)

    try:
        print("STEP 2 - MongoDB 연결 시도")
        client.admin.command("ping")
        print("MongoDB 연결 성공")
        

        for submodel in original_data.get("submodels", []):
            semantic_id = extract_semantic_id(submodel)
            if not semantic_id:
                continue

            schema_data = {
                "submodel_id": semantic_id,
                "version": submodel.get("version"),
                "revision": submodel.get("revision"),
                "create_at": datetime.datetime.now(),
                "uploaded_by": "IDTA",
                "schema": binary_data  # 여기서 dict로 넣음 (MongoDB는 dict 저장 가능)
            }

            insert_result = client.aas.aas_schema.insert_one({"schema":binary_data})
            print(f"✅ Inserted _id: {insert_result.inserted_id}")

        return insert_result

    except Exception as e:
        print(f"Error occurred while inserting: {e}")
        return False