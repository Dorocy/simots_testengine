import json, re, os
import subprocess
from utils.response_handler import ErrorCode, error_response, success_response
from utils.data_type import MessageGroup
from run_template import run_constraint_check
from utils.data_type import TEMPLATE_EXCLUDE_PATTERNS
from fastapi import Request
from fastapi.responses import JSONResponse
from aas_core3.types import Environment


# def run_test_engine(file, file_name: str, is_template: bool) -> dict:
#     command = build_command(file, file_name)
#     env = os.environ.copy()

#     env["PYTHONIOENCODING"] = "utf-8"
#     try:
#         if is_template:
#             message = run_constraint_check(file)
#             return parse_engine_output(message, is_stdout=True, is_template=is_template)

#         result = subprocess.run(command, capture_output=True, env=env)

#         if result.stdout:
#             meta_output = result.stdout.decode('utf-8-sig', errors='replace')
#             return parse_engine_output(meta_output, is_stdout=True, is_template=is_template)

#         if result.stderr:
#             meta_output = result.stderr.decode('utf-8-sig', errors='replace')
#             return parse_engine_output(meta_output, is_stdout=False, is_template=is_template)

#         return error_response(500, ErrorCode.TEST_ENGINE_NO_OUTPUT)

#     except json.JSONDecodeError as e:
#         return error_response(500, ErrorCode.INVALID_JSON_FORMAT, {str(e)})

#     except Exception as e:
#         return {str(e)}
#         # return error_response(500, ErrorCode.INTERNAL_SERVER_ERROR)


def run_test_engine(file, file_name: str, is_template: bool) -> dict:
    command = build_command(file, file_name)
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"

    try:
        result = subprocess.run(command, capture_output=True, env=env)
        output = ""
        is_stdout = True

        if result.stdout:
            output = result.stdout.decode("utf-8-sig", errors="replace")
            is_stdout = True
            print('stdout: ', output)
        elif result.stderr:
            output = result.stderr.decode("utf-8-sig", errors="replace")
            is_stdout = False
            print('stderr: ', output)
        else:
            return error_response(500, ErrorCode.TEST_ENGINE_NO_OUTPUT)

        constraint_output = ""
        if is_template:
            constraint_output = run_constraint_check(file)

        combined_output = output.strip()
        if constraint_output:
            combined_output += "\n" + constraint_output.strip()
            print('combined_output: ', combined_output)

        return parse_engine_output(
            combined_output,
            is_stdout=is_stdout,
            is_template=is_template
        )

    except json.JSONDecodeError as e:
        return error_response(500, ErrorCode.INVALID_JSON_FORMAT, {str(e)})

    except Exception as e:
        return error_response(500, ErrorCode.INTERNAL_SERVER_ERROR, {str(e)})


def build_command(file, file_name: str) -> list:
    _, file_ext = os.path.splitext(file.filename)
    base_command = ["aas_test_engines", "check_file", file_name]

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

        msg: MessageGroup = MessageGroup(
            assetInfo=[],
            submodels=[],
            conceptDescriptions=[],
            constraints=[],
            etc=[],
            needless=[]
        )

        for line in lines:
            clean_line = ansi_escape.sub('', line.strip())

            if is_stdout is False:
                if clean_line.startswith('f"Constraint violated:'):
                    msg['constraints'].append(clean_line)
                    verification_status = 'failed'
                    continue

            if is_template and any(re.search(pattern, clean_line) for pattern in TEMPLATE_EXCLUDE_PATTERNS):
                continue

            if is_stdout is True:
                if re.match(r'^(Constraint AASd-120|Check|Skipped|Template:|Relationship aasx/)', clean_line):
                    msg['needless'].append(clean_line)
                elif clean_line.startswith('Constraint '):
                    msg['constraints'].append(clean_line)
                elif "@ /assetAdministrationShells" in clean_line:
                    msg['assetInfo'].append(clean_line)
                elif "@ /submodels" in clean_line:
                    msg['submodels'].append(clean_line)
                elif "@ /conceptDescriptions" in clean_line:
                    msg['conceptDescriptions'].append(clean_line)
                else:
                    msg['etc'].append(clean_line)

        verification_message = {
            key: {"count": len(val), "message": val}
            for key, val in msg.items()
            if key != "needless"
        }

        if is_template:
            total_msgs = sum(len(val) for key, val in msg.items() if key != "needless")
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
