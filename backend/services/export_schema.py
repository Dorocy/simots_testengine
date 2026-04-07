import sys
import re
import json
sys.stdout.reconfigure(encoding="utf-8")
from typing import List
from db.db_hadler import connect_and_insert, extract_semantic_id
from utils.data_type import SchemaGroup


# schema = SchemaGroup()


# def to_snake_case(s: str) -> str:
#     s = s.replace(" ", "_")
#     s = re.sub(r"([a-z])([A-Z])", r"\1_\2", s)
#     return s.lower()


# def to_pascal_case(s: str) -> str:
#     return "".join(word.capitalize() for word in s.split("_"))


# def generate_dataclass(name: str, fields: List[str], semantic_id: str = None):
#     class_body = "@dataclass\n"
#     if semantic_id:
#         class_body += f'@template("{semantic_id}")\n'
#     class_body += f"class {name}:\n"
#     for field_def in fields:
#         class_body += f"    {field_def}\n"
#     return class_body


# def generate_enum(name: str, values: List[str]):
#     return "class {}(Enum):\n{}".format(
#         name,
#         "".join(f'    {to_snake_case(label)} = "{value}"\n' for label, value in values)
#     )


# def get_valid_id_short(id_short_raw):
#     global unnamed_element_counter
#     id_short = (id_short_raw or "").strip()
#     if not id_short:
#         id_short = f"UnnamedElement_{unnamed_element_counter}"
#         unnamed_element_counter += 1
#     return id_short


# def get_enumeration(element, class_name):
#     descriptions = element.get("description", [])
#     for desc in descriptions:
#         text = desc.get("text", "")
#         if not text.strip().startswith("enumeration:"):
#             continue

#         entries = text.replace("enumeration:", "").strip().split(", ")
#         enum_values = []
#         for entry in entries:
#             # print("entries: ", entries, '\n')
#             # print("entry: ", entry, '\n')
#             match = re.match(r"(.+?) \((.+?)\)", entry)
#             if match:
#                 # print("match: ", match, '\n''\n''\n')
#                 enum_values.append((to_snake_case(match.group(2)), match.group(1)))

#         if class_name not in schema.generated_enums:
#             schema.enum_definitions.append(generate_enum(class_name, enum_values))
#             schema.generated_enums.add(class_name)


# def get_submodel_collection(element, sub_elements, top_level_semantic_id):
#     sub_class_name = to_pascal_case(to_snake_case(element["idShort"]))
#     if not sub_elements or sub_class_name in schema.generated_classes:
#         return

#     process_submodel_elements(
#         sub_class_name,
#         sub_elements,
#         top_level_semantic_id=top_level_semantic_id,
#     )
#     schema.generated_classes.add(sub_class_name)


# def get_submodel_list(element, sub_elements, top_level_semantic_id):
#     list_name = to_pascal_case(to_snake_case(element.get("idShort", "ListElement")))
#     for sub_element in sub_elements:
#         if sub_element.get("modelType") == "SubmodelElementCollection":
#             process_submodel_elements(list_name, sub_element.get("value", []))
#         else:
#             process_submodel_elements(list_name, [sub_element])

#     if list_name not in schema.generated_classes:
#         schema.class_definitions.append(generate_dataclass(list_name, []))
#         schema.generated_classes.add(list_name)


# # def process_submodel_elements(
# #     name: str,
# #     elements: List[dict],
# #     is_top_level: bool = False,
# #     top_level_semantic_id: str = "",
# # ):
# #     fields = []
# #     # print("name: ", name, '\n')
# #     # print("elements: ", elements, '\n''\n')

# #     for element in elements:
# #         if not isinstance(element, dict):
# #             continue

# #         id_short = get_valid_id_short(element.get("idShort"))
# #         pascal_name = to_pascal_case(to_snake_case(id_short))
# #         model_type = element.get("modelType", "")
# #         sub_elements = element.get("value", [])

# #         get_enumeration(element, pascal_name)

# #         sub_element_field = extract_values(element)
# #         if sub_element_field:
# #             fields.append(sub_element_field)

# #         if model_type == "SubmodelElementCollection":
# #             get_submodel_collection(element, sub_elements, top_level_semantic_id)

# #         if model_type == "SubmodelElementList":
# #             get_submodel_list(element, sub_elements, top_level_semantic_id)

