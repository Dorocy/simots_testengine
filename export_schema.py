import sys
sys.stdout.reconfigure(encoding="utf-8")
import json
from typing import Optional, List
from dataclasses import dataclass, field
import re
from enum import Enum

# JSON 파일 로드
with open('C:/Users/Lenovo/Desktop/smt/testsmt/IDTA_02003-1-2_Template_TechnicalData.json', 'r') as file:
    data = json.load(file)

result = []
class_definitions = []
enum_definitions = []
generated_classes = set()
generated_enums = set()

def to_snake_case(s: str) -> str:
    s = s.replace(" ", "_") 
    s = re.sub(r'([a-z])([A-Z])', r'\1_\2', s)
    return s.lower()

def to_pascal_case(s: str) -> str:
    return ''.join(word.capitalize() for word in s.split('_'))

def generate_class(name: str, fields: List[str], semantic_id: str = None):
    class_body = "@dataclass\n"
    if semantic_id:
        class_body += f"@template(\"{semantic_id}\")\n"
    class_body += f"class {name}:\n"
    for field_def in fields:
        class_body += f"    {field_def}\n"
    return class_body

def generate_enum(name: str, values: List[str]):
    enum_body = f"class {name}(Enum):\n"
    for item in values:
        label, value = item
        snake_case_label = to_snake_case(label)
        enum_body += f"    {snake_case_label} = \"{value}\"\n"
    return enum_body

def extract_values(value):
    if not isinstance(value, dict):  # value가 dict인지 확인
        print(f"value type {type(value)}: {value}")
        return ""  # 잘못된 경우 빈 문자열 반환
    
    id_short = value.get("idShort")
    if not id_short:
        return ""

    
    semantic_id_value = None
    if "semanticId" in value:
        semantic_id_value = value["semanticId"]["keys"][0].get("value")
    elif "supplementalSemanticIds" in value:
        semantic_id_value = value["supplementalSemanticIds"]["keys"][0].get("value")

    qualifiers_value = value.get("qualifiers", [{}])[0].get("value", "Optional")
    model_type = value.get("modelType")
    
    snake_case_id_short = to_snake_case(id_short)
    pascal_case_id_short = to_pascal_case(snake_case_id_short)
    
    value_type = 'str'

    if "description" in value:
        for desc in value["description"]:
            if "text" in desc and "enumeration:" in desc["text"]:
                enum_entries = desc["text"].replace("enumeration:", "").strip().split(", ")
                enum_values = []
                for entry in enum_entries:
                    match = re.match(r"(.+?) \((.+?)\)", entry)  # "값 (라벨)" 형태 분리
                    if match:
                        enum_values.append((to_snake_case(match.group(2)), match.group(1)))  # (라벨, 값)
                        model_type="SubmodelElementCollection"

                # Enum 클래스 생성
                if pascal_case_id_short not in generated_enums:
                    enum_definitions.append(generate_enum(pascal_case_id_short, enum_values))
                    generated_enums.add(pascal_case_id_short)
                value_type = pascal_case_id_short
                break
    
    # valueType 결정
    if model_type == "MultiLanguageProperty":
        value_type = 'LangString'
    elif model_type in ["Property", "File"]:
        value_type = 'str'
    elif model_type == "SubmodelElementCollection":
        value_type = pascal_case_id_short
    elif model_type == 'Entity':
        value_type = "EntType"
    
    # Optional 결정
    if qualifiers_value == "One":
        type_annotation = value_type
    elif qualifiers_value in ["ZeroToOne", "optional"]:
        type_annotation = f"Optional[{value_type}]"
    elif qualifiers_value == "ZeroToMany":
        type_annotation = f"Optional[List[{value_type}]]"
    elif qualifiers_value == "OneToMany": # 추가
        type_annotation = f"List[{value_type}]"
    else:
        type_annotation = f"Optional[{value_type}]"  # 기본값
    
    if model_type == "SubmodelElementCollection":
        sub_fields = []
        for sub_value in value.get("value", []):  # "value"가 있으면 반복
            sub_field = extract_values(sub_value)
            if sub_field:
                sub_fields.append(sub_field)

        if pascal_case_id_short not in generated_classes:
            class_definitions.append(generate_class(value_type, sub_fields))
            generated_classes.add(pascal_case_id_short)

    field_definition = f"{snake_case_id_short}: {type_annotation} = field(metadata={{\n    'semantic_id': '{semantic_id_value}'\n}})"

    if field_definition not in result:
        result.append(field_definition)
    return field_definition

def process_submodel_elements(name: str, elements: List[dict], is_top_level: bool = False, top_level_semantic_id: str = ""):
    fields = []
    sub_class_names = set()
    
    for element in elements:
        sub_element_field = extract_values(element)
        if sub_element_field:
            fields.append(sub_element_field)
        
        sub_elements = element.get("value", [])
        if sub_elements:
            sub_class_name = to_pascal_case(to_snake_case(element["idShort"]))
            sub_class_names.add(sub_class_name)
            if sub_class_name not in generated_classes:
                process_submodel_elements(sub_class_name, sub_elements, top_level_semantic_id=top_level_semantic_id)
                generated_classes.add(sub_class_name)
    
    if name not in generated_classes:
        class_def = generate_class(name, fields, top_level_semantic_id if is_top_level else None)
        class_definitions.append(class_def)
        generated_classes.add(name)

# 첫 번째 submodel의 semanticId.keys[0].value 값 가져옴
top_level_semantic_id = ""
if data.get("submodels"):
    first_submodel = data["submodels"][0]
    top_level_semantic_id = first_submodel.get("semanticId", {}).get("keys", [{}])[0].get("value", "")

# 모든 submodel 처리
for i, submodel in enumerate(data.get("submodels", [])):
    submodel_id_short = submodel.get("idShort")
    if submodel_id_short:
        pascal_case_id_short = to_pascal_case(to_snake_case(submodel_id_short))
        first_level_elements = submodel.get("submodelElements", [])
        process_submodel_elements(pascal_case_id_short, first_level_elements, is_top_level=(i == 0), top_level_semantic_id=top_level_semantic_id)

# 모든 클래스 출력
for class_def in class_definitions:
    print(class_def)