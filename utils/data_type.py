import re
from typing import TypedDict, List, Set
from dataclasses import dataclass, field
from aas_test_engines.data_types import DataTypeDefXsd


class MessageGroup(TypedDict):
    assetInfo: List[str]
    submodels: List[str]
    conceptDescriptions: List[str]
    constraints: List[str]
    etc: List[str]
    needless: List[str]


def new_message_group() -> MessageGroup:
    return MessageGroup(
        assetInfo=[],
        submodels=[],
        conceptDescriptions=[],
        constraints=[],
        etc=[],
        needless=[]
    )


@dataclass
class SchemaGroup:
    result: List[str] = field(default_factory=list)
    class_definitions: List[str] = field(default_factory=list)
    enum_definitions: List[str] = field(default_factory=list)
    generated_classes: Set[str] = field(default_factory=set)
    generated_enums: Set[str] = field(default_factory=set)
    unnamed_element_counter: int = 0


# class SchemaState(TypedDict):
#     result: List[str]
#     class_definitions: List[str]
#     enum_definitions: List[str]
#     generated_classes: Set[str]
#     generated_enums: Set[str]
#     unnamed_element_counter: int


# def new_schema_state() -> SchemaState:
#     return SchemaState(
#         result=[],
#         class_definitions=[],
#         enum_definitions=[],
#         generated_classes=set(),
#         generated_enums=set(),
#         unnamed_element_counter=0
#     )


value_type_names = [v.value for v in DataTypeDefXsd]
value_type_pattern = "|".join(re.escape(name) for name in value_type_names)

TEMPLATE_EXCLUDE_PATTERNS = [
        "String is shorter than 1 characters",
        "Empty array not allowed",
        rf"Value '.*?' is not a '({value_type_pattern})'.*"
    ]
