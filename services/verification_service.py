import json, io, sys, os, utils.file_handler as file_handler, test_engine_run, run_submodel
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from utils.file_handler import remove_ansi_codes
from utils.response_handler import ErrorCode, error_response
import aas_core3.types as aas_types
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
    
    #DB저장로직~
    
    
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
    # formatted_output = cleaned_output.splitlines()

    return JSONResponse(content=cleaned_output)


async def verification_metamodel(file):
    response = process_verification(file)
    return response


def process_verification(file) -> dict:
    _, file_ext = os.path.splitext(file.filename)
    
#파일 형태 예외처리 error_handler에서 공통 함수 사용해서 처리
    if file_ext not in file_handler.SUPPORTED_EXTENSIONS:
        return error_response(
                status_code=400,
                error_code=ErrorCode.INVALID_FILE_FORMAT
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

        response = {"file": os.path.basename(file_path), "verification": result}
        if extracted_id:
            response["extracted_id"] = extracted_id

        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except RuntimeError as re:
        raise HTTPException(status_code=500, detail=str(re))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"처리 중 오류 발생: {str(e)}")


def check_submodel_kind(data:json):
    #submodel을 라이브러리의 타입에 맞게 변화하는 부분 확인차 에러 처리
    try:
        submodel = aas_jsonization.submodel_from_jsonable(data)
    except Exception as e:
        return error_response(
            400, ErrorCode.INVALID_FILE_FORMAT,
        )

    if submodel.kind.value == "Instance":
        return error_response(
            400, ErrorCode.INVALID_SUBMODEL_KIND
        )
    return None


#Mission 1. 위의 라이브러리를 사용하여 아래 소스코드 간소화 및 수정 요함!
#SME의 qualifier 검사
def validate_qualifiers(data: json):
    
    for submodel in data["submodels"]:
        submodel_elements = submodel.get("submodelElements", [])
        
        if not isinstance(submodel_elements, list):
            continue  

        for element in submodel_elements:
            element_id = element.get("idShort", "Unknown")
            qualifiers = element.get("qualifiers", [])
            
            for qualifier in qualifiers:
                kind = qualifier.get("kind")
                q_type = qualifier.get("type")
                print(f"DEBUG: Checking {element_id} -> kind: {kind}, type: {q_type}")
                
                if kind and kind != "TemplateQualifier":
                    return error_response(
                        400, ErrorCode.INVALID_QUALIFIER_KIND,
                        f"element '{element_id}'의 qualifier.kind는 'TemplateQualifier'여야 합니다."
                    )

                if q_type and q_type != "SMT_Cardinality":
                    return error_response(
                        400, ErrorCode.INVALID_QUALIFIER_TYPE,
                        f"element '{element_id}'의 qualifier.type은 'SMT_Cardinality'여야 합니다."
                    )