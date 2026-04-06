import sys, json, io
import importlib
from aas_test_engines.test_cases.v3_0.parse import check_constraints, CheckConstraintException
from aas_test_engines.test_cases.v3_0.adapter import AdapterPath
from aas_test_engines.result import AasTestResult
from api.response_handler import ErrorCode, error_response
from dataclasses import is_dataclass, fields


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


def safe_check_constraints(obj, result: AasTestResult, path: AdapterPath = AdapterPath()):
    if not is_dataclass(obj):
        return

    # 1) check_ 메서드들 실행 (예외는 전부 잡고 계속)
    fns = [getattr(obj, i) for i in dir(obj) if i.startswith("check_")]
    for fn in fns:
        try:
            fn()
        except CheckConstraintException as e:
            result.append(AasTestResult(f"{e} @ {path}", level=e.level))
        except Exception:
            pass

    for field in fields(obj):
        try:
            value = getattr(obj, field.name)
        except Exception:
            continue

        if isinstance(value, list):
            for idx, item in enumerate(value):
                safe_check_constraints(item, result, path + field.name + idx)
        else:
            safe_check_constraints(value, result, path + field.name)


ER_PATTERNS = (
    "AssetAdministrationShell' object has no attribute 'id_short_path'",
    "'object' object has no attribute 'id_short'"
    "'object' object has no attribute 'raw_value'",
)


def run_constraint_check(file, model_type="Environment") -> str:
    try:
        json_to_obj = _resolve_json_to_obj()
        if json_to_obj is None:
            return "Constraint check failed: json_to_obj is unavailable in current aas_test_engines version."

        if hasattr(file, "file"):
            file.file.seek(0)
            file_stream = io.TextIOWrapper(file.file, encoding="utf-8")
        else:
            file_stream = file

        data = json.load(file_stream)

        _, obj = json_to_obj(data, model_type=model_type)
        print(type(obj), getattr(obj, "__class__", None))

        constraint_result = AasTestResult("")
        try:
            safe_check_constraints(obj, constraint_result, AdapterPath())
        except Exception as e:
            print("[DBG] check_constraints raised:", repr(e))
            constraint_result.append(AasTestResult(f"Constraint check failed: {e}"))

        print("[DBG] sub_results count:", len(getattr(constraint_result, "sub_results", []) or []))

        buffer = io.StringIO()
        sys.stdout = buffer
        constraint_result.dump()
        sys.stdout = sys.__stdout__
        output = buffer.getvalue()

        lines = [ln.strip() for ln in output.splitlines() if ln.strip()]
        violations = [ln for ln in lines if ln.startswith("Constraint ")]
        failed = [ln for ln in lines if "Constraint check failed:" in ln]
        print("[DBG] violations:", len(violations), "failed:", len(failed))
        if failed:
            print("[DBG] failed head:", failed[0])

        return output

    except json.JSONDecodeError:
        return error_response(
            500,
            ErrorCode.INTERNAL_SERVER_ERROR
        )
