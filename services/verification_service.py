import json, io, sys, os, utils.file_handler as file_handler, test_engine_run, run_submodel
import aas_core3.jsonization as aas_jsonization
import asyncio
from fastapi import HTTPException, Query, Path
# from fastapi.responses import JSONResponse
from aas_core3.types import Environment, SubmodelElement, Qualifier
from utils.file_handler import remove_ansi_codes
from utils.response_handler import ErrorCode, error_response, success_response
from utils.db_hadler import (
    delete_schema_by_semantic_id,
    retrieve_schemas,
    extract_semantic_id,
    search_schema_in_all_fields,
    search_schema_with_semantic_id,
    search_schema_with_uploaded_by,
    delete_schema_by_semantic_id,
    alter_schema_put,
    alter_schema_patch
    )
from export_schema import get_schema_result, generate_schema_code


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


# def validate_qualifiers(data: json):
#     try:
#         environment = aas_jsonization.environment_from_jsonable(data)
#     except Exception:
#         return error_response(
#             400,
#             ErrorCode.INVALID_FILE_FORMAT
#             )

#     for submodel in environment.submodels:
#         for element in submodel.submodel_elements or []:
#             element_id = element.id_short or "Unknown"
#             qualifiers = element.qualifiers or []

#             has_required_qualifier = False
#             for qualifier in qualifiers:
#                 q_kind = qualifier.kind.value if qualifier.kind else None
#                 q_type = qualifier.type if qualifier.type else None

#                 print(f"DEBUG: Checking {element_id} -> kind: {q_kind}, type: {q_type}")

#                 if q_kind == "TemplateQualifier" and q_type == "SMT_Cardinality":
#                     has_required_qualifier = True
#                     break  # 조건 만족 시 바로 통과

#             if not has_required_qualifier:
#                 return error_response(
#                     400,
#                     ErrorCode.INVALID_QUALIFIER_COMBINATION,
#                     element_id
#                 )

#     return True


# def validate_qualifiers(data: json):
#     try:
#         environment = aas_jsonization.environment_from_jsonable(data)
#     except Exception:
#         return error_response(
#             400,
#             ErrorCode.INVALID_FILE_FORMAT
#             )

#     # for submodel in environment.submodels:
#     for submodel in environment.over_submodels_or_empty():
#         for element in submodel.submodel_elements or []:
#             element_id = element.id_short or "Unknown"
#             qualifiers = element.qualifiers or []

#             has_required_qualifier = False
#             for qualifier in qualifiers:
#                 q_kind = qualifier.kind.value if qualifier.kind else None
#                 q_type = qualifier.type if qualifier.type else None

#                 print(f"DEBUG: Checking {element_id} -> kind: {q_kind}, type: {q_type}")

#                 if q_kind == "TemplateQualifier" and q_type == "SMT_Cardinality":
#                     has_required_qualifier = True
#                     break  # 조건 만족 시 바로 통과

#             if not has_required_qualifier:
#                 return error_response(
#                     400,
#                     ErrorCode.INVALID_QUALIFIER_COMBINATION,
#                     element_id
#                 )

#     return True

def is_required_qualifier(q: Qualifier) -> bool:
    return (
        q.kind and q.kind.value == "TemplateQualifier"
        and q.type and q.type == "SMT_Cardinality"
    )


def validate_qualifiers(data: dict):
    try:
        environment: Environment = aas_jsonization.environment_from_jsonable(data)
    except Exception:
        return error_response(400, ErrorCode.INVALID_FILE_FORMAT)

    for instance in environment.descend():
        if isinstance(instance, SubmodelElement):
            element_id = instance.id_short or "Unknown"

            if not any(is_required_qualifier(q) for q
                       in instance.over_qualifiers_or_empty()):
                return error_response(
                    400,
                    ErrorCode.INVALID_QUALIFIER_COMBINATION,
                    element_id
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


def postprocess_grouped_templates(grouped: dict) -> tuple[str, dict]:
    all_perfect = True
    for key in grouped:
        if not grouped[key]:
            grouped[key] = ["PERFECT"]
        else:
            all_perfect = False
    result_status = "success" if all_perfect else "failed"
    return result_status, grouped


async def verification_instance(file):

    file_content = await file.read()
    try:
        json_data = json.loads(file_content.decode("utf-8"))
    except Exception:
        return ErrorCode.INVALID_JSON_FORMAT

    buffer = io.StringIO()
    sys.stdout = buffer
    run_submodel.check_submodel_templates(json_data)

    output = buffer.getvalue()
    cleaned_output = remove_ansi_codes(output).strip().splitlines()
    grouped_templates = group_by_template(cleaned_output)

    result_status, grouped_templates = postprocess_grouped_templates(grouped_templates)
    return success_response(
            "Instance API",
            result_status,
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


async def update_schema_put(file):
    contents = await file.read()
    data = json.loads(contents)

    for submodel_data in data.get("submodels", []):
        try:
            submodel = aas_jsonization.submodel_from_jsonable(submodel_data)
        except Exception:
            return error_response(400, ErrorCode.INVALID_FILE_FORMAT)

        # 스키마 추출 전, submodel kind 검사
        submodel_type_error = check_submodel_kind(submodel_data)
        if submodel_type_error:
            return submodel_type_error

    semanticId = submodel.semantic_id.keys[0].value

    # 스키마 추출에 필요한 검사들
    if semanticId.startswith("https://admin-shell.io/"):
        return generate_schema_code(data)
    elif semanticId in ['0173-1#01-AHF578#001', '0173-1#01-AHX837#002']:
        return generate_schema_code(data)
    else:
        validate_result = validate_qualifiers(data)
        if validate_result is not True:
            return validate_result

    binary_data = generate_schema_code(data)
    update_result = alter_schema_put(semanticId, binary_data, data)
    print("******************************update result", update_result)

    if update_result:
        return success_response(
            "Edit API",
            "success",
            f"스키마 '{semanticId}'가 성공적으로 수정되었습니다."
        )
    else:
        return error_response(
            400,
            ErrorCode.DB_ERROR
        )


async def update_schema_patch(file):
    contents = await file.read()
    data = json.loads(contents)

    for submodel_data in data.get("submodels", []):
        try:
            submodel = aas_jsonization.submodel_from_jsonable(submodel_data)
        except Exception:
            return error_response(400, ErrorCode.INVALID_FILE_FORMAT)

        submodel_type_error = check_submodel_kind(submodel_data)
        if submodel_type_error:
            return submodel_type_error

    semanticId = submodel.semantic_id.keys[0].value

    if semanticId.startswith("https://admin-shell.io/"):
        return generate_schema_code(data)
    elif semanticId in ['0173-1#01-AHF578#001', '0173-1#01-AHX837#002']:
        return generate_schema_code(data)
    else:
        validate_result = validate_qualifiers(data)
        if validate_result is not True:
            return validate_result

    existing_schema = search_schema_with_semantic_id(semanticId)
    if not existing_schema:
        return error_response(
            400,
            ErrorCode.SCHEMA_NOT_FOUND
            )

    binary_data = generate_schema_code(data)

    if existing_schema.get("schema") == binary_data:
        return success_response(
            "Patch API",
            "noop",
            f"스키마 '{semanticId}'는 기존과 동일하여 수정되지 않았습니다."
        )

    update_result = alter_schema_patch(semanticId, binary_data)
    if not update_result:
        return error_response(400, ErrorCode.DB_ERROR)

    return success_response(
        "Patch API",
        "success",
        f"스키마 '{semanticId}'가 성공적으로 수정되었습니다."
    )
