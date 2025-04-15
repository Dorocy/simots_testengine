from pymongo import MongoClient
from pymongo.server_api import ServerApi


def connect_and_insert(uri: str, data):
    # MongoDB 클라이언트 생성 및 연결
    client = MongoClient(uri, server_api=ServerApi("1"))
    binary_data = data.encode("utf-8")
    # 연결 확인
    try:
        client.admin.command("ping")
        print("Pinged your deployment. You successfully connected to MongoDB!")

        # 이진 데이터 삽입
        insert_result = client.aas.aas_schema.insert_one({"binary_data": binary_data})
        print(f"Data inserted with _id: {insert_result.inserted_id}")

    except Exception as e:
        print(f"Error occurred: {e}")
