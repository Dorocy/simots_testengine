# import sys
# sys.stdout.reconfigure(encoding="utf-8")

# import json
# from typing import Tuple, Optional
# from aas_test_engines.test_cases.v3_0.parse import parse
# from aas_test_engines.test_cases.v3_0.adapter import JsonAdapter, AdapterPath
# from aas_test_engines.test_cases.v3_0.submodel_templates import parse_submodel_templates
# from aas_test_engines.result import AasTestResult
# from aas_test_engines.test_cases.v3_0.model import Environment


# def parse_env_without_meta(cls, value: any) -> Tuple[AasTestResult, Optional[Environment]]:
#     result_root = AasTestResult("Check")
#     result_meta_model = AasTestResult("Skip meta model check")

#     adapter = JsonAdapter(value, AdapterPath())
#     env = parse(cls, adapter, result_meta_model)
#     result_root.append(result_meta_model)  

#     return result_root, env

# def check_submodel_templates(file_path: str):
#     with open(file_path, "r", encoding="utf-8") as file:
#         data = json.load(file)

#     result, env = parse_env_without_meta(Environment, data)

#     if env is not None: # 추후에 수정해야 할 수 있음
#         parse_submodel_templates(result, env)
#     else:
#         print("Failed to parse environment")

#     return result

# json_file_path = "c:/Users/Lenovo/Desktop/smt/URRobotAAS_v3_DN+TD.json"

# result = check_submodel_templates(json_file_path)

# result.dump()
