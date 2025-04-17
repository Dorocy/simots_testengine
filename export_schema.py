import sys
import json
sys.stdout.reconfigure(encoding="utf-8")

from typing import Optional, List
from dataclasses import dataclass, field
import re
from enum import Enum


# JSON 파일 로드
with open(
    "./sample_files/schema_sample/IDTA_02004-1-2_Template_Handover_Documentation.json",
    "r",
) as file:
    data = json.load(file)

result = []
class_definitions = []
enum_definitions = []
generated_classes = set()
generated_enums = set()


def to_snake_case(s: str) -> str:
    s = s.replace(" ", "_")
    s = re.sub(r"([a-z])([A-Z])", r"\1_\2", s)
    return s.lower()


def to_pascal_case(s: str) -> str:
    return "".join(word.capitalize() for word in s.split("_"))


def generate_dataclass(name: str, fields: List[str], semantic_id: str = None):
    class_body = "@dataclass\n"
    if semantic_id:
        class_body += f'@template("{semantic_id}")\n'
    class_body += f"class {name}:\n"
    for field_def in fields:
        class_body += f"    {field_def}\n"
    return class_body


def generate_enum(name: str, values: List[str]):
    enum_body = f"class {name}(Enum):\n"
    for item in values:
        label, value = item
        snake_case_label = to_snake_case(label)
        enum_body += f'    {snake_case_label} = "{value}"\n'
    return enum_body


def extract_values(value, parent_name=None):
    if not isinstance(value, dict):
        return ""

    id_short = value.get("idShort")

    semantic_id_value = None
    if "semanticId" in value:
        semantic_id_value = value["semanticId"]["keys"][0].get("value")
    else:
        pass

    qualifiers_value = value.get("qualifiers", [{}])[0].get("value")
    model_type = value.get("modelType")

    snake_case_id_short = to_snake_case(id_short)
    pascal_case_id_short = to_pascal_case(snake_case_id_short)

    value_type = "str"

    if "description" in value:
        for desc in value["description"]:
            if "text" in desc and "enumeration:" in desc["text"]:
                enum_entries = (
                    desc["text"].replace("enumeration:", "").strip().split(", ")
                )
                enum_values = []
                for entry in enum_entries:
                    match = re.match(r"(.+?) \((.+?)\)", entry)
                    if match:
                        enum_values.append(
                            (to_snake_case(match.group(2)), match.group(1))
                        )
                        model_type = "SubmodelElementCollection"

                if pascal_case_id_short not in generated_enums:
                    enum_definitions.append(
                        generate_enum(pascal_case_id_short, enum_values)
                    )
                    generated_enums.add(pascal_case_id_short)
                value_type = pascal_case_id_short
                break

    if model_type == "MultiLanguageProperty":
        value_type = "LangString"
    elif model_type in ["Property", "File"]:
        value_type = "str"
    elif model_type == "SubmodelElementCollection":
        if not value.get("value"):
            value_type = "str"
        else:
            value_type = pascal_case_id_short
    elif model_type == "SubmodelElementList":
        value_type = pascal_case_id_short
    elif model_type == "Entity":
        value_type = "EntType"
    elif model_type == "ReferenceElement":
        value_type = "RefType"

    if qualifiers_value == "One":
        type_annotation = value_type
    elif qualifiers_value in ["ZeroToOne", "optional"]:
        type_annotation = f"Optional[{value_type}]"
    elif qualifiers_value == "ZeroToMany":
        type_annotation = f"Optional[List[{value_type}]]"
    elif qualifiers_value == "OneToMany":
        type_annotation = f"List[{value_type}]"
    else:
        type_annotation = f"Optional[{value_type}]"

    if model_type == "SubmodelElementList":
        sub_fields = []
        for sub_value in value.get("value", []):
            if isinstance(sub_value, dict):  # value가 dict인지 확인
                # typevaluelistelement 요소만 필터링
                if sub_value.get("modelType") == "typevaluelistelement":
                    sub_field = extract_values(sub_value)
                    if sub_field:
                        sub_fields.append(sub_field)

        if pascal_case_id_short not in generated_classes:
            class_definitions.append(generate_dataclass(value_type, sub_fields))
            generated_classes.add(pascal_case_id_short)

    if model_type == "SubmodelElementCollection":
        if value.get("value"):
            sub_fields = []
            for sub_value in value.get("value", []):
                if isinstance(sub_value, dict):  # value가 dict인지 확인
                    sub_field = extract_values(sub_value)
                    if sub_field:
                        sub_fields.append(sub_field)

    field_definition = f"{snake_case_id_short}: {type_annotation} = field(metadata={{\n    'semantic_id': '{semantic_id_value}'\n}})"

    if field_definition not in result:
        result.append(field_definition)

    return field_definition


