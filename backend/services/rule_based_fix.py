import json
import re
from typing import Any


DEFAULT_TEXT_VALUE = "arbitrary"
DEFAULT_DEFINITION_TEXT = "arbitary definition custom"
DEFAULT_LANG_VALUE = "en"


def _to_patch(path: str, value: Any, op: str = "replace") -> str:
    return json.dumps(
        {
            "op": op,
            "path": path,
            "value": value,
        },
        ensure_ascii=False,
    )


def _normalize_identifier_for_pattern(raw: str) -> str:
    # Pattern expects: [a-zA-Z][a-zA-Z0-9_]*
    normalized = re.sub(r"[^A-Za-z0-9_]", "_", raw.strip())
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    if not normalized:
        return "AAS_VALUE"
    if not re.match(r"^[A-Za-z]", normalized):
        normalized = f"A_{normalized}"
    return normalized


def _definition_value() -> list[dict[str, str]]:
    return [
        {
            "language": "en",
            "text": DEFAULT_DEFINITION_TEXT,
        }
    ]


def _is_snake_case_location(location: str) -> bool:
    return "_" in location


def _location_key(location: str, camel: str, snake: str) -> str:
    return snake if _is_snake_case_location(location) else camel


def _definition_patch_path(location: str) -> str:
    base = location.rstrip("/")
    embedded = _location_key(location, "embeddedDataSpecifications", "embedded_data_specifications")
    content = _location_key(location, "dataSpecificationContent", "data_specification_content")
    return f"{base}/{embedded}/0/{content}/definition"


def _preferred_name_patch_path(location: str) -> str:
    base = location.rstrip("/")
    return f"{base}/{_location_key(location, 'preferredName', 'preferred_name')}"


def _message_field_path(message: str) -> str:
    match = re.search(r"^([A-Za-z0-9_\-/\[\]]+)\s+has unexpected value", message, flags=re.IGNORECASE)
    if not match:
        return ""
    raw_path = match.group(1).strip()
    raw_path = re.sub(r"\[(\d+)\]", r"/\1", raw_path)
    return raw_path.strip("/")


def _join_patch_path(location: str, field_path: str, leaf: str | None = None) -> str:
    parts: list[str] = []
    if location:
        parts.append(location.rstrip("/"))
    if field_path:
        parts.append(field_path.strip("/"))
    path = "/".join(part for part in parts if part)
    if not path.startswith("/"):
        path = f"/{path}" if path else ""
    if leaf:
        path = f"{path.rstrip('/')}/{leaf}"
    return path


def _build_suggestion(
    error_item: dict[str, Any],
    summary: str,
    reason: str,
    patch: str,
    fixed_snippet: Any,
) -> dict[str, Any]:
    return {
        "errorId": error_item.get("id"),
        "code": error_item.get("code"),
        "location": error_item.get("location"),
        "summary": summary,
        "reason": reason,
        "patch": patch,
        "fixedSnippet": json.dumps(fixed_snippet, ensure_ascii=False),
        "raw": {
            "source": "rule_based_fix",
            "summary": summary,
        },
    }


