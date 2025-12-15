import sys, json, io
import json
from aas_test_engines.test_cases.v3_0.parse import check_constraints
from aas_test_engines.test_cases.v3_0.__init__ import json_to_obj
from aas_test_engines.test_cases.v3_0.adapter import AdapterPath, AdapterException
from aas_test_engines.result import AasTestResult
from api.response_handler import ErrorCode, error_response
from dataclasses import asdict


def run_constraint_check(file, model_type="Environment") -> str:
    try:
        if hasattr(file, "file"):
            file.file.seek(0)
            file_stream = io.TextIOWrapper(file.file, encoding="utf-8")
        else:
            file_stream = file

        data = json.load(file_stream)
        _, obj = json_to_obj(data, model_type=model_type)
####
        try:
            constraint_result = AasTestResult("Check")
            check_constraints(obj, constraint_result, AdapterPath())
        except Exception as e:
            constraint_result.append(AasTestResult(f"Constraint check failed: {e}"))
####
        # _, obj = json_to_obj(data, model_type=model_type)

        # constraint_result = AasTestResult("Check")
        # check_constraints(obj, constraint_result, AdapterPath())

        buffer = io.StringIO()
        sys.stdout = buffer
        constraint_result.dump()
        sys.stdout = sys.__stdout__
        output = buffer.getvalue()

        return output

    except Exception as e:
        msg = str(e)
        if "'AssetAdministrationShell' object has no attribute 'id_short_path'" in msg:
            return error_response(
                400,
                ErrorCode.INVALID_TEMPLATE
            )

        return error_response(
            500,
            ErrorCode.INTERNAL_SERVER_ERROR
        )
