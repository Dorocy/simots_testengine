import sys
sys.stdout.reconfigure(encoding="utf-8")
from typing import Tuple, Optional
from aas_test_engines.test_cases.v3_0.parse import parse
from aas_test_engines.test_cases.v3_0.submodel_templates import parse_submodel_templates
from aas_test_engines.test_cases.v3_0.adapter import JsonAdapter, AdapterPath
from aas_test_engines.result import AasTestResult
from aas_test_engines.test_cases.v3_0.model import Environment, Submodel
from typing import List
from utils.db_hadler import export_schema_to_py_file
import schema_files.test_schema as schemas
templates = {}


def parse_env_without_meta(
    cls, value: any
) -> Tuple[AasTestResult, Optional[Environment]]:
    result_root = AasTestResult("") #durl rh
    result_meta_model = AasTestResult("")
    adapter = JsonAdapter(value, AdapterPath())
    env = parse(cls, adapter, result_meta_model)
    result_root.append(result_meta_model)

    return result_root, env


def check_submodel_templates(json_data: dict):
    try:
        result, env = parse_env_without_meta(Environment, json_data)
        if env is None:
            return

        # submodel의 semantic_id 수집
        submodel_ids = []
        for submodel in env.submodels or []:
            if submodel.semantic_id and submodel.semantic_id.keys:
                sid = submodel.semantic_id.keys[0].value.raw_value
                if sid not in submodel_ids:
                    submodel_ids.append(sid)

        # 수집한 모든 submodel_id로 schema export
        if submodel_ids:
            export_schema_to_py_file(submodel_ids)

        # submodel 검사 실행
        parse_submodel_templates(result, env)
        return (result.dump())

    except Exception as e:
        print(f"[Template Check Error] {e}")