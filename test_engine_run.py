import json, io, re, os, sys
import subprocess
from utils.response_handler import ErrorCode, error_response, success_response
from run_template import run_constraint_check
from fastapi import Request
from fastapi.responses import JSONResponse
from aas_core3.types import Environment


# def run_test_engine(file_path: str, file_ext: str, is_template: bool = False) -> dict:
#     command = build_command(file_path, file_ext)
#     env = os.environ.copy()

#     env["PYTHONIOENCODING"] = "utf-8"
#     try:
#         result = subprocess.run(command, capture_output=True, env=env)

#         if not result:
#             return error_response(500, ErrorCode.TEST_ENGINE_NO_OUTPUT)

#         if result.stdout:
#             result.stdout = result.stdout.decode('utf-8-sig', errors='replace')
#             return parse_engine_output(result.stdout, is_stdout=True, is_template=is_template)

#         if result.stderr:
#             result.stderr = result.stderr.decode('utf-8-sig', errors='replace')
#             return parse_engine_output(result.stderr, is_stdout=False, is_template=is_template)

#         return error_response(500, ErrorCode.TEST_ENGINE_NO_OUTPUT)

#     except json.JSONDecodeError as e:
#         return error_response(500, ErrorCode.INVALID_JSON_FORMAT, {str(e)})

#     except Exception:
#         return error_response(500, ErrorCode.INTERNAL_SERVER_ERROR)


# async def run_test_engine(file, file_path: str, file_ext: str, is_template: bool = False) -> dict:
#     command = build_command(file_path, file_ext)
#     env = os.environ.copy()
#     env["PYTHONIOENCODING"] = "utf-8"

#     try:
#         result = subprocess.run(command, capture_output=True, env=env)

#         if not result:
#             return error_response(500, ErrorCode.TEST_ENGINE_NO_OUTPUT)

#         raw_bytes = result.stdout if result.stdout else result.stderr
#         is_stdout = bool(result.stdout)
#         raw_output = raw_bytes.decode('utf-8-sig', errors='replace')

#         if is_template:
#             with open(file_path, "r", encoding="utf-8") as f:
#                 file_content = json.load(f)
#                 print('aaaaaaaa: ', file_content)
#             # try:
#             #     json_data = json.loads(file_content.decode("utf-8"))
#             # except Exception:
#             #     return ErrorCode.INVALID_JSON_FORMAT

#             buffer = io.StringIO()
#             sys.stdout = buffer
#             constraint_output = run_constraint_check(json_data)

#             raw_output = raw_output + "\n" + constraint_output

#         final_parsed = parse_engine_output(raw_output, is_stdout=is_stdout, is_template=is_template)

#         return final_parsed

#     except json.JSONDecodeError as e:
#         return error_response(500, ErrorCode.INVALID_JSON_FORMAT, {str(e)})
#     except Exception as e:
#         return error_response(500, ErrorCode.INTERNAL_SERVER_ERROR, {str(e)})


def run_test_engine(file_path: str, file_ext: str, is_template: bool = False) -> dict:
    command = build_command(file_path, file_ext)
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"

    try:
        result = subprocess.run(command, capture_output=True, env=env)

        if not result:
            return error_response(500, ErrorCode.TEST_ENGINE_NO_OUTPUT)

        output_str = None
        if result.stdout:
            output_str = result.stdout.decode('utf-8-sig', errors='replace')
        elif result.stderr:
            output_str = result.stderr.decode('utf-8-sig', errors='replace')
        else:
            return error_response(500, ErrorCode.TEST_ENGINE_NO_OUTPUT)

        if is_template:
            try:
                json_data = parsed_result.get("json_data")
                if json_data:
                    forced_result = run_constraint_check(json_data)
                    parsed_result["forced_constraint_check"] = forced_result
            except Exception as e:
                parsed_result["forced_constraint_check"] = {"error": str(e)}

        parsed_result = parse_engine_output(output_str, is_stdout=bool, is_template=is_template)
        return parsed_result

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

    return base_command


ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')


def parse_engine_output(output: str, is_stdout: bool = True, is_template: bool = False) -> dict:
    if output.startswith('\u001b[92mCheck'):  # 초록색, 노란색
        verification_status = 'success'
    elif output.startswith('\u001b[91mCheck') or output.startswith('\u001b[93mCheck'):  # 빨간색
        verification_status = 'failed'
    else:
        verification_status = None

    try:
        lines = output.strip().splitlines()

        needless_msg = []
        asset_info_msgs = []
        submodel_msgs = []
        concept_description_msgs = []
        constraint_msgs = []
        etc_msgs = []

        for line in lines:
            clean_line = ansi_escape.sub('', line.strip())

            if clean_line.startswith('f"Constraint violated:'):
                constraint_msgs.append(clean_line)
                verification_status = 'failed'
                continue

            if is_template and (
                "String is shorter than 1 characters" in clean_line
                or "Empty array not allowed" in clean_line
            ):
                continue

            if is_stdout is True:
                if clean_line.startswith('Constraint AASd-120') or clean_line.startswith('Check') or clean_line.startswith('Skipped') or clean_line.startswith('Template:'):
                    needless_msg.append(clean_line)
                elif clean_line.startswith('Constraint '):
                    constraint_msgs.append(clean_line)
                elif "@ /assetAdministrationShells" in clean_line:
                    asset_info_msgs.append(clean_line)
                elif "@ /submodels" in clean_line:
                    submodel_msgs.append(clean_line)
                elif "@ /conceptDescriptions" in clean_line:
                    concept_description_msgs.append(clean_line)
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

        if (is_template or is_stdout):
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
        elif verification_status == 'failed':
            return success_response("Model API", "failed", verification_message)
        else:
            return error_response("400", "Unknown Error", verification_message)

    except json.JSONDecodeError:
        return error_response(
            status_code=400,
            error_code=ErrorCode.INVALID_JSON_FORMAT,
            message=output.strip(),
        )
