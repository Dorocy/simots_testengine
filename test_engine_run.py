import json
import subprocess
from utils.response_handler import ErrorCode, error_response, success_response


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

    base_command += ["--output", "json"]

    return base_command


def parse_engine_output(output: str) -> dict:
    try:
        json_output = json.loads(output)
    except json.JSONDecodeError:
        return error_response(
            status_code=400,
            error_code=ErrorCode.INVALID_JSON_FORMAT,
            message=output.strip(),
        )

    level = json_output.get("l", None)

    # Json 형태로 응답받는 부분을 바꿨으므로 처리하는 부분도 바꿨습니다.
    if level == 0:
        return success_response("Model API", "Pass", json_output)
    elif level in [1, 2]:
        return success_response("Model API", "Fail", json_output)
    # 어떤 상황이 올지 한번 확인해봐야하며,, 이럴때는 어떤상황인지 Test 모델 작성이 필요합니다.
    else:
        return success_response("Model API", "Unknown Error", json_output)
