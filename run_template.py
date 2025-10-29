import os
import sys

from aas_test_engines.test_cases.v3_0.parse import check_constraints, _parse_and_check
from aas_test_engines.test_cases.v3_0.__init__ import json_to_obj
from aas_test_engines.result import AasTestResult


def run_constraint_check(file_path: str, parsed_result: dict = None) -> dict:
    print("constraint check 시작")

    try:
        result_root, env = json_to_obj(parsed_result, "Environment")
        print('env: ', env)

        if env is None:
            print("환경 파싱 실패")
            return result_root.dump()

        # ✅ Environment 전체에 대해 constraint 검사
        check_constraints(env, result_root)

        print("constraint check 완료")
        print(result_root.dump())
        return result_root.dump()

    except Exception as e:
        print(f"[Constraint Check Error] {e}")
        return {"status": "Constraint Check Failed", "error": str(e)}