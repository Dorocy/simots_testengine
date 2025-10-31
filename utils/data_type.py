from typing import TypedDict, List


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
