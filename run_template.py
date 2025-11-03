import os, sys, json, io

from aas_test_engines.test_cases.v3_0.parse import check_constraints, _parse_and_check, parse,parse_and_check_json
from aas_test_engines.reflect import TypeBase
from aas_test_engines.test_cases.v3_0.__init__ import json_to_obj
from aas_test_engines.test_cases.v3_0.adapter import JsonAdapter, AdapterPath
from aas_test_engines.result import AasTestResult, Level
import aas_core3.jsonization as aas_jsonization
from aas_test_engines.file import check_json_data


def run_constraint_check(file) -> dict:
    buffer = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = buffer

    try:
        if hasattr(file, "file"):
            file.file.seek(0)
            file_stream = io.TextIOWrapper(file.file, encoding="utf-8")
        else:
            file_stream = file

        data = json.load(file_stream)

        result, obj = json_to_obj(data, model_type="Environment")

        constraint_result = AasTestResult("Constraint Check")
        check_constraints(obj, constraint_result, AdapterPath())    
        sys.stdout = old_stdout
        output = buffer.getvalue()

        return output

    except json.JSONDecodeError as e:
        return {
            "status": "error",
            "message": f"Invalid JSON: {e}",
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Internal error: {e}",
        }
