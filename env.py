import json
from aas_test_engines.test_cases.v3_0.parse import JsonAdapter, AdapterPath
from aas_test_engines.test_cases.v3_0.result import AasTestResult
from aas_test_engines.test_cases.v3_0.parse import parse
from aas_test_engines.test_cases.v3_0.model import r_environment

# JSON 파일 읽기
with open("warning_only.json", "r", encoding="utf-8") as f:
    json_data = json.load(f)

# Adapter 생성
adapter = JsonAdapter(json_data, AdapterPath())

# meta model 검사 결과 객체
result_meta_model = AasTestResult("Check meta model")

# parse 호출 → env 객체 생성
env = parse(r_environment, adapter, result_meta_model)
