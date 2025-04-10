from utils.error_handler import error_response, ErrorCode, setup_exception_handlers
from fastapi import FastAPI, UploadFile, File, HTTPException, Request
# from fastapi.responses import PlainTextResponse
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
# from starlette.responses import JSONResponse
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY
import aas_core3.types as aas_types
import aas_core3.jsonization as aas_jsonization
from export_schema import process_submodel_elements, to_pascal_case, to_snake_case, extract_values, get_schema_result
from aas_test_engines.test_cases.v3_0.model import Referable
import io
import re
import json
import sys

import save
import run
import run_submodel




from routes.verification import router as verification_router


app = FastAPI()
app.include_router(verification_router, prefix="/verification")
setup_exception_handlers(app)

#사용자 입력에서 나오는 에러 (400처리, 잘못된 파라미터)
# @app.exception_handler(HTTPException)
# async def http_exception_handler(request: Request, exc: HTTPException):
#     error_code = ErrorCode.INVALID_PARAMETER if exc.status_code == 400 else ErrorCode.INTERNAL_SERVER_ERROR
#     return error_response(exc.status_code, error_code, exc.detail)

# # 파라미터 입력문제
# @app.exception_handler(RequestValidationError)
# async def validation_exception_handler(request: Request, exc: RequestValidationError):
#     return error_response(
#         HTTP_422_UNPROCESSABLE_ENTITY,
#         ErrorCode.INVALID_PARAMETER,
#     )

# # 코드로직에서 나오는 에러(500으로처리)
# @app.exception_handler(Exception)
# async def unhandled_exception_handler(request: Request, exc: Exception):
#     return error_response(500, ErrorCode.INTERNAL_SERVER_ERROR)


#원하는 형태 파일 지원이 아님.
@app.exception_handler(UnicodeDecodeError)
async def unicode_decode_error_handler(request: Request, exc: UnicodeDecodeError):
    return error_response(
        status_code=400,
        error_code=ErrorCode.INVALID_FILE_FORMAT,
    )


existing_names = {}



# def remove_ansi_codes(text):
#     ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
#     return ansi_escape.sub('', text)


# def process_verification(file: UploadFile) -> dict:
#     _, file_ext = os.path.splitext(file.filename)
    
#     if file_ext not in save.SUPPORTED_EXTENSIONS:
#         return {"status": "Unknown type", "details": f"지원하지 않는 파일 형식입니다. 허용된 확장자: {save.SUPPORTED_EXTENSIONS}"}

#     try:
#         file_path = save.save_uploaded_file(file, existing_names) 

#         extracted_id = None
#         if file_ext == ".json":
#             extracted_id = save.extract_id_from_json(file_path)
#         elif file_ext == ".xml":
#             extracted_id = save.extract_id_from_xml(file_path)
#         elif file_ext == ".aasx":
#             extracted_id = save.extract_id_from_aasx(file_path)

#         result = run.run_test_engine(file_path, file_ext)
#         print('결과는',result)

#         # response = {"file": os.path.basename(file_path), "verification": result}
#         if extracted_id:
#             response["extracted_id"] = extracted_id

#         return result
#     except ValueError as ve:
#         raise HTTPException(status_code=400, detail=str(ve))
#     except RuntimeError as re:
#         raise HTTPException(status_code=500, detail=str(re))
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"처리 중 오류 발생: {str(e)}")


# #SME의 qualifier 검사
# def validate_qualifiers(data: dict):
    
#     for submodel in data["submodels"]:
#         submodel_elements = submodel.get("submodelElements", [])
        
#         if not isinstance(submodel_elements, list):
#             continue  

#         for element in submodel_elements:
#             element_id = element.get("idShort", "Unknown")
#             qualifiers = element.get("qualifiers", [])
            
#             for qualifier in qualifiers:
#                 kind = qualifier.get("kind")
#                 q_type = qualifier.get("type")
#                 print(f"DEBUG: Checking {element_id} -> kind: {kind}, type: {q_type}")
                
#                 if kind and kind != "TemplateQualifier":
#                     return error_response(
#                         400, ErrorCode.INVALID_QUALIFIER_KIND,
#                         f"element '{element_id}'의 qualifier.kind는 'TemplateQualifier'여야 합니다."
#                     )

#                 if q_type and q_type != "SMT_Cardinality":
#                     return error_response(
#                         400, ErrorCode.INVALID_QUALIFIER_TYPE,
#                         f"element '{element_id}'의 qualifier.type은 'SMT_Cardinality'여야 합니다."
#                     )


#Metamodel 검사(AAS Instance/Template, Submodel Template)
# @app.post("/verification/metamodel")
# async def verification(file: UploadFile = File(...)):
#     response = process_verification(file)
#     return JSONResponse(content=response)


#Submodel Template 검증 스키마에 따른 Instance 부합여부 검증
# @app.post("/verification/instance")
# async def verification_sm(file: UploadFile = File(...)):
#     file_content = await file.read()
#     json_data = json.loads(file_content.decode("utf-8"))

#     old_stdout = sys.stdout
#     sys.stdout = io.StringIO()

#     run_submodel.check_submodel_templates(json_data)
#     output = sys.stdout.getvalue()
#     sys.stdout = old_stdout

#     cleaned_output = remove_ansi_codes(output).strip()
#     formatted_output = cleaned_output.splitlines()

#     return JSONResponse(content= formatted_output)


#submodel의 kind 체크를 통해 template 이어야 스키마 생성가능
# def check_submodel_kind(data:json):
#     #submodel을 라이브러리의 타입에 맞게 변화하는 부분 확인차 에러 처리
#     try:
#         submodel = aas_jsonization.submodel_from_jsonable(data)

#     except Exception as e:
#         return error_response(
#             400, ErrorCode.INVALID_FILE_FORMAT,
#         )

#     if submodel.kind.value == "Instance":
#         return error_response(
#             400, ErrorCode.INVALID_SUBMODEL_KIND
#         )

#     return None


#Submodel Template 스키마 추출
# @app.post("/verification/schema")
# async def export_submodel_schema(file: UploadFile = File(...)):
#     contents = await file.read()
#     data = json.loads(contents)

#     for submodel in data.get("submodels", []):
#         submodel_type_error = check_submodel_kind(submodel)
#         if submodel_type_error:
#             return submodel_type_error
#         semantic_id_keys = submodel.get("semanticId", {}).get("keys", [])
#         if semantic_id_keys and isinstance(semantic_id_keys, list):
#             first_key_value = semantic_id_keys[0].get("value", "")
#             if first_key_value.startswith("https://admin-shell.io/"):
#                 return get_schema_result(data)

#     validate_qualifiers(data)

#     result = get_schema_result(data)
#     return result