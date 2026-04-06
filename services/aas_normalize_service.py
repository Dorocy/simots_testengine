import copy
import json
import re
from typing import Any
try:
    import aas_core3.jsonization as aas_jsonization
except Exception:  # pragma: no cover
    aas_jsonization = None


DEFAULT_LANG = "en"
DEFAULT_TEXT = "arbitrary"
LANG_TAG_RE = re.compile(r"^[A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8})*$")


def _to_camel(token: str) -> str:
    parts = token.split("_")
    if not parts:
        return token
    return parts[0] + "".join(p[:1].upper() + p[1:] for p in parts[1:])


def _to_snake(token: str) -> str:
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", token).lower()


def _resolve_key(obj: dict[str, Any], token: str) -> str | None:
    if token in obj:
        return token
    camel = _to_camel(token)
    if camel in obj:
        return camel
    snake = _to_snake(token)
    if snake in obj:
        return snake
    return None


def _set_by_tokens(root: Any, tokens: list[str], value: Any) -> bool:
    if not tokens:
        return False
    current = root
    for idx, token in enumerate(tokens[:-1]):
        next_token = tokens[idx + 1]
        next_is_index = next_token.isdigit()
        if isinstance(current, list):
            if not token.isdigit():
                return False
            i = int(token)
            if i < 0:
                return False
            while len(current) <= i:
                current.append({} if not next_is_index else [])
            if current[i] is None:
                current[i] = {} if not next_is_index else []
            current = current[i]
            continue

        if isinstance(current, dict):
            key = _resolve_key(current, token) or token
            if key not in current or current[key] is None:
                current[key] = [] if next_is_index else {}
            current = current[key]
            continue
        return False

    last = tokens[-1]
    if isinstance(current, list):
        if not last.isdigit():
            return False
        i = int(last)
        if i < 0:
            return False
        while len(current) < i:
            current.append(None)
        if i == len(current):
            current.append(value)
        else:
            current[i] = value
        return True

    if isinstance(current, dict):
        key = _resolve_key(current, last) or last
        current[key] = value
        return True
    return False


def _parse_pointer(path: str) -> list[str]:
    if not path:
        return []
    if path.startswith("/"):
        return [p.replace("~1", "/").replace("~0", "~") for p in path.split("/")[1:]]
    path = path.replace("/", ".")
    tokens: list[str] = []
    for part in path.split("."):
        if not part:
            continue
        for m in re.finditer(r"([^[\]]+)|\[(\d+)\]", part):
            if m.group(1):
                tokens.append(m.group(1))
            if m.group(2):
                tokens.append(m.group(2))
    return tokens


def _apply_patch_object(root: Any, patch_obj: dict[str, Any]) -> bool:
    op = str(patch_obj.get("op", "")).lower()
    if op not in {"add", "replace"}:
        return False
    path = patch_obj.get("path")
    if not isinstance(path, str):
        return False
    tokens = _parse_pointer(path)
    if not tokens:
        return False
    return _set_by_tokens(root, tokens, patch_obj.get("value"))


def apply_rule_suggestions_to_json(root: dict[str, Any], suggestions: list[dict[str, Any]]) -> dict[str, Any]:
    patched = copy.deepcopy(root)
    for s in suggestions:
        patch_raw = s.get("patch")
        if not isinstance(patch_raw, str):
            continue
        try:
            patch_obj = json.loads(patch_raw)
        except Exception:
            continue
        if isinstance(patch_obj, dict):
            _apply_patch_object(patched, patch_obj)
        elif isinstance(patch_obj, list):
            if patch_obj and isinstance(patch_obj[0], dict):
                _apply_patch_object(patched, patch_obj[0])
    return patched