def process_submodel_elements(
    name: str,
    elements: List[dict],
    is_top_level: bool = False,
    top_level_semantic_id: str = "",
):
    fields = []
    sub_class_names = set()

    for element in elements:
        if not isinstance(element, dict):
            continue  # dict가 아닌 값은 무시

        sub_elements = element.get("value", [])
        model_type = element.get("modelType", "")
        id_short = element.get("idShort", "")

        if not id_short:
            continue

        pascal_case_id_short = to_pascal_case(to_snake_case(id_short))

        # description에서 enumeration이 있는 경우 enum 생성
        if "description" in element:
            for desc in element["description"]:
                if "text" in desc and "enumeration:" in desc["text"]:
                    enum_entries = (
                        desc["text"].replace("enumeration:", "").strip().split(", ")
                    )
                    enum_values = []
                    for entry in enum_entries:
                        match = re.match(r"(.+?) \((.+?)\)", entry)
                        if match:
                            enum_values.append(
                                (to_snake_case(match.group(2)), match.group(1))
                            )

                    if pascal_case_id_short not in generated_enums:
                        enum_definitions.append(
                            generate_enum(pascal_case_id_short, enum_values)
                        )
                        generated_enums.add(pascal_case_id_short)

        sub_element_field = extract_values(element)
        if sub_element_field:
            fields.append(sub_element_field)

        # 특정 modelType인 경우에만 클래스 생성
        if model_type == "SubmodelElementCollection" and isinstance(sub_elements, list):
            sub_class_name = to_pascal_case(to_snake_case(element["idShort"]))

            if not sub_elements:
                continue

            sub_class_names.add(sub_class_name)
            if sub_class_name not in generated_classes:
                process_submodel_elements(
                    sub_class_name,
                    sub_elements,
                    top_level_semantic_id=top_level_semantic_id,
                )
                generated_classes.add(sub_class_name)

    if name not in generated_classes:
        class_def = generate_dataclass(
            name, fields, top_level_semantic_id if is_top_level else None
        )
        class_definitions.append(class_def)
        generated_classes.add(name)


# 첫 번째 submodel의 semanticId.keys[0].value 값 가져옴
top_level_semantic_id = ""
if data.get("submodels"):
    first_submodel = data["submodels"][0]
    top_level_semantic_id = (
        first_submodel.get("semanticId", {}).get("keys", [{}])[0].get("value", "")
    )

# 모든 submodel 처리
for i, submodel in enumerate(data.get("submodels", [])):
    submodel_id_short = submodel.get("idShort")
    if submodel_id_short:
        pascal_case_id_short = to_pascal_case(to_snake_case(submodel_id_short))
        first_level_elements = submodel.get("submodelElements", [])
        process_submodel_elements(
            pascal_case_id_short,
            first_level_elements,
            is_top_level=(i == 0),
            top_level_semantic_id=top_level_semantic_id,
        )

# print("\n".join(enum_definitions))
# print("\n".join(class_definitions))


def get_schema_result(data):
    result.clear()
    class_definitions.clear()
    enum_definitions.clear()
    generated_classes.clear()
    generated_enums.clear()

    top_level_semantic_id = ""
    if data.get("submodels"):
        first_submodel = data["submodels"][0]
        top_level_semantic_id = (
            first_submodel.get("semanticId", {}).get("keys", [{}])[0].get("value", "")
        )

    for i, submodel in enumerate(data.get("submodels", [])):
        submodel_id_short = submodel.get("idShort")
        if submodel_id_short:
            pascal_case_id_short = to_pascal_case(to_snake_case(submodel_id_short))
            first_level_elements = submodel.get("submodelElements", [])
            process_submodel_elements(
                pascal_case_id_short,
                first_level_elements,
                is_top_level=(i == 0),
                top_level_semantic_id=top_level_semantic_id,
            )

    # 원래 콘솔 출력 형식 유지 + 줄바꿈 적용
    schema_output = "\n".join(enum_definitions + class_definitions)

    return {"schema": schema_output}  # JSON에서 개행 문자 유지