# #     if name not in schema.generated_classes:
# #         schema.class_definitions.append(
# #             generate_dataclass(name, fields, top_level_semantic_id if is_top_level else None)
# #         )
# #         schema.generated_classes.add(name)


# def process_submodel_elements(
#     name: str,
#     elements: List[dict],
#     is_top_level: bool = False,
#     top_level_semantic_id: str = "",
# ):
#     fields = []
#     sub_class_names = set()

#     for element in elements:
#         if not isinstance(element, dict):
#             continue  # dict가 아닌 값은 무시

#         sub_elements = element.get("value", [])
#         model_type = element.get("modelType", "")
#         id_short = element.get("idShort", "")

#         if not id_short:
#             continue
#         id_short_raw = element.get("idShort")
#         id_short = get_valid_id_short(id_short_raw)

#         pascal_case_id_short = to_pascal_case(to_snake_case(id_short))

#         # description에서 enumeration이 있는 경우 enum 생성
#         if "description" in element:
#             for desc in element["description"]:
#                 if "text" in desc and "enumeration:" in desc["text"]:
#                     enum_entries = (
#                         desc["text"].replace("enumeration:", "").strip().split(", ")
#                     )
#                     enum_values = []
#                     for entry in enum_entries:
#                         match = re.match(r"(.+?) \((.+?)\)", entry)
#                         if match:
#                             enum_values.append(
#                                 (to_snake_case(match.group(2)), match.group(1))
#                             )

#                     if pascal_case_id_short not in schema.enerated_enums:
#                         schema.enum_definitions.append(
#                             generate_enum(pascal_case_id_short, enum_values)
#                         )
#                         schema.generated_enums.add(pascal_case_id_short)

#         sub_element_field = extract_values(element)
#         if sub_element_field:
#             fields.append(sub_element_field)

#         if model_type == "SubmodelElementCollection" and isinstance(sub_elements, list):
#             sub_class_name = to_pascal_case(to_snake_case(element["idShort"]))

#             if not sub_elements:
#                 continue

#             sub_class_names.add(sub_class_name)
#             if sub_class_name not in schema.generated_classes:
#                 process_submodel_elements(
#                     sub_class_name,
#                     sub_elements,
#                     top_level_semantic_id=top_level_semantic_id,
#                 )
#                 schema.generated_classes.add(sub_class_name)

#     if name not in schema.generated_classes:
#         class_def = generate_dataclass(
#             name, fields, top_level_semantic_id if is_top_level else None
#         )
#         schema.class_definitions.append(class_def)
#         schema.generated_classes.add(name)


# def extract_values(value, parent_name=None):
#     if not isinstance(value, dict):
#         return ""

#     id_short_raw = value.get("idShort", "")
#     id_short = get_valid_id_short(id_short_raw)
#     semantic_id_value = value.get("semanticId", {}).get("keys", [{}])[0].get("value")
#     qualifiers_value = value.get("qualifiers", [{}])[0].get("value")
#     model_type = value.get("modelType", "")
#     snake_case_id_short = to_snake_case(id_short)
#     pascal_case_id_short = to_pascal_case(snake_case_id_short)

#     model_type_map = {
#         "MultiLanguageProperty": "LangString",
#         "Property": "str",
#         "File": "str",
#         "Entity": "EntType",
#         "ReferenceElement": "RefType",
#     }

#     if model_type == "SubmodelElementCollection":
#         value_type = pascal_case_id_short if value.get("value") else "str"
#     elif model_type == "SubmodelElementList":
#         value_type = pascal_case_id_short
#     else:
#         value_type = model_type_map.get(model_type, "str")

#     qualifier_map = {
#         "One": "{t}",
#         "ZeroToOne": "Optional[{t}]",
#         "optional": "Optional[{t}]",
#         "ZeroToMany": "Optional[List[{t}]]",
#         "OneToMany": "List[{t}]",
#     }

#     type_annotation = qualifier_map.get(
#         qualifiers_value, "Optional[{t}]"
#     ).format(t=value_type)

#     field_definition = (
#         f"{snake_case_id_short}: {type_annotation} = field(metadata={{\n"
#         f"    'semantic_id': '{semantic_id_value}'\n}})"
#     )

#     if field_definition not in schema.result:
#         schema.result.append(field_definition)

#     return field_definition


# def get_schema_result(data):

