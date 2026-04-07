import json, re, os
import subprocess
from api.response_handler import ErrorCode, error_response, success_response
from fastapi import Request
from fastapi.responses import JSONResponse


from typing import TypedDict, List, Dict, Optional

from utils.data_type import MessageGroup

def log_message_group() -> MessageGroup:
    return {
        "assetInfo": [],
        "submodels": [],
        "conceptDescriptions": [],
        "constraints": [],
        "etc": [],
        "checks": [],
    }
    
def process_log_message_group(mg: MessageGroup) -> Dict[str, Dict[str, List[str]]]:
    return {
        "assetInfo": {"count": len(mg["assetInfo"]), "message": mg["assetInfo"]},
        "submodels": {"count": len(mg["submodels"]), "message": mg["submodels"]},
        "conceptDescriptions": {"count": len(mg["conceptDescriptions"]), "message": mg["conceptDescriptions"]},
        "constraints": {"count": len(mg["constraints"]), "message": mg["constraints"]},
        "etc": {"count": len(mg["etc"]), "message": mg["etc"]},
    }



def run_test_engine(file_path: str, file_ext: str, is_template: bool) -> dict:
    command = build_command(file_path, file_ext)
    env = os.environ.copy()

    env["PYTHONIOENCODING"] = "utf-8"
    try:
        result = subprocess.run(command, capture_output=True, env=env)
        
        #중복 리턴 에러 반환, 지원도 되는지 확인(밑에꺼는 남겨놓기)
        if not result:
            return error_response(500, ErrorCode.TEST_ENGINE_NO_OUTPUT)

        if result.stdout:
            result.stdout = result.stdout.decode('utf-8-sig', errors='replace')
            return parse_engine_output(result.stdout, is_stdout=True, is_template=is_template)

        if result.stderr:
            result.stderr = result.stderr.decode('utf-8-sig', errors='replace')
            return parse_engine_output(result.stderr, is_stdout=False, is_template=is_template)

        return error_response(500, ErrorCode.TEST_ENGINE_NO_OUTPUT)
    
        #아래 예외처리는 없어도 될 것으로 보이나.. 확인필요, aasx와 xml 파일이 이상할경우 에러는 ? 
    except json.JSONDecodeError as e:
        return error_response(500, ErrorCode.INVALID_JSON_FORMAT, {str(e)})

    except Exception:
        return error_response(500, ErrorCode.INTERNAL_SERVER_ERROR)

#file_path -> 파일이름.aasx 형태인지 확인하고, 이게 맞으면 파라미터 이름은 file_name바꾸기
def build_command(file_path: str, file_ext: str) -> list:
    #file_path: test.aasx -> 확장자 다 있음. 여기서 확장자만 떼어내도 file_exe정보 확인 가능(필수는아님)
    #CLi 명령어 바꼇으니 불필요한 부분 삭제
    base_command = ["python", "-m", "aas_test_engines", "check_file", file_path]

    if file_ext == ".json":
        base_command += ["--format", "json"]
    elif file_ext == ".xml":
        base_command += ["--format", "xml"]

    return base_command


ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')


def parse_engine_output(output: str, is_stdout: bool, is_template: bool = False) -> dict:
    if output.startswith('\u001b[92mCheck'):  # 초록색
        verification_status = 'success'
    elif output.startswith('\u001b[91mCheck'):  # 빨간색
        verification_status = 'failed'
#warning 처리
    else:
        verification_status = None

    try:
        constraint_msgs = log_message_group()
        lines = output.strip().splitlines()

#data_type에 클래스 형태로 만들어서 데이터 형식 미리 생성해놓기(고정된 값이기 때문)
        # check_msg = []
        # asset_info_msgs = []
        # submodel_msgs = []
        # concept_description_msgs = []
        # constraint_msgs = []
        # etc_msgs = []

        for line in lines:
            clean_line = ansi_escape.sub('', line.strip())

    #ste_err인지 out 인지 확인필요
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
                    constraint_msgs['constraints'].append(clean_line)
                elif "@ /assetAdministrationShells" in clean_line:
                    constraint_msgs['assetInfo'].append(clean_line)
                elif "@ /submodels" in clean_line:
                    constraint_msgs['submodels'].append(clean_line)
                elif "@ /conceptDescriptions" in clean_line:
                    constraint_msgs['conceptDescriptions'].append(clean_line)
                elif clean_line.startswith('Check') or clean_line.startswith('Skipped') or clean_line.startswith('Template:'):
                    constraint_msgs['checks'].append(clean_line)
                else:
                    constraint_msgs['etc'].append(clean_line)

        # verification_message = {
        #     "assetInfo": {
        #         "count": len(asset_info_msgs),
        #         "message": asset_info_msgs
        #     },
        #     "submodels": {
        #         "count": len(submodel_msgs),
        #         "message": submodel_msgs
        #     },
        #     "conceptDescriptions": {
        #         "count": len(concept_description_msgs),
        #         "message": concept_description_msgs
        #     },
        #     "constraints": {
        #         "count": len(constraint_msgs),
        #         "message": constraint_msgs
        #     },
        #     "etc": {
        #         "count": len(etc_msgs),
        #         "message": etc_msgs
        #     }
        # }
        
        verification_message = process_log_message_group(constraint_msgs)
        
        # verification_status = process_log_message_group()

        if is_template:
            total_msgs = (len(constraint_msgs['assetInfo'])
                          + len(constraint_msgs['submodels'])
                          + len(constraint_msgs['conceptDescriptions'])
                          + len(constraint_msgs['constraints'])
                          + len(constraint_msgs['etc']))
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

#에러가 json 에러가 아닌 일반적인 에러로 수정하기
    except json.JSONDecodeError:
        return error_response(
            status_code=400,
            error_code=ErrorCode.INVALID_JSON_FORMAT,
            message=output.strip(),
        )
