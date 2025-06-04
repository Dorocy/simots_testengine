import json, io, sys, os, utils.file_handler as file_handler, test_engine_run, run_submodel
from fastapi import HTTPException, Query
from fastapi.responses import JSONResponse
from utils.file_handler import remove_ansi_codes
from utils.response_handler import ErrorCode, error_response, success_response
from utils.db_hadler import (
    delete_schema_by_semantic_id,
    retrieve_schemas,
    search_schema_in_all_fields,
    search_schema_with_semantic_id,
    search_schema_with_uploaded_by
    )
import aas_core3.jsonization as aas_jsonization
from export_schema import get_schema_result


existing_names = {}


async def verification_schema(file):
    contents = await file.read()
    data = json.loads(contents)

    for submodel in data.get("submodels", []):
        submodel_type_error = check_submodel_kind(submodel)
        if submodel_type_error:
            return submodel_type_error
        semantic_id_keys = submodel.get("semanticId", {}).get("keys", [])
        if semantic_id_keys and isinstance(semantic_id_keys, list):
            first_key_value = semantic_id_keys[0].get("value", "")
            if first_key_value.startswith("https://admin-shell.io/"):
                return get_schema_result(data)
    validate_qualifiers(data)
    result = get_schema_result(data)
    
    return result

async def verification_instance(file):
    file_content = await file.read()
    try:
        json_data = json.loads(file_content.decode("utf-8"))
    except Exception:
        error_response("json 파싱 에러")

    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    run_submodel.check_submodel_templates(json_data)
    output = sys.stdout.getvalue()
    sys.stdout = old_stdout

    cleaned_output = remove_ansi_codes(output).strip().splitlines()

    return JSONResponse(content=cleaned_output)


async def verification_metamodel(file):
    response = process_verification(file)
    return response
    
# async def verification_instance(file):
#     file_content = await file.read()
#     try:
#         json_data = json.loads(file_content.decode("utf-8"))

#         old_stdout = sys.stdout
#         sys.stdout = io.StringIO()
#         run_submodel.check_submodel_templates(json_data)
#         output = sys.stdout.getvalue()
#         sys.stdout = old_stdout

#         cleaned_output = remove_ansi_codes(output).strip().splitlines()
#     except Exception:
#             error_response(status_code=400, error_code=ErrorCode.INVALID_JSON_FORMAT)
#     return JSONResponse(content=cleaned_output)


async def verification_metamodel(file):
    response = process_verification(file)
    return response


def process_verification(file) -> dict:
    _, file_ext = os.path.splitext(file.filename)

    # 파일 형태 예외처리 error_handler에서 공통 함수 사용해서 처리
    if file_ext not in file_handler.SUPPORTED_EXTENSIONS:
        return error_response(status_code=400, error_code=ErrorCode.INVALID_FILE_FORMAT)

    try:
        file_path = file_handler.save_uploaded_file(file, existing_names)

        extracted_id = None
        if file_ext == ".json":
            extracted_id = file_handler.extract_id_from_json(file_path)
        elif file_ext == ".xml":
            extracted_id = file_handler.extract_id_from_xml(file_path)
        elif file_ext == ".aasx":
            extracted_id = file_handler.extract_id_from_aasx(file_path)

        result = test_engine_run.run_test_engine(file_path, file_ext)

        response = {"file": os.path.basename(file_path), 
                    "verification": result}
        if extracted_id:
            response["extracted_id"] = extracted_id

        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except RuntimeError as re:
        raise HTTPException(status_code=500, detail=str(re))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"처리 중 오류 발생: {str(e)}")


async def verification_metamodel(file):
    response = process_verification(file)
    return response


async def verification_schema(file):
    contents = await file.read()
    data = json.loads(contents)

    for submodel in data.get("submodels", []):
        submodel_type_error = check_submodel_kind(submodel)

        if submodel_type_error:
            return submodel_type_error

        semantic_id_keys = submodel.get("semanticId", {}).get("keys", [])
        if semantic_id_keys and isinstance(semantic_id_keys, list):
            semantic_id = semantic_id_keys[0].get("value", "")
            if semantic_id.startswith("https://admin-shell.io/"):
                return get_schema_result(data)
            elif semantic_id in ['0173-1#01-AHF578#001', '0173-1#01-AHX837#002']:
                return get_schema_result(data)
            else:
                validate_result = validate_qualifiers(data)
                if validate_result is not True:
                    return validate_result
    result = get_schema_result(data)
    return result


def check_submodel_kind(data: json):
    # submodel을 라이브러리의 타입에 맞게 변화하는 부분 확인차 에러 처리
    try:
        submodel = aas_jsonization.submodel_from_jsonable(data)

    except Exception:
        return error_response(
            400,
            ErrorCode.INVALID_FILE_FORMAT,
        )

    if submodel.kind.value != "Template":
        return error_response(400, ErrorCode.INVALID_SUBMODEL_KIND)
    return None


