import sys
import re
import json
sys.stdout.reconfigure(encoding="utf-8")
from typing import List
from db.db_hadler import connect_and_insert, extract_semantic_id
from utils.data_type import SchemaGroup


schema = SchemaGroup()


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
    return "class {}(Enum):\n{}".format(
        name,
        "".join(f'    {to_snake_case(label)} = "{value}"\n' for label, value in values)
    )


def get_valid_id_short(id_short_raw):
    global unnamed_element_counter
    id_short = (id_short_raw or "").strip()
    if not id_short:
        id_short = f"UnnamedElement_{unnamed_element_counter}"
        unnamed_element_counter += 1
    return id_short


def get_enumeration(element, class_name):
    descriptions = element.get("description", [])
    for desc in descriptions:
        text = desc.get("text", "")
        if not text.strip().startswith("enumeration:"):
            continue

        entries = text.replace("enumeration:", "").strip().split(", ")
        enum_values = []
        for entry in entries:
            print("entries: ", entries, '\n')
            print("entry: ", entry, '\n')
            match = re.match(r"(.+?) \((.+?)\)", entry)
            if match:
                print("match: ", match, '\n''\n''\n')
                enum_values.append((to_snake_case(match.group(2)), match.group(1)))

        if class_name not in schema.generated_enums:
            schema.enum_definitions.append(generate_enum(class_name, enum_values))
            schema.generated_enums.add(class_name)


def get_submodel_collection(element, sub_elements, top_level_semantic_id):
    sub_class_name = to_pascal_case(to_snake_case(element["idShort"]))
    if not sub_elements or sub_class_name in schema.generated_classes:
        return

    process_submodel_elements(
        sub_class_name,
        sub_elements,
        top_level_semantic_id=top_level_semantic_id,
    )
    schema.generated_classes.add(sub_class_name)


def process_submodel_elements(
    name: str,
    elements: List[dict],
    is_top_level: bool = False,
    top_level_semantic_id: str = "",
):
    fields = []
    print("name: ", name)
    print("elements: ", elements)

    for element in elements:
        if not isinstance(element, dict):
            continue

        id_short = get_valid_id_short(element.get("idShort"))
        pascal_name = to_pascal_case(to_snake_case(id_short))
        model_type = element.get("modelType", "")
        sub_elements = element.get("value", [])

        get_enumeration(element, pascal_name)

        sub_element_field = extract_values(element)
        if sub_element_field:
            fields.append(sub_element_field)

        if model_type == "SubmodelElementCollection":
            get_submodel_collection(element, sub_elements, top_level_semantic_id)

    if name not in schema.generated_classes:
        schema.class_definitions.append(
            generate_dataclass(name, fields, top_level_semantic_id if is_top_level else None)
        )
        schema.generated_classes.add(name)


def extract_values(value, parent_name=None):
    if not isinstance(value, dict):
        return ""

    id_short_raw = value.get("idShort", "")
    id_short = get_valid_id_short(id_short_raw)
    semantic_id_value = value.get("semanticId", {}).get("keys", [{}])[0].get("value")
    qualifiers_value = value.get("qualifiers", [{}])[0].get("value")
    model_type = value.get("modelType", "")
    snake_case_id_short = to_snake_case(id_short)
    pascal_case_id_short = to_pascal_case(snake_case_id_short)

    model_type_map = {
        "MultiLanguageProperty": "LangString",
        "Property": "str",
        "File": "str",
        "Entity": "EntType",
        "ReferenceElement": "RefType",
    }

    if model_type == "SubmodelElementCollection":
        value_type = pascal_case_id_short if value.get("value") else "str"
    elif model_type == "SubmodelElementList":
        value_type = pascal_case_id_short
    else:
        value_type = model_type_map.get(model_type, "str")

    qualifier_map = {
        "One": "{t}",
        "ZeroToOne": "Optional[{t}]",
        "optional": "Optional[{t}]",
        "ZeroToMany": "Optional[List[{t}]]",
        "OneToMany": "List[{t}]",
    }

    type_annotation = qualifier_map.get(
        qualifiers_value, "Optional[{t}]"
    ).format(t=value_type)

    field_definition = (
        f"{snake_case_id_short}: {type_annotation} = field(metadata={{\n"
        f"    'semantic_id': '{semantic_id_value}'\n}})"
    )

    if field_definition not in schema.result:
        schema.result.append(field_definition)

    return field_definition


def get_schema_result(data):

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

    schema_output = "\n".join(schema.enum_definitions + schema.class_definitions)
    # print(schema_output)
    return connect_and_insert(data, schema_output)


def generate_schema_code(data: dict) -> tuple[str, bytes]:

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

    schema_output = "\n".join(schema.enum_definitions + schema.class_definitions)
    binary_data = schema_output.encode("utf-8")

    print(binary_data)

    return binary_data
