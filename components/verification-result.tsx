'use client';

import { useEffect, useMemo, useState } from 'react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { CheckCircle2, XCircle, AlertCircle, ChevronDown, ChevronRight, Wand2, Loader2 } from 'lucide-react';
import { apiClient, type LlmFixSuggestion, type VerificationResult as ApiVerificationResult } from '@/lib/api-client';
import {
  type FixContextSnippet,
  buildSnippetContext,
} from '@/lib/verification-fix-utils';

export interface VerificationError {
  code: string;
  message: string;
  location?: string;
}

interface VerificationResultProps {
  success: boolean;
  message?: string;
  errors?: VerificationError[];
  verificationType?: 'metamodel' | 'template' | 'instance';
  fileName?: string;
  sourceFile?: File | null;
}

type FixStatus = 'idle' | 'requested' | 'generated' | 'applied' | 'failed';

interface FixPipelineSummary {
  llmMatchedCount: number;
}

const INITIAL_GROUP_ITEM_LIMIT = 5;
const SEND_FILE_CONTEXT_FOR_FIX = true;

export function VerificationResult({
  success,
  message,
  errors,
  verificationType = 'metamodel',
  fileName,
  sourceFile,
}: VerificationResultProps) {
  const [expandedGroups, setExpandedGroups] = useState<Record<string, boolean>>({});
  const [fixStatuses, setFixStatuses] = useState<Record<string, FixStatus>>({});
  const [fixSuggestions, setFixSuggestions] = useState<Record<string, LlmFixSuggestion>>({});
  const [sentSnippets, setSentSnippets] = useState<Record<string, string>>({});
  const [isRequestingSelected, setIsRequestingSelected] = useState(false);
  const [updatedFileContent, setUpdatedFileContent] = useState<string | null>(null);
  const [liveResult, setLiveResult] = useState<ApiVerificationResult | null>(null);
  const [lastPipelineSummary, setLastPipelineSummary] = useState<FixPipelineSummary | null>(null);

  useEffect(() => {
    setLiveResult(null);
    setFixStatuses({});
    setFixSuggestions({});
    setSentSnippets({});
    setUpdatedFileContent(null);
    setExpandedGroups({});
    setLastPipelineSummary(null);
  }, [fileName, verificationType, errors, message, success]);

  const effectiveSuccess = liveResult?.success ?? success;
  const effectiveMessage = liveResult?.message ?? message;
  const effectiveErrors = liveResult?.errors ?? errors;

  const indexedErrors = useMemo(
    () =>
      (effectiveErrors ?? []).map((error, index) => ({
        ...error,
        id: `${error.code}|${error.location ?? ''}|${index}`,
      })),
    [effectiveErrors],
  );

  const groupedErrors = useMemo(() => {
    const groups = new Map<string, Array<VerificationError & { id: string }>>();
    for (const error of indexedErrors) {
      const key = error.code || 'UNKNOWN_ERROR';
      const current = groups.get(key) ?? [];
      current.push(error);
      groups.set(key, current);
    }

    return Array.from(groups.entries()).sort((a, b) => b[1].length - a[1].length);
  }, [indexedErrors]);

  const generatedCount = useMemo(
    () => indexedErrors.filter((error) => fixStatuses[error.id] === 'generated').length,
    [indexedErrors, fixStatuses],
  );
  const remainingCount = useMemo(
    () => Math.max(indexedErrors.length - generatedCount, 0),
    [indexedErrors.length, generatedCount],
  );

  const toggleGroup = (code: string) => {
    setExpandedGroups((prev) => ({ ...prev, [code]: !prev[code] }));
  };

  const mapSuggestionsToErrors = (
    targets: Array<VerificationError & { id: string }>,
    suggestions: LlmFixSuggestion[],
  ): Record<string, LlmFixSuggestion> => {
    const byErrorId = new Map<string, LlmFixSuggestion>();
    const byCodeLocation = new Map<string, LlmFixSuggestion>();
    const byMessage = new Map<string, LlmFixSuggestion>();
    for (const suggestion of suggestions) {
      if (suggestion.errorId) byErrorId.set(suggestion.errorId, suggestion);
      const key = `${suggestion.code ?? ''}|${suggestion.location ?? ''}`;
      if (key !== '|') byCodeLocation.set(key, suggestion);

      const raw = suggestion.raw as {
        anchorPair?: {
          error_messages?: string[];
        };
      } | undefined;
      const anchorMessages = raw?.anchorPair?.error_messages ?? [];
      anchorMessages.forEach((msg) => {
        const normalized = msg.split(' @ /')[0]?.trim();
        if (normalized) byMessage.set(normalized, suggestion);
      });

      if (suggestion.summary?.trim()) {
        byMessage.set(suggestion.summary.trim(), suggestion);
      }
    }

    const mappedSuggestions: Record<string, LlmFixSuggestion> = {};
    targets.forEach((error, index) => {
      const mapped =
        byErrorId.get(error.id)
        ?? byCodeLocation.get(`${error.code}|${error.location ?? ''}`)
        ?? byMessage.get(error.message.trim())
        ?? suggestions[index];
      if (mapped) mappedSuggestions[error.id] = mapped;
    });

    return mappedSuggestions;
  };

  const assignSuggestionsToErrors = (
    targets: Array<VerificationError & { id: string }>,
    mappedSuggestions: Record<string, LlmFixSuggestion>,
  ) => {

    setFixStatuses((prev) => {
      const nextStatuses: Record<string, FixStatus> = { ...prev };
      targets.forEach((error) => {
        const mapped = mappedSuggestions[error.id];
        nextStatuses[error.id] = mapped ? 'generated' : 'failed';
      });
      return nextStatuses;
    });

    setFixSuggestions((prev) => {
      const nextSuggestions: Record<string, LlmFixSuggestion> = { ...prev };
      targets.forEach((error) => {
        const mapped = mappedSuggestions[error.id];
        if (mapped) nextSuggestions[error.id] = mapped;
      });
      return nextSuggestions;
    });
  };

  const requestFixForErrors = async (targets: Array<VerificationError & { id: string }>) => {
    if (targets.length === 0) return;
    setLastPipelineSummary(null);

    setFixStatuses((prev) => {
      const next = { ...prev };
      for (const target of targets) next[target.id] = 'requested';
      return next;
    });

    let sourceText: string | undefined;
    if (sourceFile) {
      try {
        sourceText = await sourceFile.text();
      } catch {
        sourceText = undefined;
      }
    }

    const buildContextPayload = (currentTargets: Array<VerificationError & { id: string }>) => {
      if (!sourceText) return undefined;
      const snippetContext = buildSnippetContext(sourceText, currentTargets);
      if (SEND_FILE_CONTEXT_FOR_FIX) {
        return {
          ...(snippetContext ?? {}),
          originalFileContent: sourceText,
        } satisfies Record<string, unknown>;
      }
      return snippetContext;
    };

    const contextPayload = buildContextPayload(targets);
    if (contextPayload?.snippets && Array.isArray(contextPayload.snippets)) {
      setSentSnippets((prev) => {
        const next = { ...prev };
        for (const snippet of contextPayload.snippets as FixContextSnippet[]) {
          if (snippet?.errorId && snippet?.snippet) {
            next[snippet.errorId] = snippet.snippet;
          }
        }
        return next;
      });
    }

    const baseRequest = {
      mode: targets.length > 1 ? 'batch' : 'single',
      verificationType,
      fileName,
      includeUpdatedFile: Boolean(sourceText),
      errors: targets.map((target) => ({
        id: target.id,
        code: target.code,
        message: target.message,
        location: target.location,
      })),
      context: contextPayload,
    };

    const llmResponse = sourceFile
      ? await apiClient.requestLlmRepairFile(sourceFile, {
        verificationType,
        fileName: sourceFile.name,
      })
      : null;

    if (!llmResponse?.success) {
      const msg = llmResponse?.message ?? 'LLM 수정 요청에 실패했습니다.';
      alert(msg);
      setFixStatuses((prev) => {
        const next = { ...prev };
        for (const t of targets) next[t.id] = 'failed';
        return next;
      });
      return;
    }

    const llmMappedSuggestions = mapSuggestionsToErrors(targets, llmResponse.suggestions ?? []);
    assignSuggestionsToErrors(targets, llmMappedSuggestions);

    if (llmResponse?.updatedFile) {
      setUpdatedFileContent(llmResponse.updatedFile);
    }

    const rawMeta = (llmResponse?.raw ?? {}) as {
      llmMatchedCount?: number;
    };
    if (rawMeta) {
      setLastPipelineSummary({
        llmMatchedCount: Number(rawMeta.llmMatchedCount ?? (llmResponse?.suggestions?.length ?? 0)),
      });
    }
  };

  const downloadUpdatedFile = () => {
    if (!updatedFileContent) return;
    const blob = new Blob([updatedFileContent], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    const base = fileName?.replace(/\.json$/i, '') ?? '수정된-모델';
    a.href = url;
    a.download = `${base}.fixed.json`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  };

  const getFixStatusLabel = (status: FixStatus) => {
    if (status === 'requested') return '요청됨';
    if (status === 'generated') return '수정안 준비됨';
    if (status === 'failed') return '실패';
    return '대기';
  };

  const getFixStatusVariant = (status: FixStatus): 'secondary' | 'outline' | 'success' | 'destructive' => {
    if (status === 'generated') return 'secondary';
    if (status === 'failed') return 'destructive';
    return 'outline';
  };

  const getSuggestionSourceLabel = (suggestion?: LlmFixSuggestion): '규칙 기반 결과' | 'LLM 결과' => {
    const raw = suggestion?.raw as { source?: string } | undefined;
    if (raw?.source === 'rule_based_fix') return '규칙 기반 결과';
    return 'LLM 결과';
  };

  const getAnchorPair = (suggestion?: LlmFixSuggestion) => {
    const raw = suggestion?.raw as { anchorPair?: {
      error_messages?: string[];
      broken_anchor?: unknown;
      corrected_anchor?: unknown;
    } } | undefined;
    return raw?.anchorPair;
  };

  return (
    <Card className={effectiveSuccess ? 'border-green-500/50' : 'border-destructive/50'}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            {effectiveSuccess ? (
              <>
                <CheckCircle2 className="h-5 w-5 text-green-500" />
                검증 성공
              </>
            ) : (
              <>
                <XCircle className="h-5 w-5 text-destructive" />
                검증 실패
              </>
            )}
          </CardTitle>
          <Badge variant={effectiveSuccess ? 'success' : 'destructive'}>
            {effectiveSuccess ? '통과' : '실패'}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        {effectiveMessage && (
          <p className="text-sm text-muted-foreground mb-4">{effectiveMessage}</p>
        )}
        
        {effectiveErrors && effectiveErrors.length > 0 && (
          <div className="space-y-3">
            <div className="rounded-md border border-primary/20 bg-primary/5 p-4 space-y-3">
              <div className="flex items-center justify-between gap-2">
                <div>
                  <p className="text-sm font-semibold flex items-center gap-2">
                    <Wand2 className="h-4 w-4 text-primary" />
                    오류 수정 작업 영역
                  </p>
                  <p className="text-xs text-muted-foreground">
                    흐름: 1) 오류 선택 2) 수정 요청 3) 수정안 확인 4) 선택 항목 적용
                  </p>
                  <p className="text-xs text-muted-foreground">
                    모든 오류에 대해 LLM 수정 결과를 확인할 수 있습니다.
                  </p>
                </div>
                <Badge variant="outline">전체 오류 대상</Badge>
              </div>

              <div className="rounded border border-border bg-background/60 p-3 text-xs">
                <p className="font-medium mb-2">수정 파이프라인</p>
                <div className="flex flex-wrap items-center gap-2 text-muted-foreground">
                  <span className={isRequestingSelected ? 'text-foreground font-medium' : ''}>1. 원본 파일 업로드</span>
                  <span>→</span>
                  <span className={isRequestingSelected ? 'text-foreground font-medium' : ''}>2. LLM 분석</span>
                  <span>→</span>
                  <span className={isRequestingSelected ? 'text-foreground font-medium' : ''}>3. 수정 결과 확인</span>
                </div>
                {lastPipelineSummary && (
                  <div className="mt-2 grid grid-cols-1 gap-2 text-[11px] md:grid-cols-2">
                    <div className="rounded border border-border p-2">
                      <p className="text-muted-foreground">LLM 수정안</p>
                      <p className="font-semibold">{lastPipelineSummary.llmMatchedCount}건</p>
                    </div>
                    <div className="rounded border border-border p-2">
                      <p className="text-muted-foreground">최종 파일 생성</p>
                      <p className="font-semibold">{updatedFileContent ? '예' : '아니오'}</p>
                    </div>
                  </div>
                )}
              </div>

              <div className="grid grid-cols-4 gap-2 text-xs">
                <div className="rounded border border-border p-2">
                  <p className="text-muted-foreground">수정안 준비</p>
                  <p className="font-semibold">{generatedCount}</p>
                </div>
                <div className="rounded border border-border p-2">
                  <p className="text-muted-foreground">미매칭 오류</p>
                  <p className="font-semibold">{remainingCount}</p>
                </div>
              </div>

              <div className="flex flex-wrap gap-2">
                <Button
                  size="sm"
                  disabled={indexedErrors.length === 0 || isRequestingSelected}
                  onClick={async () => {
                    setIsRequestingSelected(true);
                    try {
                      await requestFixForErrors(indexedErrors);
                    } finally {
                      setIsRequestingSelected(false);
                    }
                  }}
                >
                  {isRequestingSelected ? '요청 중...' : '전체 오류 LLM 수정 요청'}
                </Button>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={downloadUpdatedFile}
                  disabled={!updatedFileContent}
                >
                  수정된 파일 다운로드
                </Button>
              </div>
              {isRequestingSelected && (
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  원본 파일을 LLM에 전달하고 수정 결과를 가져오는 중...
                </div>
              )}
            </div>

            <div className="flex items-center gap-2 text-sm font-medium">
              <AlertCircle className="h-4 w-4" />
              발견된 오류 ({effectiveErrors.length})
              <span className="text-muted-foreground font-normal">
                / {groupedErrors.length}종류
              </span>
            </div>
            <div className="max-h-[28rem] overflow-y-auto pr-1 space-y-3">
              {groupedErrors.map(([code, grouped], index) => {
                const isExpanded = expandedGroups[code] ?? index === 0;
                const visible = isExpanded ? grouped : grouped.slice(0, INITIAL_GROUP_ITEM_LIMIT);
                const hiddenCount = grouped.length - visible.length;

                return (
                  <div
                    key={code}
                    className="rounded-md border border-destructive/20 bg-destructive/5"
                  >
                    <div className="flex items-center justify-between p-3 border-b border-destructive/10">
                      <div className="flex items-center gap-2">
                        <button
                          type="button"
                          onClick={() => toggleGroup(code)}
                          className="inline-flex items-center gap-1 text-sm font-medium text-destructive"
                        >
                          {isExpanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                          {code}
                        </button>
                        <Badge variant="destructive">{grouped.length}</Badge>
                      </div>
                    </div>

                    <div className="space-y-2 p-3">
                      {visible.map((error, itemIndex) => (
                        <div key={`${code}-${itemIndex}`} className="rounded-md bg-background/70 p-3 border border-border">
                          <div className="flex items-start justify-between gap-3">
                            <div className="flex-1">
                              <p className="text-sm text-muted-foreground">{error.message}</p>
                              {error.location && (
                                <p className="text-xs text-muted-foreground mt-1 font-mono">
                                  위치: {error.location}
                                </p>
                              )}
                            </div>
                            <div className="flex items-center gap-2">
                              <Badge variant={getFixStatusVariant(fixStatuses[error.id] ?? 'idle')}>
                                {getFixStatusLabel(fixStatuses[error.id] ?? 'idle')}
                              </Badge>
                            </div>
                          </div>
                          {(fixSuggestions[error.id] || sentSnippets[error.id]) && (
                            <div className="mt-2 grid gap-2 md:grid-cols-2">
                              <div className="rounded border border-border p-2 bg-muted/20">
                                <p className="text-xs font-medium mb-1">LLM에 전달된 내용</p>
                                {getAnchorPair(fixSuggestions[error.id]) ? (
                                  <pre className="text-[11px] leading-4 text-muted-foreground whitespace-pre-wrap break-words">
                                    {JSON.stringify(getAnchorPair(fixSuggestions[error.id])?.broken_anchor ?? {}, null, 2)}
                                  </pre>
                                ) : (
                                  <pre className="text-[11px] leading-4 text-muted-foreground whitespace-pre-wrap break-words">
                                    {sentSnippets[error.id] ?? '이 오류에 대해 전달된 스니펫이 없습니다.'}
                                  </pre>
                                )}
                              </div>
                              <div className="rounded border border-border p-2 bg-muted/30">
                                <p className="text-xs font-medium mb-1">{getSuggestionSourceLabel(fixSuggestions[error.id])}</p>
                                {getAnchorPair(fixSuggestions[error.id]) ? (
                                  <div className="space-y-2 text-[11px] leading-4 text-muted-foreground">
                                    <div>
                                      <pre className="whitespace-pre-wrap break-words">
                                        {JSON.stringify(getAnchorPair(fixSuggestions[error.id])?.corrected_anchor ?? {}, null, 2)}
                                      </pre>
                                    </div>
                                  </div>
                                ) : (
                                  <pre className="text-[11px] leading-4 text-muted-foreground whitespace-pre-wrap break-words">
                                    {fixSuggestions[error.id]?.fixedSnippet
                                      ?? fixSuggestions[error.id]?.patch
                                      ?? fixSuggestions[error.id]?.summary
                                      ?? fixSuggestions[error.id]?.reason
                                      ?? '응답을 기다리는 중...'}
                                  </pre>
                                )}
                              </div>
                            </div>
                          )}
                        </div>
                      ))}

                      {hiddenCount > 0 && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => toggleGroup(code)}
                          className="w-full"
                        >
                          {hiddenCount}개 더 보기
                        </Button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {effectiveSuccess && !effectiveMessage && (
          <p className="text-sm text-green-600 dark:text-green-400">
            모든 검증을 통과했습니다. 현재 AAS 파일은 요구 규격을 만족합니다.
          </p>
        )}
      </CardContent>
    </Card>
  );
}
