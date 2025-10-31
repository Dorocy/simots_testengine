import os, sys, json

from aas_test_engines.test_cases.v3_0.parse import check_constraints, _parse_and_check, parse,parse_and_check_json
from aas_test_engines.reflect import TypeBase
from aas_test_engines.test_cases.v3_0.__init__ import json_to_obj
from aas_test_engines.test_cases.v3_0.adapter import JsonAdapter
from aas_test_engines.result import AasTestResult, Level
import aas_core3.jsonization as aas_jsonization
from aas_test_engines.file import check_json_data

# def run_constraint_check(file_path: str, parsed_result: dict = None) -> dict:
#     print("constraint check 시작")

#     try:
#         result_root, env = json_to_obj(parsed_result, "Environment")
#         print('env: ', env)

#         if env is None:
#             print("환경 파싱 실패")
#             return result_root.dump()

#         check_constraints(env, result_root)

#         print("constraint check 완료")
#         print(result_root.dump())
#         return result_root.dump()

#     except Exception as e:
#         print(f"[Constraint Check Error] {e}")
#         return {"status": "Constraint Check Failed", "error": str(e)}


# def run_constraint_check(file_path: str) -> str:
#     print("constraint check 시작")

#     try:
#         json_data = json.loads(file_content.decode("utf-8"))

#         result_root, env = json_to_obj(parsed_json, "Environment")
#         # print('env: ', env)
#         print('parsed json: ', parsed_json)

#         if env is None:
#             return f"[Constraint Check Error] Failed to parse environment for {file_path}"

#         constraint_result = AasTestResult("Forced constraint check")
#         check_constraints(env, constraint_result)

#         return constraint_result.dump()

#     except Exception as e:
#         return f"[Forced constraint check error] {e}"



def run_constraint_check(json_data: dict):
    print("constraint check 시작")
    result_root = AasTestResult("constraints한번보자")
    try:
        # 1. JSON → Environment 객체
        test = check_json_data(json_data, "Environment")
        print(test)

        # result_root, env = json_to_obj(test, "Environment")
        # if env is None:
        #     print("Environment 파싱 실패")
        #     return result_root.dump()

        # 2. Environment 전체에 대해 constraint 검사
        constCheck=_parse_and_check(1, test)
        return constCheck.dump()
        # return result_root.dump()

    except Exception as e:
        print(f"[Forced Constraint Check Error] {e}")
        error_result = AasTestResult("Forced Constraint Check Failed")
        error_result.append(AasTestResult(f"Exception: {e}"))
        return error_result.dump()


# def run_constraint_check(json_data: dict, cls: TypeBase):
#     print("constraint check 시작")

#     try:
#         result_root = AasTestResult("Forced Constraint Check")
#         result_meta = AasTestResult("Parse JSON to Environment")
#         print('ttttt')
#         env = parse(cls, JsonAdapter(json_data), result_meta)  # parse 사용
#         print('ENV변환되는값봅시다',env)

#         result_root.append(result_meta)

#         # 2. Environment 전체에 대해 constraint 검사
#         check_constraints(env, result_root)

#         return result_root.dump()

#     except Exception as e:
#         print(f"[Forced Constraint Check Error] {e}")
#         error_result = AasTestResult("Forced Constraint Check Failed")
#         error_result.append(AasTestResult(f"Exception: {e}"))
#         return error_result.dump()
