export type JsonValue = null | boolean | number | string | JsonValue[] | { [key: string]: JsonValue };

export interface ErrorWithId {
  id: string;
  code: string;
  message: string;
  location?: string;
}

export interface FixContextSnippet {
  errorId: string;
  code: string;
  location?: string;
  pointer?: string;
  targetType: string;
  snippet: string;
}

const MAX_SNIPPET_CHARS = 2000;
const MAX_SNIPPETS_PER_REQUEST = 5;

function toCamelCaseToken(token: string): string {
  return token.replace(/_([a-zA-Z0-9])/g, (_, ch: string) => ch.toUpperCase());
}

function toSnakeCaseToken(token: string): string {
  return token
    .replace(/([a-z0-9])([A-Z])/g, '$1_$2')
    .replace(/-/g, '_')
    .toLowerCase();
}

function expandBracketToken(token: string): string[] {
  if (!token) return [];
  const tokens: string[] = [];
  const re = /([^[\]]+)|\[(\d+)\]/g;
  let m: RegExpExecArray | null = re.exec(token);
  while (m) {
    if (m[1]) tokens.push(m[1]);
    if (m[2]) tokens.push(m[2]);
    m = re.exec(token);
  }
  return tokens.length > 0 ? tokens : [token];
}

export function normalizePathTokens(tokens: string[]): string[] {
  const normalized: string[] = [];
  for (const token of tokens) {
    normalized.push(...expandBracketToken(token));
  }
  return normalized;
}

function resolveObjectKey(obj: Record<string, JsonValue>, token: string): string | undefined {
  if (token in obj) return token;
  const camel = toCamelCaseToken(token);
  if (camel in obj) return camel;
  const snake = toSnakeCaseToken(token);
  if (snake in obj) return snake;
  return undefined;
}

function decodeJsonPointerToken(token: string): string {
  return token.replace(/~1/g, '/').replace(/~0/g, '~');
}

