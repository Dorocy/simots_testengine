import re
from typing import TypedDict, List
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


value_type_names = [v.value for v in DataTypeDefXsd]
value_type_pattern = "|".join(re.escape(name) for name in value_type_names)
print(value_type_pattern)

TEMPLATE_EXCLUDE_PATTERNS = [
        "String is shorter than 1 characters",
        "Empty array not allowed",
        rf"Value '.*?' is not a '({value_type_pattern})'.*"
    ]
