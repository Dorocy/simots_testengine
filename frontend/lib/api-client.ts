const API_BASE_URL = "/api";
const FIX_API_ENDPOINT =
  process.env.NEXT_PUBLIC_LLM_FIX_ENDPOINT ?? `${API_BASE_URL}/verification/fix`;
const RULE_FIX_API_ENDPOINT =
  process.env.NEXT_PUBLIC_RULE_FIX_ENDPOINT ?? `${API_BASE_URL}/verification/rule-fix`;
const LLM_REPAIR_API_ENDPOINT =
  process.env.NEXT_PUBLIC_REPAIR_FIX_ENDPOINT ?? "https://overhead-anticipated-carroll-rainbow.trycloudflare.com/repair";
const DIRECT_FIX_ENDPOINT =
  process.env.NEXT_PUBLIC_DIRECT_FIX_ENDPOINT ?? "https://simotstestengine-production.up.railway.app/verification/fix";
const DIRECT_RULE_FIX_ENDPOINT =
  process.env.NEXT_PUBLIC_DIRECT_RULE_FIX_ENDPOINT ?? "https://simotstestengine-production.up.railway.app/verification/rule-fix";
const DIRECT_LLM_REPAIR_ENDPOINT =
  process.env.NEXT_PUBLIC_DIRECT_LLM_REPAIR_ENDPOINT ?? "https://overhead-anticipated-carroll-rainbow.trycloudflare.com/repair";

export interface VerificationResult {
  success: boolean;
  message?: string;
  errors?: Array<{
    code: string;
    message: string;
    location?: string;
  }>;
}

export interface Schema {
  semanticId: string;
  uploadedBy: string;
  schema: Record<string, unknown>;
  createdAt?: string;
}

export interface FixTargetError {
  id?: string;
  code: string;
  message: string;
  location?: string;
}

export interface LlmFixRequest {
  mode: "single" | "batch";
  verificationType: "metamodel" | "template" | "instance";
  errors: FixTargetError[];
  fileName?: string;
  context?: Record<string, unknown>;
  includeUpdatedFile?: boolean;
}

export interface LlmFixSuggestion {
  errorId?: string;
  code?: string;
  location?: string;
  summary?: string;
  reason?: string;
  patch?: string;
  fixedSnippet?: string;
  raw?: unknown;
}

export interface RepairAnchorPair {
  anchor_id?: string;
  status?: string;
  success?: boolean;
  error_messages?: string[];
  broken_anchor?: unknown;
  corrected_anchor?: unknown;
}

export interface LlmFixResponse {
  success: boolean;
  message?: string;
  jobId?: string;
  suggestions?: LlmFixSuggestion[];
  updatedFile?: string;
  remainingErrors?: FixTargetError[];
  raw?: unknown;
}

interface BackendErrorPayload {
  error?: {
    code?: string;
    message?: string;
  };
}

interface BackendVerificationPayload {
  verification?: {
    result?: string;
    message?: unknown;
  };
}

async function fetchApi(path: string, init?: RequestInit): Promise<Response> {
  return fetch(`${API_BASE_URL}${path}`, init);
}

function toErrorCode(category: string): string {
  return category.replace(/([a-z])([A-Z])/g, "$1_$2").toUpperCase();
}

function splitMessageAndLocation(raw: string): { message: string; location?: string } {
  const text = raw.trim();
  const idx = text.lastIndexOf(" @ /");
  if (idx < 0) {
    return { message: text };
  }

  const message = text.slice(0, idx).trim();
  const location = text.slice(idx + 3).trim();
  return {
    message: message || text,
    location: location || undefined,
  };
}

function stringifyJson(value: unknown): string {
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value ?? "");
  }
}

function buildSuggestionsFromAnchorPairs(anchorPairs: RepairAnchorPair[]): LlmFixSuggestion[] {
  return anchorPairs.map((pair, index) => {
    const firstMessage = Array.isArray(pair.error_messages) && pair.error_messages.length > 0
      ? pair.error_messages[0]
      : "";
    const parsed = splitMessageAndLocation(firstMessage);
    return {
      errorId: pair.anchor_id ?? `anchor-${index}`,
      code: "LLM_REPAIR",
      location: parsed.location,
      summary: parsed.message || "LLM corrected anchor",
      reason: Array.isArray(pair.error_messages) ? pair.error_messages.join("\n") : undefined,
      fixedSnippet: stringifyJson(pair.corrected_anchor),
      raw: {
        source: "llm_repair",
        anchorPair: pair,
      },
    };
  });
}

function normalizeAnchorPairs(value: unknown): RepairAnchorPair[] {
  if (Array.isArray(value)) {
    return value as RepairAnchorPair[];
  }

  if (value && typeof value === "object") {
    return Object.values(value as Record<string, unknown>).map(
      (pair) => pair as RepairAnchorPair,
    );
  }

  return [];
}

