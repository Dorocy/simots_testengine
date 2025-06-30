import json, io, sys, os, utils.file_handler as file_handler, test_engine_run, run_submodel
import asyncio
from fastapi import HTTPException, Query
from fastapi.responses import JSONResponse
from utils.file_handler import remove_ansi_codes
from utils.response_handler import ErrorCode, error_response, success_response
from utils.db_hadler import (
    delete_schema_by_semantic_id,
    retrieve_schemas,
    search_schema_in_all_fields,
    search_schema_with_semantic_id,
    search_schema_with_uploaded_by,
    delete_schema_by_semantic_id,
    restore_schema_backup,
    get_db_client
    )
import aas_core3.jsonization as aas_jsonization
from export_schema import get_schema_result


existing_names = {}


async def verification_metamodel(file):
    response = process_verification(file)
    return response


def process_verification(file) -> dict:
    _, file_ext = os.path.splitext(file.filename)

    if file_ext not in file_handler.SUPPORTED_EXTENSIONS:
        return error_response(
            400,
            ErrorCode.INVALID_FILE_FORMAT
            )

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
    try:
        submodel = aas_jsonization.submodel_from_jsonable(data)

    except Exception:
        return error_response(
            400,
            ErrorCode.INVALID_FILE_FORMAT
            )

    if submodel.kind.value != "Template":
        return error_response(
            400,
            ErrorCode.INVALID_SUBMODEL_KIND
            )
    return None


def validate_qualifiers(data: json):
    try:
        environment = aas_jsonization.environment_from_jsonable(data)
    except Exception:
        return error_response(
            400,
            ErrorCode.INVALID_FILE_FORMAT
            )

    for submodel in environment.submodels:
        for element in submodel.submodel_elements or []:
            element_id = element.id_short or "Unknown"
            qualifiers = element.qualifiers or []

            has_required_qualifier = False
            for qualifier in qualifiers:
                q_kind = qualifier.kind.value if qualifier.kind else None
                q_type = qualifier.type if qualifier.type else None

                print(f"DEBUG: Checking {element_id} -> kind: {q_kind}, type: {q_type}")

                if q_kind == "TemplateQualifier" and q_type == "SMT_Cardinality":
                    has_required_qualifier = True
                    break  # 조건 만족 시 바로 통과

            if not has_required_qualifier:
                return error_response(
                    400,
                    ErrorCode.INVALID_QUALIFIER_COMBINATION,
                    f"element '{element_id}'에는 kind='TemplateQualifier', type='SMT_Cardinality'인 qualifier가 하나 이상 있어야 합니다.",
                )

    return True


SUCCESS_COLOR_CODE = "\x1b[92m"
FAILED_COLOR_CODE = "\x1b[91m"


def group_by_template(output_lines: list[str]) -> dict:
    groups = {}
    current_key = None

    for line in output_lines:
        stripped_line = line.strip()
        if stripped_line.startswith("Template:"):
            current_key = stripped_line.replace("Template: ", "")
            groups[current_key] = []
        elif current_key:
            if not stripped_line.startswith("Check submodel"):
                groups[current_key].append(stripped_line)
                print(groups)
    return groups


async def verification_instance(file):
    file_content = await file.read()
    try:
        json_data = json.loads(file_content.decode("utf-8"))
    except Exception:
        return ErrorCode.INVALID_JSON_FORMAT

    buffer = io.StringIO()  # 기본 출력을 문자열 버퍼로 변경
    sys.stdout = buffer
    run_submodel.check_submodel_templates(json_data)  # 터미널 출력을 저장
    output = buffer.getvalue()

    cleaned_output = remove_ansi_codes(output).strip().splitlines()

    grouped_templates = group_by_template(cleaned_output)

    for line in output.splitlines():
        if "Check submodel" in line:
            if SUCCESS_COLOR_CODE in line:
                return success_response(
                    "Instance API",
                    "success",
                    grouped_templates
                )
            elif FAILED_COLOR_CODE in line:
                return success_response(
                    "Instance API",
                    "failed",
                    grouped_templates
                )


async def delete_schema(semanticId: str = Query(..., description="SemanticId of the schema to delete")):
    success = delete_schema_by_semantic_id(semanticId)
    if not success:
        return success_response(
            "Delete API",
            "failed",
            "Schema not found in database."
            )
    return success_response(
        "Delete API",
        "success",
        f"Schema for semanticId '{semanticId}' has been deleted from DB."
        )


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
            "uploaded_by": result.get("uploaded_by")
        }

        return {
            "message": f"'{uploadedBy}'의 '{semanticId}'를 찾았습니다.",
            "data": data
        }

    except Exception as e:
        print(f"Error in service: {e}")


async def edit_schema_by_semantic_id(file):
    contents = await file.read()
    data = json.loads(contents)

    for submodel_data in data.get("submodels", []):
        try:
            submodel = aas_jsonization.submodel_from_jsonable(submodel_data)
        except Exception:
            return error_response(
                400,
                ErrorCode.INVALID_FILE_FORMAT
                )

        try:
            semantic_id = submodel.semantic_id.keys[0].value
            search_result = search_schema_with_semantic_id(semantic_id)
        except Exception:
            return error_response(
                400,
                ErrorCode.SEMANTIC_ID_NOT_FOUND
            )

        await file.seek(0)  # 파일 포인터 초기화

        if search_result is None:
            return success_response(
                "Edit API",
                "failed",
                f"schema: {semantic_id} not found."
                )

        backup_schema = search_result
        delete_schema_by_semantic_id(semantic_id)

        client = get_db_client()

        for _ in range(10):
            still_exists = client.aas.aas_schema.find_one({"submodel_id": semantic_id})
            if not still_exists:
                break
            await asyncio.sleep(0.1)
        else:
            # 10번 돌았는데도 안 없어졌으면 실패
            return error_response(
                500,
                ErrorCode.DB_ERROR,
                f"Failed to delete schema '{semantic_id}' from DB in time."
            )

        edit_result = await verification_schema(file)

        try:
            body = json.loads(edit_result.body)
            verification_status = body.get("verification", {}).get("result")
        except Exception:
            verification_status = None
        print("*****************", verification_status)

        if verification_status == "success":
            return success_response(
                "Edit API",
                "success",
                f"Schema '{semantic_id}'가 수정되었습니다."
                )
        else:
            # 복구 시도
            restored = restore_schema_backup(backup_schema)
            if restored:
                print("복구 성공")
            else:
                print("**복구 실패**")

            return success_response(
                "Edit API",
                "failed",
                f"Schema '{semantic_id}'가 올바르지 않습니다."
            )
