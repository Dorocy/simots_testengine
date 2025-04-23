import json, re
import subprocess
from utils.response_handler import ErrorCode, error_response, success_response
from fastapi import Request
from fastapi.responses import JSONResponse


def run_test_engine(file_path: str, file_ext: str) -> dict:
    command = build_command(file_path, file_ext)

    try:
        result = subprocess.run(command, capture_output=True, text=True)
        if not result:
            return error_response(500, ErrorCode.TEST_ENGINE_NO_OUTPUT)

        if result.stderr:
            return parse_engine_output(result.stderr)

        if result.stdout:
            return parse_engine_output(result.stdout)

        return error_response(500, ErrorCode.TEST_ENGINE_NO_OUTPUT)
    # 커맨드 라인에서 발생하는 에러니까.. 메세지는 따로 출력되도록 처리함
    except json.JSONDecodeError as e:
        return error_response(500, ErrorCode.INVALID_JSON_FORMAT, {str(e)})

    except Exception:
        return error_response(500, ErrorCode.INTERNAL_SERVER_ERROR)


def build_command(file_path: str, file_ext: str) -> list:
    base_command = ["python", "-m", "aas_test_engines", "check_file", file_path]

    if file_ext == ".json":
        base_command += ["--format", "json"]
    elif file_ext == ".xml":
        base_command += ["--format", "xml"]

    # base_command += ["--output", "json"]

    return base_command


# def parse_engine_output(output: str) -> dict:
#     try:
#         json_output = json.loads(output)
#     except json.JSONDecodeError:
#         return error_response(
#             status_code=400,
#             error_code=ErrorCode.INVALID_JSON_FORMAT,
#             message=output.strip(),
#         )

#     level = json_output.get("l", None)

#     # Json 형태로 응답받는 부분을 바꿨으므로 처리하는 부분도 바꿨습니다.
#     if level == 0:
#         return success_response("Model API", "Pass", json_output)
#     elif level in [1, 2]:
#         return success_response("Model API", "Fail", json_output)
#     # 어떤 상황이 올지 한번 확인해봐야하며,, 이럴때는 어떤상황인지 Test 모델 작성이 필요합니다.
#     else:
#         return success_response("Model API", "Unknown Error", json_output)

ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')
green_check = re.compile(r'\x1b\[92mCheck')
red_check = re.compile(r'\x1b\[91mCheck')

def parse_engine_output(output: str) -> dict:
    if output.startswith('\u001b[92mCheck'):  # 초록색
        verification_status = 'Pass'
    elif output.startswith('\u001b[91mCheck'):  # 빨간색
        verification_status = 'Fail'

    try:
        lines = output.strip().splitlines()

        check_msg = []
        asset_info_msgs = []
        submodel_msgs = []
        concept_description_msgs = []
        constraint_msgs = []
        etc_msgs = []

        for line in lines:
            clean_line = ansi_escape.sub('', line.strip())
            print('한줄한줄체크해볼까?',line)
            if clean_line.startswith("Constraint "):
                constraint_msgs.append(clean_line)
            elif "@ /assetAdministrationShells" in clean_line:
                asset_info_msgs.append(clean_line)
            elif "@ /submodels" in clean_line:
                submodel_msgs.append(clean_line)
            elif "@ /conceptDescriptions" in clean_line:
                concept_description_msgs.append(clean_line)
            elif clean_line.startswith("Check") or clean_line.startswith("Skipped") or clean_line.startswith("Template:"):
                check_msg.append(clean_line)
                
            else:
                etc_msgs.append(clean_line)

        verification_message = {
            "assetInfo": {
                "count": len(asset_info_msgs),
                "message": asset_info_msgs
            },
            "submodels": {
                "count": len(submodel_msgs),
                "message": submodel_msgs
            },
            "conceptDescriptions": {
                "count": len(concept_description_msgs),
                "message": concept_description_msgs
            },
            "constraints": {
                "count": len(constraint_msgs),
                "message": constraint_msgs
            },
            "etc": {
                "count": len(etc_msgs),
                "message": etc_msgs
            }
        }

        if verification_status == 'Pass':
            return success_response("Model API", "Pass", "PERFECT")
        elif verification_status == 'Fail':
            return success_response("Model API", "Fail", verification_message)
        # 어떤 상황이 올지 한번 확인해봐야하며,, 이럴때는 어떤상황인지 Test 모델 작성이 필요합니다.
        else:
            return success_response("Model API", "Unknown Error", verification_message)

    except Exception as e:
        return error_response(500, ErrorCode.INTERNAL_SERVER_ERROR, {"detail": str(e)})
