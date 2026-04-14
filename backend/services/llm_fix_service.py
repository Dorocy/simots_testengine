import asyncio
import copy
import json
import os
import uuid
from typing import Any
from urllib import error, request
from api.response_handler import ErrorCode, error_response
from services.rule_based_fix import build_rule_based_suggestions
from services.aas_normalize_service import build_updated_file_from_rules_and_normalize


REPAIR_API_URL = os.getenv(
    "REPAIR_API_URL",
    "https://overhead-anticipated-carroll-rainbow.trycloudflare.com/repair",
).rstrip("/")
REPAIR_TIMEOUT_SECONDS = float(os.getenv("REPAIR_TIMEOUT_SECONDS", "120"))
REVERIFY_BASE_URL = os.getenv(
    "REVERIFY_BASE_URL",
    os.getenv("VERIFICATION_PROXY_URL", "https://overhead-anticipated-carroll-rainbow.trycloudflare.com "),
    
).rstrip("/")


def _int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value.strip())
    except (TypeError, ValueError):
        return default


MAX_CONTEXT_CHARS = _int_env("FIX_MAX_CONTEXT_CHARS", 30000)


SYSTEM_PROMPT = (
    "You are an AAS JSON repair assistant. "
    "Given verification errors, suggest precise fixes. "
    "Return only JSON with this shape: "
    '{"suggestions":[{"errorId":"","code":"","location":"","summary":"","reason":"","patch":"","fixedSnippet":""}],"updatedFile":""}. '
    "Do not add markdown."
)


def _build_user_prompt(payload: dict[str, Any]) -> str:
    verification_type = payload.get("verificationType", "metamodel")
    file_name = payload.get("fileName", "")
    errors = payload.get("errors", [])
    context = payload.get("context", {})
    include_updated_file = bool(payload.get("includeUpdatedFile", False))
    prompt_context = copy.deepcopy(context) if isinstance(context, dict) else context
    if isinstance(prompt_context, dict):
        original = prompt_context.get("originalFileContent")
        if isinstance(original, str) and len(original) > MAX_CONTEXT_CHARS:
            prompt_context["originalFileContent"] = (
                original[:MAX_CONTEXT_CHARS]
                + "\n...<truncated>..."
            )

    return (
        "Task: Suggest fixes for AAS verification errors.\n"
        f"Verification type: {verification_type}\n"
        f"File name: {file_name}\n"
        f"Errors JSON: {json.dumps(errors, ensure_ascii=False)}\n"
        f"Context JSON: {json.dumps(prompt_context, ensure_ascii=False)}\n"
        "Rules:\n"
        "1) Keep one suggestion per error when possible.\n"
        "2) Use concise summary and concrete reason.\n"
        "3) patch should be a minimal JSON patch-style text or direct replacement hint.\n"
        "4) fixedSnippet should contain only the relevant corrected JSON snippet.\n"
        "4-1) If context.snippets is present, match by errorId and use that snippet as primary evidence.\n"
        f"5) includeUpdatedFile={str(include_updated_file).lower()}. "
        "If true and originalFileContent exists, return updatedFile. "
        "If false, set updatedFile to an empty string.\n"
    )


def _verification_endpoint(verification_type: str) -> str | None:
    mapping = {
        "metamodel": "/verification/metamodel",
        "template": "/verification/template",
        "instance": "/verification/instance",
    }
    return mapping.get(verification_type)


def _split_message_and_location(raw: str) -> tuple[str, str | None]:
    text = raw.strip()
    idx = text.rfind(" @ /")
    if idx < 0:
        return text, None
    message = text[:idx].strip() or text
    location = text[idx + 3 :].strip() or None
    return message, location


def _to_error_code(category: str) -> str:
    chars: list[str] = []
    for idx, ch in enumerate(category):
        if idx > 0 and ch.isupper() and category[idx - 1].islower():
            chars.append("_")
        chars.append(ch.upper())
    return "".join(chars)


