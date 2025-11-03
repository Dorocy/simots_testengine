import os, sys, json, io
from dataclasses import asdict
import json

from aas_test_engines.test_cases.v3_0.parse import check_constraints, _parse_and_check, parse,parse_and_check_json
from aas_test_engines.reflect import  (TypeBase, StringFormattedValue, reflect,
    TypeBase,
    ListType,
    ClassType,
    StringFormattedValueType,
    EnumType,
    StringType,
    BoolType,
    AnyType,
)
from aas_test_engines.test_cases.v3_0.__init__ import json_to_obj
from aas_test_engines.test_cases.v3_0.adapter import JsonAdapter, AdapterPath, Adapter
from aas_test_engines.test_cases.v3_0.model import (
    Environment,
    Submodel,
    SubmodelElement,
    Key,
    Reference,
    Property,
    ValueReferencePair,
    RelationshipElement,
    ConceptDescription
)
from aas_test_engines.result import AasTestResult, Level
import aas_core3.jsonization as aas_jsonization
from aas_test_engines.file import check_json_data

# ## 완성
# def run_constraint_check(file) -> dict:
#     try:
#         if hasattr(file, "file"):
#             file.file.seek(0)
#             file_stream = io.TextIOWrapper(file.file, encoding="utf-8")
#         else:
#             file_stream = file

#         data = json.load(file_stream)

#         result, obj = json_to_obj(data, model_type="Environment")

#         constraint_result = AasTestResult("Check Constraint")
#         print('제약조건 검사 시작')
#         check_constraints(obj, constraint_result, AdapterPath())
#         print('제약조건 검사 끝')

#         buffer = io.StringIO()
#         sys.stdout = buffer
#         print(constraint_result.dump())  # 없으면 안 됨!! 콘솔에 출력하기 위해서,,, 필수임
#         sys.stdout = sys.__stdout__
#         output = buffer.getvalue()
#         return output

#     except json.JSONDecodeError as e:
#         return {
#             "status": "error",
#             "message": f"Invalid JSON: {e}",
#         }

#     except Exception as e:
#         return {
#             "status": "error",
#             "message": f"Internal error: {e}",
#         }

def run_constraint_check(file, model_type="Environment") -> str:
    try:
        # 파일 혹은 스트림 처리
        if hasattr(file, "file"):
            file.file.seek(0)
            file_stream = io.TextIOWrapper(file.file, encoding="utf-8")
        else:
            file_stream = file

        data = json.load(file_stream)

        result, obj = json_to_obj(data, model_type=model_type)
        # print('obj: ', obj)
        try:
            test_Rresult=[]
            for i in (0, 5):
                i=0
                constraint_result = AasTestResult("Check")
                check_constraints(obj, constraint_result, AdapterPath())
                test_Rresult.append(constraint_result.dump())
                print('FOR문에서 한문장씩', test_Rresult)
                i+=1
                
            
            print('전체문장',test_Rresult)
            # t = 

            print('durlsms', t)
            constraint_result.append(AasTestResult(f"Constraint check success: {t}"))
        except Exception as e:
            # constraint 검사 중 예외 발생 시 기록
            constraint_result.append(AasTestResult(f"Constraint check failed: {e}"))

        # 문자열로 변환
        buffer = io.StringIO()
        sys.stdout = buffer
        print(constraint_result.dump())  # 반드시 print
        sys.stdout = sys.__stdout__
        output = buffer.getvalue()

        return output

    except json.JSONDecodeError as e:
        return f"Check\n   Invalid JSON: {e}"

    except Exception as e:
        return f"Check\n   Internal error: {e}"
