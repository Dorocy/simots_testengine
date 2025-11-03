import sys, io, json
sys.stdout.reconfigure(encoding="utf-8")
from typing import Tuple, Optional
from aas_test_engines.test_cases.v3_0.parse import parse
from aas_test_engines.test_cases.v3_0.__init__ import json_to_obj
from aas_test_engines.test_cases.v3_0.submodel_templates import parse_submodel_templates
from aas_test_engines.test_cases.v3_0.adapter import JsonAdapter, AdapterPath
from aas_test_engines.result import AasTestResult
from aas_test_engines.test_cases.v3_0.model import Environment, r_environment, Submodel
from typing import List
from utils.db_hadler import export_schema_to_py_file
# import schema_files.test_schema as schemas
templates = {}


def parse_env_without_meta(
    cls, value: any
) -> Tuple[AasTestResult, Optional[r_environment]]:
    result_root = AasTestResult("")
    result_meta_model = AasTestResult("")
    adapter = JsonAdapter(value, AdapterPath())
    env = parse(cls, adapter, result_meta_model)
    print(env)
    result_root.append(result_meta_model)

    return result_root, env


def check_submodel_templates(file):
    try:
        result, env = json_to_obj(file, r_environment)
        file.file.seek(0)
        file_stream = io.TextIOWrapper(file.file, encoding="utf-8")
        data = json.load(file_stream)

        result, obj = json_to_obj(data, model_type="Environment")

        if env is None:
            print('env error')
            return result

        submodel_ids = []
        for submodel in env.submodels or []:
            if submodel.semantic_id and submodel.semantic_id.keys:
                sid = submodel.semantic_id.keys[0].value.raw_value
                if sid not in submodel_ids:
                    submodel_ids.append(sid)

        if submodel_ids:
            export_schema_to_py_file(submodel_ids)

        parse_submodel_templates(result, env)
        return (result.dump())

    except Exception as e:
        print(f"[Template Check Error] {e}")
        return AasTestResult("Check Submodel Templates")

# def check_submodel_templates(json_data: dict):
#     try:
#         result, env = parse_env_without_meta(Environment, json_data)

#         if env is not None:
#             parse_submodel_templates(result, env)
#             return {"status": "success", "submodel_verification": result.dump()}
#         else:
#             return {"status": "error", "message": "Failed to parse environment"}

#     except Exception as e:
#         return {"status": "error", "message": str(e)}