function normalizeVerificationErrors(message: unknown): VerificationResult["errors"] {
  if (!message) return [];

  if (typeof message === "string") {
    const parsed = splitMessageAndLocation(message);
    return [{ code: "VERIFICATION_ERROR", message: parsed.message, location: parsed.location }];
  }

  if (Array.isArray(message)) {
    return message
      .map((item) => String(item).trim())
      .filter(Boolean)
      .map((item) => {
        const parsed = splitMessageAndLocation(item);
        return {
          code: "VERIFICATION_ERROR",
          message: parsed.message,
          location: parsed.location,
        };
      });
  }

  if (typeof message === "object") {
    const errors: VerificationResult["errors"] = [];
    for (const [category, value] of Object.entries(message as Record<string, unknown>)) {
      const entry = value as { message?: unknown };
      const messages = Array.isArray(entry?.message) ? entry.message : [];
      for (const item of messages) {
        const text = String(item).trim();
        if (!text) continue;
        const parsed = splitMessageAndLocation(text);
        errors.push({
          code: toErrorCode(category),
          message: parsed.message,
          location: parsed.location,
        });
      }
    }
    return errors;
  }

  return [];
}

function hasMeaningfulVerificationErrors(errors: VerificationResult["errors"]): boolean {
  return Boolean(
    errors?.some((error) => error.message?.trim() || error.location?.trim() || error.code?.trim()),
  );
}

async function parseVerificationResponse(response: Response): Promise<VerificationResult> {
  const payload = await response.json();

  if (typeof payload?.success === "boolean") {
    return payload as VerificationResult;
  }

  const backendError = payload as BackendErrorPayload;
  if (!response.ok || backendError?.error) {
    return {
      success: false,
      message: "Verification failed.",
      errors: [
        {
          code: backendError?.error?.code ?? "API_ERROR",
          message: backendError?.error?.message ?? "Unknown API error",
        },
      ],
    };
  }

  const backendVerification = payload as BackendVerificationPayload;
  const verificationResult = backendVerification?.verification?.result ?? "";
  const verificationMessage = backendVerification?.verification?.message;
  const rawSuccess = verificationResult.toLowerCase() === "success";
  const normalizedErrors = rawSuccess ? [] : normalizeVerificationErrors(verificationMessage);
  const success = rawSuccess || !hasMeaningfulVerificationErrors(normalizedErrors);
  const errors = success ? [] : normalizedErrors;
  const message =
    typeof verificationMessage === "string"
      ? verificationMessage
      : success
        ? "Verification passed."
        : "Verification failed.";

  return {
    success,
    message,
    errors,
  };
}

async function parseFixResponse(response: Response): Promise<LlmFixResponse> {
  let payload: any = null;
  let rawText = "";
  const fallbackResponse = response.clone();
  try {
    payload = await response.json();
  } catch {
    payload = null;
    try {
      rawText = (await fallbackResponse.text()).trim();
    } catch {
      rawText = "";
    }
  }

  if (!response.ok) {
    const backendError = (payload ?? {}) as BackendErrorPayload;
    const genericByStatus = `Failed to request LLM fix (HTTP ${response.status})`;
    return {
      success: false,
      message:
        backendError?.error?.message
        ?? (typeof payload?.message === "string" ? payload.message : undefined)
        ?? (rawText ? rawText.slice(0, 300) : undefined)
        ?? genericByStatus,
      raw: payload,
    };
  }

  if (typeof payload?.success === "boolean") {
    return payload as LlmFixResponse;
  }

  if (Array.isArray(payload?.suggestions)) {
    return {
      success: true,
      suggestions: payload.suggestions as LlmFixSuggestion[],
      updatedFile: typeof payload.updatedFile === "string" ? payload.updatedFile : undefined,
      remainingErrors: Array.isArray(payload.remainingErrors)
        ? (payload.remainingErrors as FixTargetError[])
        : undefined,
      raw: payload,
    };
  }

  const anchorPairs = normalizeAnchorPairs(payload?.anchor_pairs);
  if (payload?.status === "success" && anchorPairs.length > 0) {
    return {
      success: true,
      message:
        typeof payload?.llm_summary?.message === "string"
          ? payload.llm_summary.message
          : typeof payload?.status === "string"
            ? payload.status
            : "LLM repair completed.",
      suggestions: buildSuggestionsFromAnchorPairs(anchorPairs),
      updatedFile:
        typeof payload?.patched_json === "string"
          ? payload.patched_json
          : payload?.patched_json && typeof payload.patched_json === "object"
            ? stringifyJson(payload.patched_json)
          : undefined,
      raw: payload,
    };
  }

  return {
    success: true,
    message: payload?.message,
    suggestions: Array.isArray(payload?.data?.suggestions)
      ? (payload.data.suggestions as LlmFixSuggestion[])
      : undefined,
    updatedFile:
      typeof payload?.updatedFile === "string"
        ? payload.updatedFile
        : typeof payload?.data?.updatedFile === "string"
          ? payload.data.updatedFile
          : undefined,
    remainingErrors: Array.isArray(payload?.remainingErrors)
      ? (payload.remainingErrors as FixTargetError[])
      : Array.isArray(payload?.data?.remainingErrors)
        ? (payload.data.remainingErrors as FixTargetError[])
        : undefined,
    raw: payload,
  };
}