def _normalize_verification_errors(message: Any) -> list[dict[str, Any]]:
    if not message:
        return []

    if isinstance(message, str):
        parsed_message, location = _split_message_and_location(message)
        return [
            {
                "code": "VERIFICATION_ERROR",
                "message": parsed_message,
                "location": location,
            }
        ]

    if isinstance(message, list):
        normalized: list[dict[str, Any]] = []
        for item in message:
            text = str(item).strip()
            if not text:
                continue
            parsed_message, location = _split_message_and_location(text)
            normalized.append(
                {
                    "code": "VERIFICATION_ERROR",
                    "message": parsed_message,
                    "location": location,
                }
            )
        return normalized

    if isinstance(message, dict):
        normalized = []
        for category, value in message.items():
            messages = value.get("message") if isinstance(value, dict) else None
            if not isinstance(messages, list):
                continue
            for item in messages:
                text = str(item).strip()
                if not text:
                    continue
                parsed_message, location = _split_message_and_location(text)
                normalized.append(
                    {
                        "code": _to_error_code(str(category)),
                        "message": parsed_message,
                        "location": location,
                    }
                )
        return normalized

    return []


def _build_multipart_form_body(field_name: str, file_name: str, content: str) -> tuple[bytes, str]:
    boundary = f"----AASVerifyBoundary{uuid.uuid4().hex}"
    lines = [
        f"--{boundary}",
        f'Content-Disposition: form-data; name="{field_name}"; filename="{file_name}"',
        "Content-Type: application/json",
        "",
        content,
        f"--{boundary}--",
        "",
    ]
    body = "\r\n".join(lines).encode("utf-8")
    content_type = f"multipart/form-data; boundary={boundary}"
    return body, content_type


def _reverify_updated_file(
    verification_type: str,
    file_name: str,
    updated_content: str,
) -> dict[str, Any]:
    endpoint = _verification_endpoint(verification_type)
    if not endpoint:
        return {"success": False, "errors": []}

    body, content_type = _build_multipart_form_body(
        "file",
        file_name or "fixed-model.json",
        updated_content,
    )
    req = request.Request(
        f"{REVERIFY_BASE_URL}{endpoint}",
        data=body,
        headers={"Content-Type": content_type},
        method="POST",
    )

    with request.urlopen(req, timeout=REPAIR_TIMEOUT_SECONDS) as resp:
        payload = json.loads(resp.read().decode("utf-8"))

    if isinstance(payload, dict) and isinstance(payload.get("success"), bool):
        return {
            "success": bool(payload.get("success")),
            "errors": payload.get("errors", []),
            "raw": payload,
        }

    verification = payload.get("verification", {}) if isinstance(payload, dict) else {}
    verification_result = str(verification.get("result", "")).lower()
    verification_message = verification.get("message")
    success = verification_result == "success"
    return {
        "success": success,
        "errors": [] if success else _normalize_verification_errors(verification_message),
        "raw": payload,
    }