#     top_level_semantic_id = ""
#     if data.get("submodels"):
#         first_submodel = data["submodels"][0]
#         top_level_semantic_id = (
#             first_submodel.get("semanticId", {}).get("keys", [{}])[0].get("value", "")
#         )
#     for i, submodel in enumerate(data.get("submodels", [])):
#         submodel_id_short = submodel.get("idShort")
#         if submodel_id_short:
#             pascal_case_id_short = to_pascal_case(to_snake_case(submodel_id_short))
#             first_level_elements = submodel.get("submodelElements", [])
#             process_submodel_elements(
#                 pascal_case_id_short,
#                 first_level_elements,
#                 is_top_level=(i == 0),
#                 top_level_semantic_id=top_level_semantic_id,
#             )

#     schema_output = "\n".join(schema.enum_definitions + schema.class_definitions)
#     print(schema_output)
#     return connect_and_insert(data, schema_output)


# def generate_schema_code(data: dict) -> tuple[str, bytes]:

#     top_level_semantic_id = ""
#     if data.get("submodels"):
#         first_submodel = data["submodels"][0]
#         top_level_semantic_id = (
#             first_submodel.get("semanticId", {}).get("keys", [{}])[0].get("value", "")
#         )
#     for i, submodel in enumerate(data.get("submodels", [])):
#         submodel_id_short = submodel.get("idShort")
#         if submodel_id_short:
#             pascal_case_id_short = to_pascal_case(to_snake_case(submodel_id_short))
#             first_level_elements = submodel.get("submodelElements", [])
#             process_submodel_elements(
#                 pascal_case_id_short,
#                 first_level_elements,
#                 is_top_level=(i == 0),
#                 top_level_semantic_id=top_level_semantic_id,
#             )

#     schema_output = "\n".join(schema.enum_definitions + schema.class_definitions)
#     binary_data = schema_output.encode("utf-8")

#     print(binary_data)

#     return binary_data


import sys
import re
import json
sys.stdout.reconfigure(encoding="utf-8")
from typing import Optional, List
from dataclasses import dataclass, field
from enum import Enum
from db.db_hadler import connect_and_insert


result = []
class_definitions = []
enum_definitions = []
generated_classes = set()
generated_enums = set()
unnamed_element_counter = 0


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


def get_valid_id_short(id_short_raw):
    global unnamed_element_counter
    id_short = (id_short_raw or "").strip()
    if id_short == "":
        id_short = f"UnnamedElement_{unnamed_element_counter}"
        unnamed_element_counter += 1
    return id_short


def extract_values(value, parent_name=None):
    if not isinstance(value, dict):
        return ""

    id_short_raw = value.get("idShort", "")
    id_short = get_valid_id_short(id_short_raw)

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
            if isinstance(sub_value, dict):
                sub_field = extract_values(sub_value)
                if sub_field:
                    sub_fields.append(sub_field)

        if pascal_case_id_short not in generated_classes:
            class_definitions.append(generate_dataclass(value_type, sub_fields))
            generated_classes.add(pascal_case_id_short)

    if model_type == "SubmodelElementCollection":
        if value.get("value"):
            # 이 시점에서 value가 list인지 확인
            sub_values = value["value"]
            contains_arbitrary = any(
                isinstance(sub, dict)
                and "idShort" in sub
                and "Arbitrary" in sub["idShort"]
                for sub in sub_values
            )

            if contains_arbitrary:
                # Arbitrary가 포함된 경우: SMC까지만 생성하고 하위는 무시
                sub_fields = []  # 빈 리스트
                sub_fields.append("pass")
            else:
                # Arbitrary가 없으면 하위까지 모두 처리
                sub_fields = []
                for sub_value in sub_values:
                    if isinstance(sub_value, dict):
                        sub_field = extract_values(sub_value)
                        if sub_field:
                            sub_fields.append(sub_field)

            if pascal_case_id_short not in generated_classes:
                class_definitions.append(generate_dataclass(value_type, sub_fields))
                generated_classes.add(pascal_case_id_short)

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

        # if not id_short:
        #     continue
        id_short_raw = element.get("idShort")
        id_short = get_valid_id_short(id_short_raw)

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

    schema_output = "\n".join(enum_definitions + class_definitions)
    print(schema_output)
    return connect_and_insert(data, schema_output)


def generate_schema_code(data: dict) -> tuple[str, bytes]:
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

    schema_output = "\n".join(enum_definitions + class_definitions)
    binary_data = schema_output.encode("utf-8")

    return binary_data