def build_rule_based_suggestions(
    payload: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    errors = payload.get("errors", [])
    if not isinstance(errors, list):
        return [], []

    matched: list[dict[str, Any]] = []
    unmatched: list[dict[str, Any]] = []

    for item in errors:
        if not isinstance(item, dict):
            continue

        message = str(item.get("message", ""))
        location_raw = str(item.get("location", "") or "")
        location_match = re.search(r"(?:location:\s*|@\s*)(/[A-Za-z0-9_/\-]+)", message, flags=re.IGNORECASE)
        location = location_raw or (location_match.group(1) if location_match else "")
        lower = message.lower()
        message_field_path = _message_field_path(message)
        suggestion: dict[str, Any] | None = None
#Definition이 없을때
        if "definition is missing" in lower and location:
            definition = _definition_value()
            suggestion = _build_suggestion(
                item,
                summary="Add missing definition",
                reason="embeddedDataSpecifications.dataSpecificationContent.definition is required.",
                patch=_to_patch(_definition_patch_path(location), definition, op="add"),
                fixed_snippet={"definition": definition},
            )

#Definition에서 영어가 없을때,
        elif "definition.language is missing english" in lower and location:
            definition = _definition_value()
            suggestion = _build_suggestion(
                item,
                summary="Add English definition",
                reason="Definition must include an English (en) entry.",
                patch=_to_patch(_definition_patch_path(location), definition, op="replace"),
                fixed_snippet={"definition": definition},
            )

        elif "aasc-3a-002 violated: english language is missing" in lower and location:
            preferred_name_key = _location_key(location, "preferredName", "preferred_name")
            suggestion = _build_suggestion(
                item,
                summary="Ensure English preferred name",
                reason="IEC61360 content must include an English language entry.",
                patch=_to_patch(
                    f"{_preferred_name_patch_path(location)}/0",
                    {"language": DEFAULT_LANG_VALUE, "text": DEFAULT_TEXT_VALUE},
                    op="add",
                ),
                fixed_snippet={
                    preferred_name_key: [
                        {"language": DEFAULT_LANG_VALUE, "text": DEFAULT_TEXT_VALUE}
                    ]
                },
            )

        elif "does not contain a language according to bcp46" in lower and location:
            lang_path = (
                location.rstrip("/")
                if location.rstrip("/").endswith("/language")
                else f"{location.rstrip('/')}/language"
            )
            suggestion = _build_suggestion(
                item,
                summary="Normalize language to BCP47 tag",
                reason="language must be a valid BCP47/BCP46 compatible language tag.",
                patch=_to_patch(lang_path, DEFAULT_LANG_VALUE),
                fixed_snippet={"language": DEFAULT_LANG_VALUE},
            )

        elif "does not match pattern [a-zA-Z][a-zA-Z0-9_]*".lower() in lower and location:
            bad_match = re.search(r"String\s+'([^']+)'\s+does not match pattern", message)
            bad_value = bad_match.group(1) if bad_match else ""
            normalized_value = _normalize_identifier_for_pattern(bad_value)
            suggestion = _build_suggestion(
                item,
                summary="Normalize identifier to allowed pattern",
                reason="Identifier must match [a-zA-Z][a-zA-Z0-9_]*. Replaced invalid characters with underscore.",
                patch=_to_patch(location.rstrip("/"), normalized_value),
                fixed_snippet=normalized_value,
            )
#"text": "" 비어있는 값인 경우
        elif "property 'text' must not be empty" in lower and location:
            suggestion = _build_suggestion(
                item,
                summary="Replace empty text",
                reason="text field cannot be empty.",
                patch=_to_patch(f"{location.rstrip('/')}/text", DEFAULT_TEXT_VALUE),
                fixed_snippet={"text": DEFAULT_TEXT_VALUE},
            )

        elif "aasd-123" in lower and "first key must be one of aasidentifiables" in lower and location:
            suggestion = _build_suggestion(
                item,
                summary="Use ExternalReference for GlobalReference/EMPTY",
                reason="ModelReference first key type must be AasIdentifiables.",
                patch=_to_patch(f"{location.rstrip('/')}/type", "ExternalReference"),
                fixed_snippet={"type": "ExternalReference"},
            )

        elif "is not a valid typeoffaxnumber" in lower and location:
            bad = re.search(r"'([^']+)'\\s+is not a valid TypeOfFaxNumber", message)
            candidate = bad.group(1).strip() if bad else "0173-1#07-AAS754#001"
            suggestion = _build_suggestion(
                item,
                summary="Normalize TypeOfFaxNumber value",
                reason="Invalid value often contains extra whitespace.",
                patch=_to_patch(f"{location.rstrip('/')}/value", candidate),
                fixed_snippet={"value": candidate},
            )

        elif "cannot convert to lang string: no value" in lower and location:
            value = [{"language": "en", "text": DEFAULT_TEXT_VALUE}]
            suggestion = _build_suggestion(
                item,
                summary="Add missing lang string value",
                reason="lang string field requires a non-empty value array.",
                patch=_to_patch(f"{location.rstrip('/')}/value", value),
                fixed_snippet={"value": value},
            )

        elif "cannot convert to string: no value" in lower and location:
            suggestion = _build_suggestion(
                item,
                summary="Add missing string value",
                reason="string field requires a non-empty value.",
                patch=_to_patch(f"{location.rstrip('/')}/value", DEFAULT_TEXT_VALUE),
                fixed_snippet={"value": DEFAULT_TEXT_VALUE},
            )
#dataspecificationied61360/3으로 대체
        elif re.search(r"dataspecification\s*/\s*keys\[0\]\s+has unexpected value", lower):
            expected_match = re.search(r"expected\s+(https?://\S+)", message, flags=re.IGNORECASE)
            expected_value = (
                expected_match.group(1).rstrip(">,.;")
                if expected_match
                else "https://admin-shell.io/DataSpecificationTemplates/DataSpecificationIec61360/3"
            )
            if location:
                data_spec_key = _location_key(location, "dataSpecification", "data_specification")
                patch_path = f"{location.rstrip('/')}/{data_spec_key}/keys/0/value"
            else:
                base_path = message_field_path or "dataSpecification/keys/0"
                patch_path = _join_patch_path("", base_path, "value")
            suggestion = _build_suggestion(
                item,
                summary="Normalize IEC61360 dataSpecification reference",
                reason="Reference must use the expected canonical IEC61360 URL.",
                patch=_to_patch(patch_path, expected_value),
                fixed_snippet={
                    (data_spec_key if location else "dataSpecification"): {
                        "keys": [
                            {
                                "value": expected_value,
                            }
                        ]
                    }
                },
            )

        if suggestion:
            matched.append(suggestion)
        else:
            unmatched.append(item)

    return matched, unmatched