def _post_repair_api(payload: dict[str, Any]) -> dict[str, Any]:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": _build_user_prompt(payload)},
    ]
    body = {
        "mode": payload.get("mode", "single"),
        "verificationType": payload.get("verificationType", "metamodel"),
        "fileName": payload.get("fileName"),
        "errors": payload.get("errors", []),
        "context": payload.get("context"),
        "includeUpdatedFile": bool(payload.get("includeUpdatedFile", False)),
        "messages": messages,
        "prompt": _build_user_prompt(payload),
        "systemPrompt": SYSTEM_PROMPT,
    }

    data = json.dumps(body).encode("utf-8")
    req = request.Request(
        REPAIR_API_URL,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with request.urlopen(req, timeout=REPAIR_TIMEOUT_SECONDS) as resp:
        raw = resp.read().decode("utf-8")
        return json.loads(raw)


def _extract_structured_fix_payload(response_data: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(response_data, dict):
        return {"suggestions": []}

    if (
        isinstance(response_data.get("suggestions"), list)
        or isinstance(response_data.get("updatedFile"), str)
    ):
        return response_data

    data = response_data.get("data")
    if (
        isinstance(data, dict)
        and (
            isinstance(data.get("suggestions"), list)
            or isinstance(data.get("updatedFile"), str)
        )
    ):
        return data

    message = response_data.get("message", {})
    if isinstance(message, dict):
        content = message.get("content", "")
        try:
            return json.loads(content) if isinstance(content, str) else content
        except json.JSONDecodeError:
            return {"suggestions": []}

    return {"suggestions": []}


def _parse_suggestions(response_data: dict[str, Any]) -> tuple[list[dict[str, Any]], str | None]:
    parsed = _extract_structured_fix_payload(response_data)

    suggestions = parsed.get("suggestions", [])
    if not isinstance(suggestions, list):
        suggestions = []

    normalized: list[dict[str, Any]] = []
    for suggestion in suggestions:
        if not isinstance(suggestion, dict):
            continue
        normalized.append(
            {
                "errorId": suggestion.get("errorId"),
                "code": suggestion.get("code"),
                "location": suggestion.get("location"),
                "summary": suggestion.get("summary"),
                "reason": suggestion.get("reason"),
                "patch": suggestion.get("patch"),
                "fixedSnippet": suggestion.get("fixedSnippet"),
                "raw": suggestion,
            }
        )
    updated_file = parsed.get("updatedFile")
    if not isinstance(updated_file, str):
        updated_file = None
    return normalized, updated_file


async def request_rule_based_fix(payload: dict[str, Any]) -> Any:
    try:
        rule_suggestions, remaining_errors = build_rule_based_suggestions(payload)
        context = payload.get("context")
        include_updated_file = bool(payload.get("includeUpdatedFile", False))
        verification_type = str(payload.get("verificationType", "metamodel"))
        file_name = str(payload.get("fileName") or "fixed-model.json")
        original_file_content = (
            context.get("originalFileContent")
            if isinstance(context, dict)
            else None
        )
        deterministic_updated_file = (
            build_updated_file_from_rules_and_normalize(original_file_content, rule_suggestions)
            if include_updated_file and isinstance(original_file_content, str)
            else None
        )

        reverified_errors = remaining_errors
        reverify_raw: dict[str, Any] | None = None
        if rule_suggestions and deterministic_updated_file:
            reverify_result = await asyncio.to_thread(
                _reverify_updated_file,
                verification_type,
                file_name,
                deterministic_updated_file,
            )
            reverify_raw = reverify_result.get("raw") if isinstance(reverify_result, dict) else None
            reverified_errors = (
                reverify_result.get("errors", [])
                if isinstance(reverify_result, dict)
                else remaining_errors
            )

        return {
            "success": True,
            "message": "Rule-based fix stage completed.",
            "suggestions": rule_suggestions,
            "updatedFile": deterministic_updated_file or "",
            "remainingErrors": reverified_errors,
            "raw": {
                "source": "rule_based_fix",
                "matchedCount": len(rule_suggestions),
                "normalized": bool(deterministic_updated_file),
                "reverified": bool(reverify_raw),
                "reverifyBaseUrl": REVERIFY_BASE_URL,
                "reverifyRaw": reverify_raw,
            },
        }
    except error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        truncated = detail[:500] if detail else ""
        return error_response(
            status_code=e.code if isinstance(e.code, int) else 502,
            error_code=ErrorCode.OLLAMA_HTTP_ERROR,
            message=f"Rule-based reverify HTTP error: {e.code}. {truncated}".strip(),
        )
    except error.URLError as e:
        return error_response(
            status_code=503,
            error_code=ErrorCode.OLLAMA_CONNECTION_ERROR,
            message=f"Rule-based reverify connection error: {str(e.reason)}",
        )
    except Exception as e:
        return error_response(
            status_code=500,
            error_code=ErrorCode.OLLAMA_REQUEST_FAILED,
            message=f"Rule-based fix failed: {str(e)}",
        )


async def request_repair_fix(payload: dict[str, Any]) -> Any:
    try:
        response_data = await asyncio.to_thread(_post_repair_api, payload)
        suggestions, updated_file = _parse_suggestions(response_data)

        if not suggestions and not updated_file:
            return error_response(
                status_code=422,
                error_code=ErrorCode.LLM_NO_USABLE_OUTPUT,
                message="LLM returned no usable fix output. Try with fewer selected errors.",
            )

        return {
            "success": True,
            "message": "LLM repair stage completed.",
            "suggestions": suggestions,
            "updatedFile": updated_file or "",
            "raw": {
                "source": "llm_repair",
                "llmMatchedCount": len(suggestions),
                "repairApiUrl": REPAIR_API_URL,
                "llmRaw": response_data,
            },
        }
    except error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        truncated = detail[:500] if detail else ""
        return error_response(
            status_code=e.code if isinstance(e.code, int) else 502,
            error_code=ErrorCode.OLLAMA_HTTP_ERROR,
            message=f"Repair API HTTP error: {e.code}. {truncated}".strip(),
        )
    except error.URLError as e:
        return error_response(
            status_code=503,
            error_code=ErrorCode.OLLAMA_CONNECTION_ERROR,
            message=f"Repair API connection error: {str(e.reason)}",
        )
    except Exception as e:
        return error_response(
            status_code=500,
            error_code=ErrorCode.OLLAMA_REQUEST_FAILED,
            message=f"LLM repair failed: {str(e)}",
        )


async def request_llm_fix(payload: dict[str, Any]) -> Any:
    rule_stage = await request_rule_based_fix(payload)
    if not isinstance(rule_stage, dict) or not rule_stage.get("success"):
        return rule_stage

    remaining_errors = rule_stage.get("remainingErrors", [])
    updated_file = rule_stage.get("updatedFile")
    rule_suggestions = rule_stage.get("suggestions", [])
    raw = rule_stage.get("raw", {}) if isinstance(rule_stage.get("raw"), dict) else {}

    if not remaining_errors:
        return {
            "success": True,
            "message": "Fix suggestions generated (rule-based only).",
            "suggestions": rule_suggestions,
            "updatedFile": updated_file or "",
            "raw": {
                "source": "rule_based_fix",
                "ruleBasedMatchedCount": len(rule_suggestions),
                "llmMatchedCount": 0,
                "deterministicUpdatedFile": bool(updated_file),
                "reverifiedErrorCount": 0,
                **raw,
            },
        }

    llm_payload = copy.deepcopy(payload)
    llm_payload["errors"] = remaining_errors
    if isinstance(llm_payload.get("context"), dict) and isinstance(updated_file, str) and updated_file:
        llm_payload["context"] = {
            **llm_payload["context"],
            "originalFileContent": updated_file,
        }

    llm_stage = await request_repair_fix(llm_payload)
    if not isinstance(llm_stage, dict) or not llm_stage.get("success"):
        return llm_stage

    llm_suggestions = llm_stage.get("suggestions", [])
    llm_updated_file = llm_stage.get("updatedFile")
    llm_raw = llm_stage.get("raw", {}) if isinstance(llm_stage.get("raw"), dict) else {}

    return {
        "success": True,
        "message": "Fix suggestions generated (rule-based + LLM).",
        "suggestions": [*rule_suggestions, *llm_suggestions],
        "updatedFile": updated_file or llm_updated_file or "",
        "raw": {
            "source": "hybrid_fix",
            "ruleBasedMatchedCount": len(rule_suggestions),
            "llmMatchedCount": len(llm_suggestions),
            "deterministicUpdatedFile": bool(updated_file),
            "reverifiedErrorCount": len(remaining_errors),
            **raw,
            **llm_raw,
        },
    }