export function parseJsonPointer(pointer?: string): string[] {
  if (!pointer) return [];
  if (!pointer.startsWith('/')) {
    const normalized = pointer.trim().replace(/^@+\s*/, '');
    if (!normalized) return [];
    return parseFieldExpression(normalized.replace(/\//g, '.'));
  }
  return normalizePathTokens(
    pointer
      .split('/')
      .slice(1)
      .map(decodeJsonPointerToken),
  );
}

export function getByPointer(root: JsonValue, tokens: string[]): JsonValue | undefined {
  let current: JsonValue | undefined = root;
  for (const token of tokens) {
    if (Array.isArray(current)) {
      const index = Number(token);
      if (!Number.isInteger(index) || index < 0 || index >= current.length) return undefined;
      current = current[index];
      continue;
    }
    if (current && typeof current === 'object') {
      const obj = current as Record<string, JsonValue>;
      const resolved = resolveObjectKey(obj, token);
      if (!resolved) return undefined;
      current = obj[resolved];
      continue;
    }
    return undefined;
  }
  return current;
}

function setByPointer(root: JsonValue, tokens: string[], value: JsonValue): boolean {
  if (tokens.length === 0) return false;
  const parentTokens = tokens.slice(0, -1);
  const key = tokens[tokens.length - 1];
  const parent = getByPointer(root, parentTokens);

  if (Array.isArray(parent)) {
    const index = Number(key);
    if (!Number.isInteger(index) || index < 0 || index > parent.length) return false;
    if (index === parent.length) {
      parent.push(value);
      return true;
    }
    parent[index] = value;
    return true;
  }
  if (parent && typeof parent === 'object') {
    const obj = parent as Record<string, JsonValue>;
    const resolved = resolveObjectKey(obj, key) ?? key;
    obj[resolved] = value;
    return true;
  }
  return false;
}

export function isPlainObject(value: JsonValue | undefined): value is Record<string, JsonValue> {
  return Boolean(value) && typeof value === 'object' && !Array.isArray(value);
}

export function deepMergeObjects(
  baseObj: Record<string, JsonValue>,
  patchObj: Record<string, JsonValue>,
): Record<string, JsonValue> {
  const merged: Record<string, JsonValue> = { ...baseObj };
  for (const [rawKey, patchVal] of Object.entries(patchObj)) {
    const resolvedKey = resolveObjectKey(baseObj, rawKey) ?? rawKey;
    const baseVal = merged[resolvedKey];
    if (isPlainObject(baseVal) && isPlainObject(patchVal)) {
      merged[resolvedKey] = deepMergeObjects(baseVal, patchVal);
    } else {
      merged[resolvedKey] = patchVal;
    }
  }
  return merged;
}

export function setByPointerWithCreate(root: JsonValue, tokens: string[], value: JsonValue): boolean {
  if (tokens.length === 0) return false;
  let current: JsonValue = root;

  for (let i = 0; i < tokens.length - 1; i += 1) {
    const token = tokens[i];
    const nextToken = tokens[i + 1];
    const nextShouldBeArray = Number.isInteger(Number(nextToken));

    if (Array.isArray(current)) {
      const index = Number(token);
      if (!Number.isInteger(index) || index < 0) return false;
      if (index > current.length) {
        while (current.length < index) current.push(null);
      }
      if (index === current.length) {
        current.push(nextShouldBeArray ? [] : {});
      } else if (typeof current[index] === 'undefined' || current[index] === null) {
        current[index] = nextShouldBeArray ? [] : {};
      }
      current = current[index];
      continue;
    }

    if (current && typeof current === 'object') {
      const obj = current as Record<string, JsonValue>;
      const resolved = resolveObjectKey(obj, token) ?? token;
      if (typeof obj[resolved] === 'undefined' || obj[resolved] === null) {
        obj[resolved] = nextShouldBeArray ? [] : {};
      }
      current = obj[resolved];
      continue;
    }

    return false;
  }

  return setByPointer(root, tokens, value);
}

function parseFieldExpression(expr: string): string[] {
  const segments = expr.split('.');
  return normalizePathTokens(segments);
}

export function inferMissingFieldTokens(message?: string): string[] {
  if (!message) return [];
  const match = message.match(/:\s*([A-Za-z0-9_.\[\]]+)\s+is missing/i);
  if (!match?.[1]) return [];
  return parseFieldExpression(match[1]);
}

export function inferUnexpectedExpectedFix(
  message?: string,
): { fieldTokens: string[]; expectedValue: string } | undefined {
  if (!message) return undefined;
  const fieldMatch = message.match(/^([A-Za-z0-9_.\[\]\/]+)\s+has unexpected value/i);
  const expectedMatch = message.match(/\bexpected\b\s+(.+)$/i);
  if (!fieldMatch?.[1] || !expectedMatch?.[1]) return undefined;

  const rawField = fieldMatch[1].replace(/\//g, '.');
  const fieldTokens = parseFieldExpression(rawField);
  const expectedValue = expectedMatch[1].trim();
  if (fieldTokens.length === 0 || !expectedValue) return undefined;
  return { fieldTokens, expectedValue };
}

function summarizeObjectAroundKey(
  obj: Record<string, JsonValue>,
  focusKey?: string,
): Record<string, JsonValue> {
  const keys = Object.keys(obj);
  if (keys.length <= 8) return obj;

  const selected: string[] = [];
  if (focusKey && keys.includes(focusKey)) selected.push(focusKey);
  for (const key of keys) {
    if (selected.length >= 8) break;
    if (!selected.includes(key)) selected.push(key);
  }

  const summarized: Record<string, JsonValue> = {};
  for (const key of selected) summarized[key] = obj[key];
  summarized.__truncatedKeys = `${keys.length - selected.length} omitted`;
  return summarized;
}

function stringifySnippet(value: JsonValue): string {
  const raw = JSON.stringify(value, null, 2);
  if (!raw) return '';
  if (raw.length <= MAX_SNIPPET_CHARS) return raw;
  return `${raw.slice(0, MAX_SNIPPET_CHARS)}\n...<truncated snippet>...`;
}

function buildSnippet(root: JsonValue, error: ErrorWithId): FixContextSnippet | null {
  const tokens = parseJsonPointer(error.location);
  const target = tokens.length > 0 ? getByPointer(root, tokens) : undefined;
  if (typeof target === 'undefined') return null;

  const parentTokens = tokens.slice(0, -1);
  const lastToken = tokens.length > 0 ? tokens[tokens.length - 1] : undefined;
  const parent = parentTokens.length > 0 ? getByPointer(root, parentTokens) : root;

  let payload: JsonValue = target;
  if (Array.isArray(parent) && typeof lastToken !== 'undefined') {
    const idx = Number(lastToken);
    if (Number.isInteger(idx)) {
      const start = Math.max(0, idx - 1);
      const end = Math.min(parent.length, idx + 2);
      payload = {
        pointer: error.location ?? '',
        index: idx,
        windowStart: start,
        window: parent.slice(start, end),
      };
    }
  } else if (parent && typeof parent === 'object' && !Array.isArray(parent) && lastToken) {
    payload = {
      pointer: error.location ?? '',
      parent: summarizeObjectAroundKey(parent as Record<string, JsonValue>, lastToken),
      focusKey: lastToken,
      focusValue: target,
    };
  }

  return {
    errorId: error.id,
    code: error.code,
    location: error.location,
    pointer: error.location,
    targetType: Array.isArray(target) ? 'array' : typeof target,
    snippet: stringifySnippet(payload),
  };
}

export function buildSnippetContext(
  sourceText: string,
  targets: ErrorWithId[],
): Record<string, unknown> | undefined {
  try {
    const parsed = JSON.parse(sourceText) as JsonValue;
    const snippets: FixContextSnippet[] = [];
    for (const target of targets) {
      if (snippets.length >= MAX_SNIPPETS_PER_REQUEST) break;
      const snippet = buildSnippet(parsed, target);
      if (snippet) snippets.push(snippet);
    }

    if (snippets.length === 0) return undefined;
    return {
      snippets,
      guidance: 'Use snippets as authoritative local context for each errorId.',
    };
  } catch {
    return undefined;
  }
}

function stripCodeFence(text: string): string {
  const trimmed = text.trim();
  if (!trimmed.startsWith('```')) return trimmed;
  const withoutStart = trimmed.replace(/^```(?:json)?\s*/i, '');
  return withoutStart.replace(/\s*```$/, '').trim();
}

export function parseJsonCandidate(text?: string): JsonValue | undefined {
  if (!text) return undefined;
  const candidate = stripCodeFence(text);
  try {
    return JSON.parse(candidate) as JsonValue;
  } catch {
    return undefined;
  }
}

export function parsePrimitiveCandidate(text?: string): JsonValue | undefined {
  if (!text) return undefined;
  const candidate = stripCodeFence(text).trim();
  if (!candidate) return undefined;

  const asJson = parseJsonCandidate(candidate);
  if (typeof asJson !== 'undefined') return asJson;

  if (/^(true|false)$/i.test(candidate)) return candidate.toLowerCase() === 'true';
  if (/^null$/i.test(candidate)) return null;
  if (/^-?\d+(\.\d+)?$/.test(candidate)) return Number(candidate);

  const quoted = candidate.match(/^"([\s\S]*)"$/) || candidate.match(/^'([\s\S]*)'$/);
  if (quoted) return quoted[1];

  const looksSerializedJson = /[\{\}\[\]]/.test(candidate) || candidate.includes('\n');
  if (looksSerializedJson && candidate.length > 80) return undefined;
  return candidate;
}

export function parsePatchReplacement(
  patch?: string,
): { op: 'replace' | 'add' | 'remove'; pathTokens: string[]; value: JsonValue | undefined } | undefined {
  if (!patch) return undefined;
  try {
    const parsed = JSON.parse(stripCodeFence(patch));
    if (Array.isArray(parsed)) {
      if (parsed.length >= 3 && typeof parsed[0] === 'string') {
        const op = parsed[0] as 'replace' | 'add' | 'remove';
        const pathRaw = parsed[1];
        const value = parsed[2] as JsonValue;
        if (op !== 'replace' && op !== 'add' && op !== 'remove') return undefined;
        if (typeof pathRaw === 'string') {
          return { op, pathTokens: parseJsonPointer(pathRaw), value };
        }
        if (Array.isArray(pathRaw)) {
          const joined = pathRaw.map((v) => String(v)).join('');
          return { op, pathTokens: parseJsonPointer(joined), value };
        }
      }
      if (parsed.length > 0 && typeof parsed[0] === 'object' && parsed[0] !== null) {
        const first = parsed[0] as { op?: string; path?: string; value?: JsonValue };
        if (
          (first.op === 'replace' || first.op === 'add' || first.op === 'remove')
          && typeof first.path === 'string'
        ) {
          return {
            op: first.op,
            pathTokens: parseJsonPointer(first.path),
            value: first.value as JsonValue,
          };
        }
      }
      return undefined;
    }
    if (parsed && typeof parsed === 'object') {
      const obj = parsed as { op?: string; path?: string; value?: JsonValue };
      if ((obj.op === 'replace' || obj.op === 'add' || obj.op === 'remove') && typeof obj.path === 'string') {
        return {
          op: obj.op,
          pathTokens: parseJsonPointer(obj.path),
          value: obj.value as JsonValue,
        };
      }
    }
    return undefined;
  } catch {
    return undefined;
  }
}

function resolveReplacementForPath(
  parsedSnippet: JsonValue | undefined,
  pathTokens: string[],
): JsonValue | undefined {
  if (typeof parsedSnippet === 'undefined') return undefined;
  if (pathTokens.length === 0) return parsedSnippet;

  const fromSamePath = getByPointer(parsedSnippet, pathTokens);
  if (typeof fromSamePath !== 'undefined') return fromSamePath;

  if (parsedSnippet && typeof parsedSnippet === 'object' && !Array.isArray(parsedSnippet)) {
    const first = pathTokens[0];
    if (first in (parsedSnippet as Record<string, JsonValue>)) {
      const value = (parsedSnippet as Record<string, JsonValue>)[first];
      const fromTrimmedPath = getByPointer(value, pathTokens.slice(1));
      if (typeof fromTrimmedPath !== 'undefined') return fromTrimmedPath;
    }
  }

  return undefined;
}

export function deriveReplacementValue(
  parsedSnippet: JsonValue | undefined,
  primitiveSnippet: JsonValue | undefined,
  currentValue: JsonValue | undefined,
  pathTokens: string[],
): JsonValue | undefined {
  const strict = resolveReplacementForPath(parsedSnippet, pathTokens);
  if (typeof strict !== 'undefined') return strict;

  if (parsedSnippet && typeof parsedSnippet === 'object' && !Array.isArray(parsedSnippet)) {
    const obj = parsedSnippet as Record<string, JsonValue>;
    if ('focusValue' in obj) return obj.focusValue;
    if ('value' in obj) return obj.value;
    if ('window' in obj && Array.isArray(obj.window)) {
      const idx = typeof obj.index === 'number' ? obj.index : undefined;
      const start = typeof obj.windowStart === 'number' ? obj.windowStart : undefined;
      if (typeof idx === 'number' && typeof start === 'number') {
        const rel = idx - start;
        if (rel >= 0 && rel < obj.window.length) {
          return obj.window[rel];
        }
      }
      if (obj.window.length > 0) return obj.window[0];
    }

    const last = pathTokens[pathTokens.length - 1];
    const resolvedLast = resolveObjectKey(obj, last ?? '');
    if (resolvedLast) return obj[resolvedLast];
  }

  if (typeof primitiveSnippet !== 'undefined') {
    if (typeof currentValue === 'string' && typeof primitiveSnippet === 'string') return primitiveSnippet;
    if (typeof currentValue === 'number' && typeof primitiveSnippet === 'number') return primitiveSnippet;
    if (typeof currentValue === 'boolean' && typeof primitiveSnippet === 'boolean') return primitiveSnippet;
    if (currentValue === null && primitiveSnippet === null) return primitiveSnippet;
    if (typeof currentValue === 'undefined') return primitiveSnippet;
    return primitiveSnippet;
  }

  if (typeof parsedSnippet !== 'undefined') return parsedSnippet;
  return undefined;
}

function extractDefinitionArrayFromSnippet(parsedSnippet: JsonValue | undefined): JsonValue | undefined {
  if (typeof parsedSnippet === 'undefined') return undefined;
  if (Array.isArray(parsedSnippet)) return parsedSnippet;
  if (!isPlainObject(parsedSnippet)) return undefined;

  const directDefinition = (parsedSnippet as Record<string, JsonValue>).definition;
  if (Array.isArray(directDefinition)) return directDefinition;

  const dsc = (parsedSnippet as Record<string, JsonValue>).dataSpecificationContent;
  if (isPlainObject(dsc)) {
    const nestedDef = (dsc as Record<string, JsonValue>).definition;
    if (Array.isArray(nestedDef)) return nestedDef;
  }

  return undefined;
}

function isLangStringObject(value: JsonValue): boolean {
  return (
    isPlainObject(value)
    && typeof (value as Record<string, JsonValue>).language === 'string'
    && typeof (value as Record<string, JsonValue>).text === 'string'
  );
}

export function normalizeDefinitionReplacement(
  replacement: JsonValue | undefined,
  parsedSnippet: JsonValue | undefined,
  preferredLanguages?: Set<string>,
): JsonValue | undefined {
  let candidate = replacement;
  if (!Array.isArray(candidate)) {
    const extracted = extractDefinitionArrayFromSnippet(parsedSnippet);
    if (Array.isArray(extracted)) candidate = extracted;
  }

  if (Array.isArray(candidate)) {
    let filtered = candidate.filter(isLangStringObject) as Array<Record<string, JsonValue>>;
    if (preferredLanguages && preferredLanguages.size > 0) {
      const byPreferred = filtered.filter((item) => {
        const lang = item.language;
        return typeof lang === 'string' && preferredLanguages.has(lang);
      });
      if (byPreferred.length > 0) {
        filtered = byPreferred;
      }
    }
    const normalized = filtered.map((item) => ({
      language: item.language as string,
      text: item.text as string,
    })) as JsonValue[];
    if (normalized.length > 0) return normalized;
  }
  return undefined;
}

export function getPreferredLanguagesFromDefinitionParent(
  root: JsonValue,
  definitionPathTokens: string[],
): Set<string> {
  const languages = new Set<string>();
  const parent = getByPointer(root, definitionPathTokens.slice(0, -1));
  if (!isPlainObject(parent)) return languages;

  const preferredName = parent.preferredName;
  if (!Array.isArray(preferredName)) return languages;
  for (const item of preferredName) {
    if (isLangStringObject(item)) {
      const lang = (item as Record<string, JsonValue>).language;
      if (typeof lang === 'string') {
        languages.add(lang);
      }
    }
  }
  return languages;
}

function isNumericToken(token: string): boolean {
  return Number.isInteger(Number(token));
}

function normalizeMatchToken(token: string): string {
  return token.replace(/[_-]/g, '').toLowerCase();
}

function tokensRoughlyEqual(a: string, b: string): boolean {
  if (isNumericToken(a) || isNumericToken(b)) return a === b;
  return normalizeMatchToken(a) === normalizeMatchToken(b);
}

function suffixMatchScore(candidate: string[], target: string[]): number {
  let score = 0;
  let i = candidate.length - 1;
  let j = target.length - 1;
  while (i >= 0 && j >= 0) {
    if (!tokensRoughlyEqual(candidate[i], target[j])) break;
    score += 1;
    i -= 1;
    j -= 1;
  }
  return score;
}

function collectContainerPaths(root: JsonValue, maxNodes = 30000): string[][] {
  const paths: string[][] = [];
  const queue: Array<{ value: JsonValue; path: string[] }> = [{ value: root, path: [] }];
  let visited = 0;

  while (queue.length > 0 && visited < maxNodes) {
    const item = queue.shift();
    if (!item) break;
    visited += 1;

    const { value, path } = item;
    if (!value || typeof value !== 'object') continue;
    paths.push(path);

    if (Array.isArray(value)) {
      value.forEach((child, index) => {
        queue.push({ value: child, path: [...path, String(index)] });
      });
      continue;
    }

    Object.entries(value).forEach(([key, child]) => {
      queue.push({ value: child, path: [...path, key] });
    });
  }

  return paths;
}

export function resolveBestEffortPath(root: JsonValue, targetPath: string[]): string[] {
  if (targetPath.length === 0) return targetPath;
  if (typeof getByPointer(root, targetPath) !== 'undefined') return targetPath;

  const parentTarget = targetPath.slice(0, -1);
  const leaf = targetPath[targetPath.length - 1];
  if (parentTarget.length === 0) return targetPath;

  const allContainerPaths = collectContainerPaths(root);
  let bestPath: string[] | undefined;
  let bestScore = 0;

  for (const candidate of allContainerPaths) {
    const candidateValue = getByPointer(root, candidate);
    if (!candidateValue || typeof candidateValue !== 'object' || Array.isArray(candidateValue)) continue;
    const score = suffixMatchScore(candidate, parentTarget);
    if (score > bestScore) {
      bestScore = score;
      bestPath = candidate;
    }
  }

  if (!bestPath || bestScore < 2) return targetPath;
  return [...bestPath, leaf];
}
