import io
import json
import sys
import importlib
from db.db_hadler import export_schema_to_py_file
sys.stdout.reconfigure(encoding="utf-8")


def _resolve_json_to_obj():
    candidates = [
        ("aas_test_engines.test_cases.v3_0", "json_to_obj"),
        ("aas_test_engines.test_cases.v3_0.parse", "json_to_obj"),
    ]
    for module_name, attr_name in candidates:
        try:
            module = importlib.import_module(module_name)
            fn = getattr(module, attr_name, None)
            if callable(fn):
                return fn
        except Exception:
            continue
    return None


def check_submodel_templates(file, model_type="Environment") -> str:
    try:
        try:
            from aas_test_engines.result import AasTestResult
            from aas_test_engines.test_cases.v3_0.submodel_templates import parse_submodel_templates
        except Exception as e:
            return f"Template: import\nAAS test engine import failed: {e}"

        json_to_obj = _resolve_json_to_obj()
        if json_to_obj is None:
            return "Template: import\njson_to_obj is not available in installed aas_test_engines version."

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
            instance_result = AasTestResult('Check instance')
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
        return f"Template: runtime\nInstance check failed: {e}"
