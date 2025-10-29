import json, re, os, sys
import subprocess
from utils.response_handler import ErrorCode, error_response, success_response
from run_template import run_constraint_check
from fastapi import Request
from fastapi.responses import JSONResponse


def run_test_engine(file_path: str, file_ext: str, is_template: bool = False) -> dict:
    command = build_command(file_path, file_ext)
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"

    try:
        result = subprocess.run(command, capture_output=True, env=env)

        if not result:
            return error_response(500, ErrorCode.TEST_ENGINE_NO_OUTPUT)

        if result.stdout:
            result.stdout = result.stdout.decode('utf-8-sig', errors='replace')
            return parse_engine_output(result.stdout, is_stdout=True, is_template=is_template)

        if result.stderr:
            result.stderr = result.stderr.decode('utf-8-sig', errors='replace')
            return parse_engine_output(result.stderr, is_stdout=False, is_template=is_template)

        return error_response(500, ErrorCode.TEST_ENGINE_NO_OUTPUT)

    except json.JSONDecodeError as e:
        return error_response(500, ErrorCode.INVALID_JSON_FORMAT, {str(e)})

    except Exception:
        return error_response(500, ErrorCode.INTERNAL_SERVER_ERROR)

# def run_test_engine(file_path: str, file_ext: str, is_template: bool = False) -> dict:
#     command = build_command(file_path, file_ext)
#     env = os.environ.copy()
#     env["PYTHONIOENCODING"] = "utf-8"

#     try:
#         result = subprocess.run(command, capture_output=True, env=env)

#         if not result:
#             return error_response(500, ErrorCode.TEST_ENGINE_NO_OUTPUT)

#         parsed_result = None

#         # 기존 stdout/parse_engine_output 처리
#         if result.stdout:
#             result.stdout = result.stdout.decode('utf-8-sig', errors='replace')
#             parsed_result = parse_engine_output(result.stdout, is_stdout=True, is_template=is_template)

#         elif result.stderr:
#             result.stderr = result.stderr.decode('utf-8-sig', errors='replace')
#             parsed_result = parse_engine_output(result.stderr, is_stdout=False, is_template=is_template)

#         # if isinstance(parsed_result, JSONResponse):
#         #     parsed_result = parsed_result.body.decode("utf-8")
#         #     parsed_result = json.loads(parsed_result)

#         # is_template=True면 강제로 constraint 검사
#         # if is_template:
#         #     print('is template까지 옴')
#         #     constraint_result = run_constraint_check(file_path, parsed_result)
#         #     print(parsed_result)
#         #     parsed_result = parse_engine_output(constraint_result, is_template=is_template)

#         return parsed_result

#     except json.JSONDecodeError as e:
#         return error_response(500, ErrorCode.INVALID_JSON_FORMAT, {str(e)})

#     except Exception:
#         return error_response(500, ErrorCode.INTERNAL_SERVER_ERROR)


def build_command(file_path: str, file_ext: str) -> list:
    base_command = ["aas_test_engines", "check_file", file_path]

    if file_ext == ".json":
        base_command += ["--format", "json"]
    elif file_ext == ".xml":
        base_command += ["--format", "xml"]

    return base_command


ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')


def parse_engine_output(output: str, is_stdout: bool = True, is_template: bool = False) -> dict:
    if output.startswith('\u001b[92mCheck'):  # 초록색
        verification_status = "success"
    elif output.startswith('\u001b[91mCheck'):  # 빨간색
        verification_status = "failed"
    else:
        verification_status = None

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

            if clean_line.startswith('f"Constraint violated:'):
                constraint_msgs.append(clean_line)
                # print(clean_line)
                verification_status = 'failed'
                continue

            if is_template and (
                "String is shorter than 1 characters" in clean_line
                or "Empty array not allowed" in clean_line
            ):
                continue

            if is_stdout is True:
                if clean_line.startswith('Constraint '):
                    constraint_msgs.append(clean_line)
                elif "@ /assetAdministrationShells" in clean_line:
                    asset_info_msgs.append(clean_line)
                elif "@ /submodels" in clean_line:
                    submodel_msgs.append(clean_line)
                elif "@ /conceptDescriptions" in clean_line:
                    concept_description_msgs.append(clean_line)
                elif clean_line.startswith('Check') or clean_line.startswith('Skipped') or clean_line.startswith('Template:') or clean_line.startwith('Constraint AASd-120 violated: element 0 must not have an idShort'):
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

        if is_template:
            total_msgs = (len(asset_info_msgs)
                          + len(submodel_msgs)
                          + len(concept_description_msgs)
                          + len(constraint_msgs)
                          + len(etc_msgs))
            if total_msgs == 0:
                verification_status = 'success'
            else:
                verification_status = 'failed'

        if verification_status == 'success':
            return success_response("Model API", "success", "PERFECT")
        elif verification_status == "failed":
            return success_response("Model API", "failed", verification_message)
        else:
            return success_response("Model API", "warning", verification_message)

    except json.JSONDecodeError:
        return error_response(
            status_code=400,
            error_code=ErrorCode.INVALID_JSON_FORMAT,
            message=output.strip(),
        )
