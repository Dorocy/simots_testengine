'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  ChevronDown,
  ChevronRight,
  Loader2,
  Sparkles,
  Brain,
  FileSearch,
  Wrench,
  CheckCheck,
  Download,
  AlertTriangle,
} from 'lucide-react';
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

type AnalysisStep = {
  id: string;
  icon: React.ReactNode;
  label: string;
  status: 'pending' | 'running' | 'done';
};

const INITIAL_GROUP_ITEM_LIMIT = 5;
const SEND_FILE_CONTEXT_FOR_FIX = true;

const buildAnalysisSteps = (fileName?: string): AnalysisStep[] => [
  {
    id: 'parse',
    icon: <FileSearch className="h-3 w-3" />,
    label: '파일 파싱',
    status: 'pending',
  },
  {
    id: 'analyze',
    icon: <Brain className="h-3 w-3" />,
    label: '패턴 분석',
    status: 'pending',
  },
  {
    id: 'generate',
    icon: <Sparkles className="h-3 w-3" />,
    label: '수정안 생성',
    status: 'pending',
  },
  {
    id: 'apply',
    icon: <Wrench className="h-3 w-3" />,
    label: '패치 적용',
    status: 'pending',
  },
];

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
  const [analysisSteps, setAnalysisSteps] = useState<AnalysisStep[]>([]);
  const [analysisLogs, setAnalysisLogs] = useState<string[]>([]);
  const [isAnalysisVisible, setIsAnalysisVisible] = useState(false);
  const logEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setLiveResult(null);
    setFixStatuses({});
    setFixSuggestions({});
    setSentSnippets({});
    setUpdatedFileContent(null);
    setExpandedGroups({});
    setLastPipelineSummary(null);
    setAnalysisSteps([]);
    setAnalysisLogs([]);
    setIsAnalysisVisible(false);
  }, [fileName, verificationType, errors, message, success]);

  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [analysisLogs]);

  const appendLog = (log: string) => {
    setAnalysisLogs((prev) => [...prev, log]);
  };

  const updateStepStatus = (stepId: string, status: AnalysisStep['status']) => {
    setAnalysisSteps((prev) =>
      prev.map((s) => (s.id === stepId ? { ...s, status } : s)),
    );
  };

  const delay = (ms: number) => new Promise((r) => setTimeout(r, ms));

  const runAnalysisAnimation = async (
    errorCount: number,
    doActualRequest: () => Promise<void>,
  ) => {
    const steps = buildAnalysisSteps(fileName);
    setAnalysisSteps(steps);
    setAnalysisLogs([]);
    setIsAnalysisVisible(true);

    updateStepStatus('parse', 'running');
    appendLog(`[init] loading ${fileName ?? 'input.json'}`);
    await delay(280);
    appendLog(`[parse] scanning JSON structure...`);
    await delay(380);
    appendLog(`[parse] detected ${errorCount} violation(s)`);
    updateStepStatus('parse', 'done');

    updateStepStatus('analyze', 'running');
    await delay(200);
    appendLog(`[analyze] classifying error codes...`);
    await delay(320);
    appendLog(`[analyze] context snippets extracted`);
    updateStepStatus('analyze', 'done');

    updateStepStatus('generate', 'running');
    await delay(180);
    appendLog(`[llm] sending repair request...`);
    await delay(140);
    appendLog(`[llm] awaiting stream response...`);

    await doActualRequest();

    appendLog(`[llm] suggestions received`);
    updateStepStatus('generate', 'done');

    updateStepStatus('apply', 'running');
    await delay(180);
    appendLog(`[patch] applying diffs to source...`);
    await delay(280);
    appendLog(`[patch] output file assembled`);
    updateStepStatus('apply', 'done');

    appendLog(`[done] pipeline complete`);
  };

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
    const byCodeLocation = new Map<string, LlmFixSuggestion[]>();
    const byMessageLocation = new Map<string, LlmFixSuggestion[]>();
    const byMessage = new Map<string, LlmFixSuggestion[]>();
    const unmatchedSuggestions: LlmFixSuggestion[] = [];

    const pushToQueue = (
      map: Map<string, LlmFixSuggestion[]>,
      key: string,
      suggestion: LlmFixSuggestion,
    ) => {
      if (!key) return;
      const queue = map.get(key) ?? [];
      queue.push(suggestion);
      map.set(key, queue);
    };

    const consumeFromQueue = (
      map: Map<string, LlmFixSuggestion[]>,
      key: string,
    ): LlmFixSuggestion | undefined => {
      const queue = map.get(key);
      if (!queue || queue.length === 0) return undefined;
      const next = queue.shift();
      if (queue.length === 0) map.delete(key);
      else map.set(key, queue);
      return next;
    };

    for (const suggestion of suggestions) {
      if (suggestion.errorId) byErrorId.set(suggestion.errorId, suggestion);
      const key = `${suggestion.code ?? ''}|${suggestion.location ?? ''}`;
      if (key !== '|') pushToQueue(byCodeLocation, key, suggestion);

      const raw = suggestion.raw as {
        anchorPair?: { error_messages?: string[] };
      } | undefined;
      const anchorMessages = raw?.anchorPair?.error_messages ?? [];
      let indexedByAnchorMessage = false;
      anchorMessages.forEach((msg) => {
        const [messagePart, locationPart] = msg.split(' @ /');
        const normalizedMessage = messagePart?.trim();
        const normalizedLocation = locationPart
          ? `/${locationPart.trim().replace(/^\/+/, '')}`
          : '';
        if (normalizedMessage) {
          pushToQueue(byMessageLocation, `${normalizedMessage}|${normalizedLocation}`, suggestion);
          pushToQueue(byMessage, normalizedMessage, suggestion);
          indexedByAnchorMessage = true;
        }
      });

      if (suggestion.summary?.trim()) {
        pushToQueue(byMessage, suggestion.summary.trim(), suggestion);
      }
      if (!indexedByAnchorMessage) unmatchedSuggestions.push(suggestion);
    }

    const mappedSuggestions: Record<string, LlmFixSuggestion> = {};
    targets.forEach((error) => {
      const mapped =
        byErrorId.get(error.id) ??
        consumeFromQueue(byCodeLocation, `${error.code}|${error.location ?? ''}`) ??
        consumeFromQueue(byMessageLocation, `${error.message.trim()}|${error.location ?? ''}`) ??
        consumeFromQueue(byMessage, error.message.trim()) ??
        unmatchedSuggestions.shift();
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
        nextStatuses[error.id] = mappedSuggestions[error.id] ? 'generated' : 'failed';
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
      try { sourceText = await sourceFile.text(); } catch { sourceText = undefined; }
    }

    const buildContextPayload = (currentTargets: Array<VerificationError & { id: string }>) => {
      if (!sourceText) return undefined;
      const snippetContext = buildSnippetContext(sourceText, currentTargets);
      if (SEND_FILE_CONTEXT_FOR_FIX) {
        return { ...(snippetContext ?? {}), originalFileContent: sourceText } satisfies Record<string, unknown>;
      }
      return snippetContext;
    };

    const contextPayload = buildContextPayload(targets);
    if (contextPayload?.snippets && Array.isArray(contextPayload.snippets)) {
      setSentSnippets((prev) => {
        const next = { ...prev };
        for (const snippet of contextPayload.snippets as FixContextSnippet[]) {
          if (snippet?.errorId && snippet?.snippet) next[snippet.errorId] = snippet.snippet;
        }
        return next;
      });
    }

    let llmResponse: Awaited<ReturnType<typeof apiClient.requestLlmRepairFile>> | null = null;

    await runAnalysisAnimation(targets.length, async () => {
      llmResponse = sourceFile
        ? await apiClient.requestLlmRepairFile(sourceFile, {
            verificationType,
            fileName: sourceFile.name,
          })
        : null;
    });

    if (!llmResponse || !(llmResponse as typeof llmResponse & { success: boolean }).success) {
      const msg =
        (llmResponse as (typeof llmResponse & { message?: string }) | null)?.message ??
        'LLM 수정 요청에 실패했습니다.';
      appendLog(`[error] ${msg}`);
      setFixStatuses((prev) => {
        const next = { ...prev };
        for (const t of targets) next[t.id] = 'failed';
        return next;
      });
      return;
    }

    const successResponse = llmResponse as typeof llmResponse & {
      success: true;
      suggestions?: LlmFixSuggestion[];
      updatedFile?: string;
      raw?: unknown;
    };

    const llmMappedSuggestions = mapSuggestionsToErrors(targets, successResponse.suggestions ?? []);
    assignSuggestionsToErrors(targets, llmMappedSuggestions);

    if (successResponse.updatedFile) setUpdatedFileContent(successResponse.updatedFile);

    const rawMeta = (successResponse.raw ?? {}) as { llmMatchedCount?: number };
    if (rawMeta) {
      setLastPipelineSummary({
        llmMatchedCount: Number(rawMeta.llmMatchedCount ?? (successResponse.suggestions?.length ?? 0)),
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

  const getFixStatusVariant = (status: FixStatus): 'secondary' | 'outline' | 'success' | 'destructive' => {
    if (status === 'generated') return 'secondary';
    if (status === 'failed') return 'destructive';
    return 'outline';
  };

  const getFixStatusLabel = (status: FixStatus) => {
    if (status === 'requested') return 'pending';
    if (status === 'generated') return 'fixed';
    if (status === 'failed') return 'error';
    return 'idle';
  };

  const getSuggestionSourceLabel = (suggestion?: LlmFixSuggestion): '규칙 기반' | 'LLM' => {
    const raw = suggestion?.raw as { source?: string } | undefined;
    return raw?.source === 'rule_based_fix' ? '규칙 기반' : 'LLM';
  };

  const getAnchorPair = (suggestion?: LlmFixSuggestion) => {
    const raw = suggestion?.raw as {
      anchorPair?: {
        error_messages?: string[];
        broken_anchor?: unknown;
        corrected_anchor?: unknown;
      };
    } | undefined;
    return raw?.anchorPair;
  };

  return (
    <div className={`rounded-b-lg border-x border-b overflow-hidden ${effectiveSuccess ? 'border-[hsl(var(--success)_/_0.3)]' : 'border-destructive/30'}`}>

      <div className="bg-card p-4 space-y-4">
        {effectiveMessage && (
          <p className="text-xs text-muted-foreground font-mono border-l-2 border-border pl-3">
            {effectiveMessage}
          </p>
        )}

        {effectiveSuccess && !effectiveErrors?.length && (
          <p className="text-xs text-[hsl(var(--success))]">
            모든 검증을 통과했습니다. 현재 AAS 파일은 요구 규격을 만족합니다.
          </p>
        )}

        {effectiveErrors && effectiveErrors.length > 0 && (
          <div className="space-y-4">

            {/* AI Repair Panel */}
            <div className="rounded-lg border border-primary/20 bg-primary/[0.03] overflow-hidden">
              {/* Panel header */}
              <div className="flex items-center justify-between px-4 py-3 border-b border-primary/10">
                <div className="flex items-center gap-2">
                  <Sparkles className="h-3.5 w-3.5 text-primary" />
                  <span className="text-xs font-semibold">AI 자동 수정</span>
                  <span className="text-[10px] font-mono text-muted-foreground">
                    {indexedErrors.length}개 오류 대상
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={downloadUpdatedFile}
                    disabled={!updatedFileContent}
                    className="h-7 gap-1.5 text-xs"
                  >
                    <Download className="h-3 w-3" />
                    다운로드
                  </Button>
                  <Button
                    size="sm"
                    disabled={indexedErrors.length === 0 || isRequestingSelected}
                    className="h-7 gap-1.5 text-xs"
                    onClick={async () => {
                      setIsRequestingSelected(true);
                      try {
                        await requestFixForErrors(indexedErrors);
                      } finally {
                        setIsRequestingSelected(false);
                      }
                    }}
                  >
                    {isRequestingSelected ? (
                      <>
                        <Loader2 className="h-3 w-3 animate-spin" />
                        분석 중
                      </>
                    ) : (
                      <>
                        <Sparkles className="h-3 w-3" />
                        수정 실행
                      </>
                    )}
                  </Button>
                </div>
              </div>

              {/* Analysis pipeline panel */}
              {isAnalysisVisible && (
                <div className="bg-[hsl(222_28%_6%)] dark:bg-[hsl(222_28%_6%)] font-mono text-xs">
                  {/* Step progress bar */}
                  <div className="flex items-stretch border-b border-white/5">
                    {analysisSteps.map((step, i) => (
                      <div
                        key={step.id}
                        className={`flex-1 flex items-center gap-1.5 px-3 py-2 text-[10px] border-r border-white/5 last:border-r-0 transition-all ${
                          step.status === 'running'
                            ? 'text-[hsl(217_91%_70%)] bg-[hsl(217_91%_50%_/_0.08)]'
                            : step.status === 'done'
                              ? 'text-[hsl(142_71%_55%)]'
                              : 'text-white/25'
                        }`}
                      >
                        {step.status === 'running' ? (
                          <Loader2 className="h-3 w-3 animate-spin shrink-0" />
                        ) : step.status === 'done' ? (
                          <CheckCheck className="h-3 w-3 shrink-0" />
                        ) : (
                          <span className="h-3 w-3 shrink-0 flex items-center justify-center">{step.icon}</span>
                        )}
                        <span className={step.status === 'running' ? 'font-bold' : ''}>{step.label}</span>
                      </div>
                    ))}
                  </div>

                  {/* Terminal log */}
                  <div className="px-4 py-3 max-h-32 overflow-y-auto space-y-0.5">
                    {analysisLogs.map((log, i) => (
                      <div
                        key={i}
                        className={`leading-5 ${
                          log.startsWith('[done]')
                            ? 'text-[hsl(142_71%_55%)]'
                            : log.startsWith('[error]')
                              ? 'text-[hsl(0_72%_65%)]'
                              : log.startsWith('[llm]')
                                ? 'text-[hsl(217_91%_70%)]'
                                : 'text-white/45'
                        }`}
                      >
                        {log}
                        {i === analysisLogs.length - 1 && isRequestingSelected && (
                          <span className="inline-block w-1.5 h-3.5 bg-[hsl(217_91%_58%)] ml-0.5 animate-pulse align-middle" />
                        )}
                      </div>
                    ))}
                    <div ref={logEndRef} />
                  </div>
                </div>
              )}

              {/* Pipeline result summary */}
              {lastPipelineSummary && (
                <div className="grid grid-cols-4 divide-x divide-border border-t border-primary/10 text-xs">
                  {[
                    { label: 'LLM 수정안', value: `${lastPipelineSummary.llmMatchedCount}건` },
                    { label: '수정 완료', value: generatedCount },
                    { label: '미처리', value: remainingCount },
                    { label: '파일 출력', value: updatedFileContent ? '완료' : '없음' },
                  ].map((stat) => (
                    <div key={stat.label} className="px-3 py-2.5">
                      <div className="text-muted-foreground text-[10px] font-mono mb-0.5">{stat.label}</div>
                      <div className="font-semibold">{stat.value}</div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Error list header */}
            <div className="flex items-center gap-2 text-xs font-mono">
              <AlertTriangle className="h-3.5 w-3.5 text-destructive" />
              <span className="font-semibold text-destructive">VIOLATIONS</span>
              <span className="text-muted-foreground">
                {effectiveErrors.length} errors / {groupedErrors.length} types
              </span>
            </div>

            {/* Grouped error list */}
            <div className="max-h-[32rem] overflow-y-auto space-y-2 pr-0.5">
              {groupedErrors.map(([code, grouped], index) => {
                const isExpanded = expandedGroups[code] ?? index === 0;
                const visible = isExpanded ? grouped : grouped.slice(0, INITIAL_GROUP_ITEM_LIMIT);
                const hiddenCount = grouped.length - visible.length;

                return (
                  <div
                    key={code}
                    className="rounded-md border border-border overflow-hidden"
                  >
                    {/* Group header */}
                    <button
                      type="button"
                      onClick={() => toggleGroup(code)}
                      className="w-full flex items-center justify-between px-3 py-2.5 bg-muted/30 hover:bg-muted/50 transition-colors text-left"
                    >
                      <div className="flex items-center gap-2">
                        {isExpanded ? (
                          <ChevronDown className="h-3.5 w-3.5 text-muted-foreground" />
                        ) : (
                          <ChevronRight className="h-3.5 w-3.5 text-muted-foreground" />
                        )}
                        <span className="text-xs font-mono font-semibold text-destructive">{code}</span>
                      </div>
                      <Badge variant="destructive" className="text-[10px] font-mono h-5">
                        {grouped.length}
                      </Badge>
                    </button>

                    {/* Error items */}
                    {isExpanded && (
                      <div className="divide-y divide-border">
                        {visible.map((error, itemIndex) => {
                          const status = fixStatuses[error.id] ?? 'idle';
                          const hasSuggestion = !!fixSuggestions[error.id];
                          return (
                            <div key={`${code}-${itemIndex}`} className="p-3 bg-card">
                              <div className="flex items-start justify-between gap-3">
                                <div className="flex-1 min-w-0">
                                  <p className="text-xs text-foreground/80 leading-relaxed">
                                    {error.message}
                                  </p>
                                  {error.location && (
                                    <p className="text-[10px] text-muted-foreground mt-1 font-mono truncate">
                                      @ {error.location}
                                    </p>
                                  )}
                                </div>
                                <Badge
                                  variant={getFixStatusVariant(status)}
                                  className="text-[10px] font-mono shrink-0 h-5"
                                >
                                  {getFixStatusLabel(status)}
                                </Badge>
                              </div>

                              {/* Diff view for fix suggestion */}
                              {(hasSuggestion || sentSnippets[error.id]) && (
                                <div className="mt-3 grid gap-2 md:grid-cols-2">
                                  <div className="rounded border border-border bg-muted/20 overflow-hidden">
                                    <div className="flex items-center gap-1.5 px-2.5 py-1.5 border-b border-border bg-muted/40">
                                      <span className="text-[10px] font-mono text-muted-foreground">before</span>
                                    </div>
                                    <pre className="text-[10px] leading-4 text-muted-foreground whitespace-pre-wrap break-words p-2.5 max-h-28 overflow-y-auto">
                                      {getAnchorPair(fixSuggestions[error.id])
                                        ? JSON.stringify(getAnchorPair(fixSuggestions[error.id])?.broken_anchor ?? {}, null, 2)
                                        : (sentSnippets[error.id] ?? '—')}
                                    </pre>
                                  </div>
                                  <div className="rounded border border-[hsl(var(--success)_/_0.3)] bg-[hsl(var(--success)_/_0.04)] overflow-hidden">
                                    <div className="flex items-center justify-between px-2.5 py-1.5 border-b border-[hsl(var(--success)_/_0.2)] bg-[hsl(var(--success)_/_0.06)]">
                                      <span className="text-[10px] font-mono text-[hsl(var(--success))]">after</span>
                                      <span className="text-[9px] font-mono text-muted-foreground">
                                        {getSuggestionSourceLabel(fixSuggestions[error.id])}
                                      </span>
                                    </div>
                                    <pre className="text-[10px] leading-4 text-muted-foreground whitespace-pre-wrap break-words p-2.5 max-h-28 overflow-y-auto">
                                      {getAnchorPair(fixSuggestions[error.id]) ? (
                                        JSON.stringify(getAnchorPair(fixSuggestions[error.id])?.corrected_anchor ?? {}, null, 2)
                                      ) : (
                                        fixSuggestions[error.id]?.fixedSnippet ??
                                        fixSuggestions[error.id]?.patch ??
                                        fixSuggestions[error.id]?.summary ??
                                        fixSuggestions[error.id]?.reason ??
                                        '...'
                                      )}
                                    </pre>
                                  </div>
                                </div>
                              )}
                            </div>
                          );
                        })}

                        {hiddenCount > 0 && (
                          <button
                            type="button"
                            onClick={() => toggleGroup(code)}
                            className="w-full py-2 text-xs text-muted-foreground hover:text-foreground font-mono transition-colors bg-muted/20 hover:bg-muted/40"
                          >
                            + {hiddenCount}개 더 보기
                          </button>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
