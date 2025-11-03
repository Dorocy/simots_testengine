import json, io, re, os, sys
import subprocess
from utils.response_handler import ErrorCode, error_response, success_response
from utils.data_type import MessageGroup
from run_template import run_constraint_check
from fastapi import Request
from fastapi.responses import JSONResponse
from aas_core3.types import Environment


def run_test_engine(file, file_name: str, is_template: bool) -> dict:
    command = build_command(file, file_name)
    env = os.environ.copy()

    env["PYTHONIOENCODING"] = "utf-8"
    try:
        result = subprocess.run(command, capture_output=True, env=env)
        if is_template:
            message = run_constraint_check(file)
            parse_engine_output(message, is_stdout=True, is_template=is_template)
            
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
                    # print(clean_line)
                    verification_status = 'failed'
                    continue

            if is_template and (
                "String is shorter than 1 characters" in clean_line
                or "Empty array not allowed" in clean_line
            ):
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
