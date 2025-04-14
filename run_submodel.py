# TODO : save files in directory, merge with run.py
import sys
sys.stdout.reconfigure(encoding="utf-8")
from typing import Tuple, Optional
from aas_test_engines.test_cases.v3_0.parse import parse
from aas_test_engines.test_cases.v3_0.submodel_templates import parse_submodel_templates
from aas_test_engines.test_cases.v3_0.adapter import JsonAdapter, AdapterPath
from aas_test_engines.result import AasTestResult
from aas_test_engines.test_cases.v3_0.model import Environment
import schemas

templates = {}

def parse_env_without_meta(cls, value: any) -> Tuple[AasTestResult, Optional[Environment]]:
    result_root = AasTestResult("Check")
    result_meta_model = AasTestResult("Skip meta model check")
    adapter = JsonAdapter(value, AdapterPath())
    env = parse(cls, adapter, result_meta_model)
    result_root.append(result_meta_model)  

    return result_root, env

def check_submodel_templates(json_data: dict):
    try:
        result, env = parse_env_without_meta(Environment, json_data)

        if env is not None:
            parse_submodel_templates(result, env)
            return {"status": "success", "submodel_verification": result.dump()}
        else:
            return {"status": "error", "message": "Failed to parse environment"}

    except Exception as e:
        return {"status": "error", "message": str(e)}