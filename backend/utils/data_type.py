import re
from typing import TypedDict, List, Set
from dataclasses import dataclass, field

try:
    from aas_test_engines.data_types import DataTypeDefXsd  # type: ignore
except Exception:
    DataTypeDefXsd = None


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
        needless=[],
    )


@dataclass
class SchemaGroup:
    result: List[str] = field(default_factory=list)
    class_definitions: List[str] = field(default_factory=list)
    enum_definitions: List[str] = field(default_factory=list)
    generated_classes: Set[str] = field(default_factory=set)
    generated_enums: Set[str] = field(default_factory=set)
    unnamed_element_counter: int = 0


if DataTypeDefXsd is not None:
    value_type_names = [v.value for v in DataTypeDefXsd]
else:
    # Fallback for aas_test_engines versions where DataTypeDefXsd is unavailable.
    value_type_names = [
        "xs:string",
        "xs:boolean",
        "xs:decimal",
        "xs:integer",
        "xs:double",
        "xs:float",
        "xs:date",
        "xs:time",
        "xs:dateTime",
    ]
value_type_pattern = "|".join(re.escape(name) for name in value_type_names)

TEMPLATE_EXCLUDE_PATTERNS = [
    "String is shorter than 1 characters",
    "Empty array not allowed",
    rf"Value '.*?' is not a '({value_type_pattern})'.*",
]