def validate_qualifiers(data: json):
    try:
        environment = aas_jsonization.environment_from_jsonable(data)
    except Exception:
        return error_response(
            400,
            ErrorCode.INVALID_FILE_FORMAT,
        )

    for submodel in environment.submodels:
        for element in submodel.submodel_elements or []:  # submodelElement가 없을 경우 []
            element_id = element.id_short or "Unknown"  # idShort가 없으면 Unknown
            for qualifier in element.qualifiers or []:  # qualifier가 없으면 []
                q_kind = qualifier.kind.value
                print(q_kind)
                q_type = qualifier.type

                print(f"DEBUG: Checking {element_id} -> kind: {q_kind}, type: {q_type}")

                if q_kind != "TemplateQualifier":
                    return error_response(
                        400,
                        ErrorCode.INVALID_QUALIFIER_KIND,
                        f"element '{element_id}'의 qualifier.kind는 'TemplateQualifier'여야 합니다.",
                    )

                if q_type != "SMT_Cardinality":
                    return error_response(
                        400,
                        ErrorCode.INVALID_QUALIFIER_TYPE,
                        f"element '{element_id}'의 qualifier.type은 'SMT_Cardinality'여야 합니다.",
                    )
    return True


SUCCESS_COLOR_CODE = "\x1b[92m"
FAILED_COLOR_CODE = "\x1b[91m"

async def verification_instance(file):
    file_content = await file.read()
    try:
        json_data = json.loads(file_content.decode("utf-8"))
    except Exception:
        print("파싱 에러")
        return ErrorCode.INVALID_JSON_FORMAT

    # n_submodel.check_submodel_templates(json_data)
    # print(test)
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    run_submodel.check_submodel_templates(json_data)
    output = sys.stdout.getvalue()
    sys.stdout = old_stdout

    cleaned_output = remove_ansi_codes(output).strip().splitlines()

    success_list = []
    failed_list = []

    for line in output.splitlines():
        if "Check submodel" in line:
            if SUCCESS_COLOR_CODE in line:
                clean_line = remove_ansi_codes(line).strip()
                success_list.append(clean_line)
                return success_response("Instance API", "success", cleaned_output)
            elif FAILED_COLOR_CODE in line:
                clean_line = remove_ansi_codes(line).strip()
                failed_list.append(clean_line)
                return success_response("Instance API", "failed", cleaned_output)


async def delete_schema(semanticId: str = Query(..., description="SemanticId of the schema to delete")):
    success = delete_schema_by_semantic_id(semanticId)
    if not success:
        raise HTTPException(status_code=404, detail="Schema not found in database.")
    return {"message": f"Schema for semanticId '{semanticId}' has been deleted from DB."}


async def schemas_list():
    try:
        submodel_ids = retrieve_schemas()
        return submodel_ids
    except Exception:
        return HTTPException(status_code=404, detail="No schemas found in database.")


async def search_schema_by_semamtic_id(value: str):
    try:
        result = search_schema_with_semantic_id(value)

        if not result:
            return {
                "message": f"'{value}'가(이) 없습니다."
            }

        data = {
            "submodel_id": result.get("submodel_id"),
            "version": result.get("version"),
            "revision": result.get("revision"),
            # "create_at": result.get("create_at"),
            "uploaded_by": result.get("uploaded_by")
        }

        return {
            "message": f"'{value}'가(이) 있습니다.",
            "data": data
        }
    except Exception as e:
        print(f"Error in service: {e}")


async def search_schema_by_uploaded_by(value: str):
    try:
        results = search_schema_with_uploaded_by(value)

        if not results:
            return {
                "message": f"'{value}'가(이) 없습니다."
            }

        data_list = []
        for result in results:
            data_list.append({
                "submodel_id": result.get("submodel_id"),
                "version": result.get("version"),
                "revision": result.get("revision"),
                # "create_at": result.get("create_at"),
                "uploaded_by": result.get("uploaded_by")
            })

        return {
            "message": f"'{value}'가(이) {len(data_list)}건 있습니다.",
            "data": data_list
        }
    except Exception as e:
        print(f"Error in service: {e}")


async def search_schema_by_value(semanticId: str, uploadedBy: str):
    try:
        result = search_schema_in_all_fields(semanticId, uploadedBy)

        if not result:
            return {
                "message": f"'{uploadedBy}'의 '{semanticId}' 스키마가 없습니다."
            }

        data = {
            "submodel_id": result.get("submodel_id"),
            "version": result.get("version"),
            "revision": result.get("revision"),
            # "create_at": result.get("create_at"),
            "uploaded_by": result.get("uploaded_by")
        }

        return {
            "message": f"'{uploadedBy}'의 '{semanticId}'를 찾았습니다.",
            "data": data
        }

    except Exception as e:
        print(f"Error in service: {e}")