async function requestMultipartFixByEndpoint(
  endpoint: string,
  directEndpoint: string,
  file: File,
  extraFields?: Record<string, string>,
): Promise<LlmFixResponse> {
  const isProxyEndpoint = endpoint.startsWith("/");
  const formData = new FormData();
  formData.append("file", file);
  if (extraFields) {
    Object.entries(extraFields).forEach(([key, value]) => {
      formData.append(key, value);
    });
  }

  const requestInit: RequestInit = {
    method: "POST",
    body: formData,
  };

  try {
    const proxyResponse = await fetch(endpoint, requestInit);
    if (proxyResponse.ok || !isProxyEndpoint || proxyResponse.status < 500) {
      return parseFixResponse(proxyResponse);
    }

    const directResponse = await fetch(directEndpoint, requestInit);
    return parseFixResponse(directResponse);
  } catch (error) {
    if (isProxyEndpoint) {
      try {
        const directResponse = await fetch(directEndpoint, requestInit);
        return parseFixResponse(directResponse);
      } catch {
        // fall through
      }
    }

    return {
      success: false,
      message:
        error instanceof Error
          ? `Failed to upload repair file (proxy and direct fallback): ${error.message}`
          : "Failed to upload repair file",
    };
  }
}

export const apiClient = {
  async verifyMetamodel(file: File): Promise<VerificationResult> {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetchApi("/verification/metamodel", {
      method: "POST",
      body: formData,
    });

    return parseVerificationResponse(response);
  },

  async verifyTemplate(file: File): Promise<VerificationResult> {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetchApi("/verification/template", {
      method: "POST",
      body: formData,
    });

    return parseVerificationResponse(response);
  },

  async verifyInstance(file: File): Promise<VerificationResult> {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetchApi("/verification/instance", {
      method: "POST",
      body: formData,
    });

    return parseVerificationResponse(response);
  },

  async createSchema(file: File): Promise<VerificationResult> {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetchApi("/verification/schema", {
      method: "POST",
      body: formData,
    });

    return response.json();
  },

  async searchSchemas(params?: {
    semanticId?: string;
    uploadedBy?: string;
  }): Promise<Schema[]> {
    const searchParams = new URLSearchParams();
    if (params?.semanticId)
      searchParams.append("semanticId", params.semanticId);
    if (params?.uploadedBy)
      searchParams.append("uploadedBy", params.uploadedBy);

    const response = await fetchApi(`/verification/schema/search?${searchParams}`);
    return response.json();
  },

  async deleteSchema(
    semanticId: string,
  ): Promise<{ success: boolean; message: string }> {
    const response = await fetchApi(
      `/verification/schema/delete/${encodeURIComponent(semanticId)}`,
      {
        method: "DELETE",
      },
    );

    return response.json();
  },

  async updateSchemaPut(file: File): Promise<VerificationResult> {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetchApi("/verification/schema", {
      method: "PUT",
      body: formData,
    });

    return response.json();
  },

  async updateSchemaPatch(file: File): Promise<VerificationResult> {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetchApi("/verification/schema", {
      method: "PATCH",
      body: formData,
    });

    return response.json();
  },

  async requestLlmFix(request: LlmFixRequest): Promise<LlmFixResponse> {
    return requestFixByEndpoint(FIX_API_ENDPOINT, DIRECT_FIX_ENDPOINT, request);
  },

  async requestRuleFix(request: LlmFixRequest): Promise<LlmFixResponse> {
    return requestFixByEndpoint(RULE_FIX_API_ENDPOINT, DIRECT_RULE_FIX_ENDPOINT, request);
  },

  async requestLlmRepair(request: LlmFixRequest): Promise<LlmFixResponse> {
    return requestFixByEndpoint(LLM_REPAIR_API_ENDPOINT, DIRECT_LLM_REPAIR_ENDPOINT, request);
  },

  async requestLlmRepairFile(file: File, extraFields?: Record<string, string>): Promise<LlmFixResponse> {
    return requestMultipartFixByEndpoint(
      LLM_REPAIR_API_ENDPOINT,
      DIRECT_LLM_REPAIR_ENDPOINT,
      file,
      extraFields,
    );
  },
};

async function requestFixByEndpoint(
  endpoint: string,
  directEndpoint: string,
  request: LlmFixRequest,
): Promise<LlmFixResponse> {
    const isProxyEndpoint = endpoint.startsWith("/");
    const requestInit: RequestInit = {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
    };

    try {
      const proxyResponse = await fetch(endpoint, requestInit);
      if (proxyResponse.ok || !isProxyEndpoint || proxyResponse.status < 500) {
        return parseFixResponse(proxyResponse);
      }

      const directResponse = await fetch(directEndpoint, requestInit);
      return parseFixResponse(directResponse);
    } catch (error) {
      if (isProxyEndpoint) {
        try {
          const directResponse = await fetch(directEndpoint, requestInit);
          return parseFixResponse(directResponse);
        } catch {
          // fall through and return proxy error message
        }
      }

      return {
        success: false,
        message:
          error instanceof Error
            ? `Failed to fetch fix API (proxy and direct fallback): ${error.message}`
            : "Failed to fetch fix API",
      };
    }
}
