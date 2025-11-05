import sys, io, json
sys.stdout.reconfigure(encoding="utf-8")
from aas_test_engines.test_cases.v3_0.__init__ import json_to_obj
from aas_test_engines.test_cases.v3_0.submodel_templates import parse_submodel_templates
from aas_test_engines.result import AasTestResult
from db.db_hadler import export_schema_to_py_file
from api.response_handler import ErrorCode, error_response
templates = {}


def check_submodel_templates(file, model_type="Environment") -> str:
    try:
        if hasattr(file, "file"):
            file.file.seek(0)
            file_stream = io.TextIOWrapper(file.file, encoding="utf-8")
        else:
            file_stream = file

        data = json.load(file_stream)
        result, obj = json_to_obj(data, model_type=model_type)

        submodel_ids = []
        for submodel in obj.submodels or []:
            if submodel.semantic_id and submodel.semantic_id.keys:
                sid = submodel.semantic_id.keys[0].value.raw_value
                if sid not in submodel_ids:
                    submodel_ids.append(sid)

        if submodel_ids:
            export_schema_to_py_file(submodel_ids)

        try:
            instance_result = AasTestResult("Check instance")
            parse_submodel_templates(instance_result, obj)

        except Exception as e:
            instance_result.append(AasTestResult(f"Instance check failed: {e}"))

        buffer = io.StringIO()
        sys.stdout = buffer
        instance_result.dump()
        sys.stdout = sys.__stdout__
        output = buffer.getvalue()

        return output

    except Exception as e:
        return error_response(
            400,
            ErrorCode.INVALID_JSON_FORMAT,
            str(e)
            )