def _normalize_lang_entry(entry: dict[str, Any]) -> None:
    language = entry.get("language")
    if not isinstance(language, str):
        entry["language"] = DEFAULT_LANG
    else:
        candidate = language.replace("_", "-").strip()
        if not candidate or not LANG_TAG_RE.match(candidate):
            entry["language"] = DEFAULT_LANG
        else:
            entry["language"] = candidate

    text = entry.get("text")
    if not isinstance(text, str) or not text.strip():
        entry["text"] = DEFAULT_TEXT
    else:
        entry["text"] = text


def _is_lang_string_list(value: Any) -> bool:
    return (
        isinstance(value, list)
        and all(
            isinstance(x, dict)
            and ("language" in x or "text" in x)
            for x in value
        )
    )


def _ensure_english_entry(items: list[dict[str, Any]]) -> None:
    has_en = any(
        isinstance(item.get("language"), str)
        and item["language"].lower().startswith("en")
        for item in items
    )
    if not has_en:
        items.append({"language": DEFAULT_LANG, "text": DEFAULT_TEXT})


def _normalize_data_spec_content(obj: dict[str, Any]) -> None:
    preferred_key = "preferredName" if "preferredName" in obj else "preferred_name" if "preferred_name" in obj else None
    if preferred_key is None:
        obj["preferredName"] = [{"language": DEFAULT_LANG, "text": DEFAULT_TEXT}]
        preferred_key = "preferredName"

    preferred = obj.get(preferred_key)
    if not isinstance(preferred, list):
        preferred = [{"language": DEFAULT_LANG, "text": DEFAULT_TEXT}]
        obj[preferred_key] = preferred

    normalized_preferred: list[dict[str, Any]] = []
    for item in preferred:
        if isinstance(item, dict):
            _normalize_lang_entry(item)
            normalized_preferred.append(item)
    if not normalized_preferred:
        normalized_preferred = [{"language": DEFAULT_LANG, "text": DEFAULT_TEXT}]
    _ensure_english_entry(normalized_preferred)
    obj[preferred_key] = normalized_preferred

    for key, value in list(obj.items()):
        if _is_lang_string_list(value):
            normalized: list[dict[str, Any]] = []
            for item in value:
                if isinstance(item, dict):
                    _normalize_lang_entry(item)
                    normalized.append(item)
            obj[key] = normalized if normalized else [{"language": DEFAULT_LANG, "text": DEFAULT_TEXT}]

    definition_key = "definition" if "definition" in obj else None
    if definition_key and isinstance(obj.get(definition_key), list):
        definition = [x for x in obj[definition_key] if isinstance(x, dict)]
        for item in definition:
            _normalize_lang_entry(item)
        _ensure_english_entry(definition)
        obj[definition_key] = definition


def normalize_aas_json(root: dict[str, Any]) -> dict[str, Any]:
    normalized = copy.deepcopy(root)
    queue: list[Any] = [normalized]
    while queue:
        current = queue.pop(0)
        if isinstance(current, list):
            queue.extend(current)
            continue
        if not isinstance(current, dict):
            continue

        dsc_key = (
            "dataSpecificationContent"
            if "dataSpecificationContent" in current
            else "data_specification_content"
            if "data_specification_content" in current
            else None
        )
        if dsc_key and isinstance(current.get(dsc_key), dict):
            _normalize_data_spec_content(current[dsc_key])

        queue.extend(current.values())
    return normalized


def build_updated_file_from_rules_and_normalize(
    original_text: str,
    rule_suggestions: list[dict[str, Any]],
) -> str | None:
    try:
        root = json.loads(original_text)
        if not isinstance(root, dict):
            return None
        if aas_jsonization is not None:
            try:
                aas_jsonization.environment_from_jsonable(root)
            except Exception:
                pass
        patched = apply_rule_suggestions_to_json(root, rule_suggestions)
        normalized = normalize_aas_json(patched)
        if aas_jsonization is not None:
            try:
                aas_jsonization.environment_from_jsonable(normalized)
            except Exception:
                pass
        return json.dumps(normalized, ensure_ascii=False, indent=2)
    except Exception:
        return None
