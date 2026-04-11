'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { BrandLogo } from '@/components/brand-logo';
import { FileUpload } from '@/components/file-upload';
import { VerificationResult } from '@/components/verification-result';
import { AasViewer } from '@/components/aas-viewer';
import { apiClient, type VerificationResult as VerificationResultType } from '@/lib/api-client';
import { useAuth } from '@/lib/auth-context';
import {
  FileCheck,
  Database,
  Layers,
  LogOut,
  Cpu,
  ShieldCheck,
  CheckCircle2,
  Play,
  Zap,
  ChevronDown,
  RotateCcw,
} from 'lucide-react';

type VerificationType = 'metamodel' | 'template' | 'instance';

const VERIFICATION_TYPES: {
  id: VerificationType;
  icon: React.ReactNode;
  label: string;
  description: string;
  tag: string;
}[] = [
  {
    id: 'metamodel',
    icon: <FileCheck className="h-4 w-4" />,
    label: '메타모델',
    description: 'AAS Metamodel v3.0 구조 검증',
    tag: 'METAMODEL',
  },
  {
    id: 'template',
    icon: <Layers className="h-4 w-4" />,
    label: '템플릿',
    description: '필수 필드 및 형식 준수 확인',
    tag: 'TEMPLATE',
  },
  {
    id: 'instance',
    icon: <Database className="h-4 w-4" />,
    label: '인스턴스',
    description: 'Semantic ID 스키마 대조 검사',
    tag: 'INSTANCE',
  },
];

// 파이프라인 스텝 정의 — 단계별 부가 설명 포함
const PIPELINE_STEPS = [
  {
    id: 'upload',
    step: '01',
    label: 'INPUT',
    sublabel: '파일 업로드',
    description: 'AAS JSON 파일을 드래그하거나 샘플을 불러옵니다',
  },
  {
    id: 'verify',
    step: '02',
    label: 'VERIFY',
    sublabel: '규격 검증',
    description: 'AAS Metamodel v3.0 규격 엔진이 구조를 자동 분석합니다',
  },
  {
    id: 'analyze',
    step: '03',
    label: 'ANALYZE',
    sublabel: '오류 분석',
    description: '위반 항목을 유형별로 분류하고 위치를 특정합니다',
  },
  {
    id: 'fix',
    step: '04',
    label: 'AI FIX',
    sublabel: 'LLM 자동 수정',
    description: 'LLM이 AAS 구조를 이해하고 오류를 자동으로 수정합니다',
  },
];

// 실제 데모 파일 목록 (public/demo/ 에 위치)
const DEMO_FILES: { id: string; label: string; filename: string; description: string; type: VerificationType }[] = [
  {
    id: 'ER2',
    label: 'ER2 — LS ELECTRIC 인버터',
    filename: 'ER2.json',
    description: '템플릿 AAS · 29K줄 · 다수 오류 포함',
    type: 'template',
  },
  {
    id: 'ER5',
    label: 'ER5 — 스마트팩토리 템플릿',
    filename: 'ER5.json',
    description: '템플릿 AAS · 다수 구조 오류 포함',
    type: 'template',
  },
];

function getPipelineActiveStep(
  hasFile: boolean,
  isVerifying: boolean,
  hasResult: boolean,
  hasErrors: boolean,
): number {
  if (!hasFile) return 0;
  if (isVerifying) return 1;
  if (hasResult && hasErrors) return 3;
  if (hasResult) return 3;
  return 1;
}

// 파이프라인 커넥터 — active/done 여부에 따라 흐르는 선 or 정적 선
function PipelineConnector({ isDone, isActive }: { isDone: boolean; isActive: boolean }) {
  return (
    <div className="shrink-0 w-10 flex items-center justify-center">
      <svg width="40" height="14" viewBox="0 0 40 14" fill="none">
        {/* Track */}
        <line x1="0" y1="7" x2="32" y2="7"
          stroke={isDone ? 'hsl(142 71% 45% / 0.4)' : isActive ? 'hsl(217 91% 58% / 0.3)' : 'hsl(var(--border))'}
          strokeWidth="1.5"
        />
        {/* Flowing dash overlay */}
        {(isDone || isActive) && (
          <line x1="0" y1="7" x2="32" y2="7"
            stroke={isDone ? 'hsl(142 71% 55%)' : 'hsl(217 91% 65%)'}
            strokeWidth="1.5"
            className={isDone ? 'pipeline-flow-done' : 'pipeline-flow'}
          />
        )}
        {/* Arrow head */}
        <polyline
          points="27,4 33,7 27,10"
          fill="none"
          stroke={isDone ? 'hsl(142 71% 50%)' : isActive ? 'hsl(217 91% 60%)' : 'hsl(var(--border))'}
          strokeWidth="1.5"
          strokeLinejoin="round"
          strokeLinecap="round"
        />
      </svg>
    </div>
  );
}

export default function VerifyPage() {
  const { user, logout } = useAuth();
  const router = useRouter();
  const [selectedType, setSelectedType] = useState<VerificationType>('metamodel');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isVerifying, setIsVerifying] = useState(false);
  const [result, setResult] = useState<VerificationResultType | null>(null);
  const [fileUploadKey, setFileUploadKey] = useState(0);
  const [demoOpen, setDemoOpen] = useState(false);
  const [isDemoLoading, setIsDemoLoading] = useState(false);
  // viewer — holds the JSON string to render (from file read or AI fix)
  const [viewerJson, setViewerJson] = useState<string | null>(null);
  const [viewerTab, setViewerTab] = useState<'errors' | 'viewer'>('errors');

  const handleLogout = () => {
    logout();
    router.push('/');
  };

  const handleFileSelect = (file: File) => {
    setSelectedFile(file);
    setResult(null);
    setViewerJson(null);
    setViewerTab('errors');
  };

  // Called by VerificationResult when AI fix produces updated content
  const handleFixComplete = (updatedJson: string) => {
    setViewerJson(updatedJson);
    setViewerTab('viewer');
  };

  const handleVerify = async () => {
    if (!selectedFile) return;
    setIsVerifying(true);
    setResult(null);
    try {
      let response: VerificationResultType;
      switch (selectedType) {
        case 'metamodel':
          response = await apiClient.verifyMetamodel(selectedFile);
          break;
        case 'template':
          response = await apiClient.verifyTemplate(selectedFile);
          break;
        case 'instance':
          response = await apiClient.verifyInstance(selectedFile);
          break;
      }
      setResult(response);
      if (response.success && selectedFile) {
        try {
          const text = await selectedFile.text();
          setViewerJson(text);
          setViewerTab('viewer');
        } catch { /* ignore read errors */ }
      }
    } catch (error) {
      setResult({
        success: false,
        message: '검증에 실패했습니다. 파일을 확인한 뒤 다시 시도해 주세요.',
        errors: [
          {
            code: 'NETWORK_ERROR',
            message: error instanceof Error ? error.message : '알 수 없는 오류가 발생했습니다.',
          },
        ],
      });
    } finally {
      setIsVerifying(false);
    }
  };

  // 데모 파일 fetch → 업로드 + 즉시 검증
  const handleLoadDemo = async (demo: typeof DEMO_FILES[number]) => {
    setDemoOpen(false);
    setIsDemoLoading(true);
    setResult(null);
    try {
      const res = await fetch(`/demo/${demo.filename}`);
      if (!res.ok) throw new Error('데모 파일을 불러올 수 없습니다.');
      const blob = await res.blob();
      const file = new File([blob], demo.filename, { type: 'application/json' });
      setSelectedFile(file);
      setSelectedType(demo.type);
      setFileUploadKey((k) => k + 1);

      setIsVerifying(true);
      setIsDemoLoading(false);
      let response: VerificationResultType;
      switch (demo.type) {
        case 'metamodel':
          response = await apiClient.verifyMetamodel(file);
          break;
        case 'template':
          response = await apiClient.verifyTemplate(file);
          break;
        case 'instance':
          response = await apiClient.verifyInstance(file);
          break;
      }
      setResult(response);
      if (response.success) {
        try {
          const text = await file.text();
          setViewerJson(text);
          setViewerTab('viewer');
        } catch { /* ignore */ }
      }
    } catch (error) {
      setResult({
        success: false,
        message: '데모 검증 실패',
        errors: [
          {
            code: 'DEMO_ERROR',
            message: error instanceof Error ? error.message : '알 수 없는 오류가 발생했습니다.',
          },
        ],
      });
    } finally {
      setIsVerifying(false);
      setIsDemoLoading(false);
    }
  };

  const hasErrors = result && !result.success && (result.errors?.length ?? 0) > 0;
  const activeStepIndex = getPipelineActiveStep(!!selectedFile, isVerifying, !!result, !!hasErrors);

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Header */}
      <header className="border-b border-border bg-card/95 backdrop-blur-sm sticky top-0 z-20">
        <div className="max-w-screen-xl mx-auto px-6 h-14 flex items-center justify-between gap-4">
          {/* Left — brand + tagline */}
          <div className="flex items-center gap-4 min-w-0">
            <Link href="/" className="shrink-0">
              <BrandLogo
                title="ezAASVerify"
                imageClassName="h-6 w-auto"
                titleClassName="text-sm font-bold tracking-tight logo-shimmer"
              />
            </Link>
            {/* divider */}
            <span className="hidden md:block h-4 w-px bg-border" />
            <div className="hidden md:flex items-center gap-1.5">
              <ShieldCheck className="h-3 w-3 text-primary shrink-0 icon-scan" />
              <span className="text-[11px] font-mono text-muted-foreground whitespace-nowrap">
                AAS Verification &amp; LLM Repair Engine
              </span>
            </div>
          </div>

          {/* Right — nav */}
          <nav className="flex items-center gap-1 shrink-0">
            {user?.role === 'admin' && (
              <Link href="/admin">
                <Button variant="ghost" size="sm" className="text-xs text-muted-foreground hover:text-foreground h-8">
                  관리자
                </Button>
              </Link>
            )}
            {user ? (
              <Button
                variant="ghost"
                size="sm"
                onClick={handleLogout}
                className="gap-1.5 text-xs text-muted-foreground hover:text-foreground h-8"
              >
                <LogOut className="h-3.5 w-3.5" />
                로그아웃
              </Button>
            ) : (
              <Link href="/login">
                <Button size="sm" className="text-xs h-8">로그인</Button>
              </Link>
            )}
          </nav>
        </div>
      </header>

      {/* Pipeline bar — full width, sticky below header */}
      <div className="border-b border-border bg-card/90 backdrop-blur-sm sticky top-[52px] z-10">
        <div className="max-w-screen-xl mx-auto px-6">
          <div className="flex items-center h-16">
            {PIPELINE_STEPS.map((node, i) => {
              const isDone = i < activeStepIndex;
              const isActive = i === activeStepIndex;
              const isVerifyingStep = isVerifying && i === 1;

              return (
                <div key={node.id} className="flex items-center min-w-0">
                  {/* Node */}
                  <div
                    className={`relative flex items-center gap-3 px-3 py-2 transition-all ${
                      isActive ? 'text-primary' : isDone ? 'text-[hsl(142_71%_45%)]' : 'text-muted-foreground/40'
                    }`}
                  >
                    {/* Active underline bar */}
                    {isActive && (
                      <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary rounded-full" />
                    )}

                    {/* Step badge */}
                    <div
                      className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-md border text-[10px] font-mono font-bold transition-all ${
                        isActive
                          ? 'bg-primary text-primary-foreground border-primary node-pulse'
                          : isDone
                            ? 'bg-[hsl(142_71%_45%_/_0.12)] text-[hsl(142_71%_45%)] border-[hsl(142_71%_45%_/_0.3)]'
                            : 'bg-muted/40 border-border/50 text-muted-foreground/40'
                      }`}
                    >
                      {isDone ? (
                        <CheckCircle2 className="h-3.5 w-3.5" />
                      ) : isVerifyingStep ? (
                        <Cpu className="h-3.5 w-3.5 animate-pulse" />
                      ) : (
                        <span>{node.step}</span>
                      )}
                    </div>

                    {/* Labels */}
                    <div className="hidden sm:block">
                      <div className={`text-[11px] font-mono font-bold leading-none mb-0.5 ${
                        isActive ? 'text-primary' : isDone ? 'text-[hsl(142_71%_45%)]' : ''
                      }`}>
                        {node.label}
                      </div>
                      <div className="text-[10px] text-muted-foreground leading-none">
                        {node.sublabel}
                      </div>
                    </div>

                    {/* Active step description — tooltip-like tag */}
                    {isActive && (
                      <div className="hidden lg:flex items-center ml-1 px-2 py-0.5 rounded bg-primary/10 border border-primary/20">
                        <span className="text-[10px] text-primary/80 leading-none whitespace-nowrap">
                          {node.description}
                        </span>
                      </div>
                    )}
                  </div>

                  {/* Animated connector */}
                  {i < PIPELINE_STEPS.length - 1 && (
                    <PipelineConnector isDone={isDone} isActive={isActive} />
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Main content */}
      <main className="flex-1 max-w-screen-xl mx-auto w-full px-6 py-6">
        <div className={`grid gap-6 transition-all duration-300 ${result ? 'lg:grid-cols-[400px_1fr]' : 'max-w-xl mx-auto'}`}>

          {/* LEFT COLUMN — Controls */}
          <div className="space-y-4">
            <div className="flex items-start justify-between">
              <div>
                <h1 className="text-lg font-semibold tracking-tight">AAS 파일 검증</h1>
                <p className="text-xs text-muted-foreground mt-0.5">
                  JSON 파일을 업로드하고 규격 적합성을 검사합니다
                </p>
              </div>
              {/* Demo dropdown */}
              <div className="relative shrink-0">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setDemoOpen((o) => !o)}
                  disabled={isVerifying || isDemoLoading}
                  className="gap-1.5 text-xs border-primary/30 text-primary hover:bg-primary/5"
                >
                  {isDemoLoading ? (
                    <Cpu className="h-3.5 w-3.5 animate-pulse" />
                  ) : (
                    <Zap className="h-3.5 w-3.5" />
                  )}
                  데모 실행
                  <ChevronDown className={`h-3 w-3 transition-transform ${demoOpen ? 'rotate-180' : ''}`} />
                </Button>
                {demoOpen && (
                  <div className="absolute right-0 top-full mt-1 z-30 w-64 rounded-md border border-border bg-card shadow-lg overflow-hidden">
                    <div className="px-3 py-1.5 border-b border-border bg-muted/30">
                      <span className="text-[9px] font-mono font-semibold text-muted-foreground uppercase tracking-widest">
                        데모 파일 선택
                      </span>
                    </div>
                    {DEMO_FILES.map((demo) => (
                      <button
                        key={demo.id}
                        onClick={() => handleLoadDemo(demo)}
                        className="w-full text-left px-3 py-2.5 hover:bg-muted/40 transition-colors border-b border-border/50 last:border-b-0"
                      >
                        <div className="text-xs font-semibold text-foreground">{demo.label}</div>
                        <div className="text-[10px] text-muted-foreground mt-0.5 font-mono">{demo.description}</div>
                      </button>
                    ))}
                  </div>
                )}
                {/* Backdrop to close */}
                {demoOpen && (
                  <div
                    className="fixed inset-0 z-20"
                    onClick={() => setDemoOpen(false)}
                  />
                )}
              </div>
            </div>

            {/* Verification type */}
            <div className="space-y-2">
              <label className="text-[10px] font-mono font-semibold text-muted-foreground uppercase tracking-widest">
                검증 유형
              </label>
              <div className="grid grid-cols-3 gap-2">
                {VERIFICATION_TYPES.map((vt) => (
                  <button
                    key={vt.id}
                    onClick={() => { setSelectedType(vt.id); setResult(null); }}
                    className={`relative p-3 rounded-lg border text-left transition-all overflow-hidden ${
                      selectedType === vt.id
                        ? 'border-primary bg-primary/5 shadow-sm'
                        : 'border-border bg-card hover:border-primary/40 hover:bg-muted/20'
                    }`}
                  >
                    {/* Active indicator — left border accent via pseudo element */}
                    {selectedType === vt.id && (
                      <span className="absolute left-0 top-0 bottom-0 w-0.5 bg-primary rounded-l-lg" />
                    )}
                    <div className={`mb-1.5 ${selectedType === vt.id ? 'text-primary' : 'text-muted-foreground'}`}>
                      {vt.icon}
                    </div>
                    <div className="text-xs font-semibold leading-none mb-1">{vt.label}</div>
                    <div className="text-[10px] text-muted-foreground leading-relaxed">{vt.description}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* File upload */}
            <div className="bg-card border border-border rounded-lg overflow-hidden">
              <div className="px-4 py-2.5 border-b border-border bg-muted/20 flex items-center justify-between">
                <span className="text-[10px] font-mono font-semibold text-muted-foreground uppercase tracking-widest">
                  파일 업로드
                </span>
                <span className="text-[10px] font-mono text-muted-foreground/60">STEP 01</span>
              </div>
              <div className="p-4 space-y-3">
                <FileUpload key={fileUploadKey} onFileSelect={handleFileSelect} />
                <Button
                  onClick={handleVerify}
                  disabled={!selectedFile || isVerifying}
                  className="w-full gap-2"
                >
                  {isVerifying ? (
                    <>
                      <Cpu className="h-4 w-4 animate-pulse" />
                      검증 실행 중...
                    </>
                  ) : (
                    <>
                      <Play className="h-3.5 w-3.5" />
                      검증 실행
                    </>
                  )}
                </Button>
              </div>
            </div>

            {/* Pipeline step guide — shows which step is active */}
            <div className="rounded-lg border border-border bg-card overflow-hidden">
              <div className="px-4 py-2.5 border-b border-border bg-muted/20">
                <span className="text-[10px] font-mono font-semibold text-muted-foreground uppercase tracking-widest">
                  파이프라인
                </span>
              </div>
              <div className="divide-y divide-border">
                {PIPELINE_STEPS.map((step, i) => {
                  const isDone = i < activeStepIndex;
                  const isActive = i === activeStepIndex;
                  return (
                    <div
                      key={step.id}
                      className={`flex items-start gap-3 px-4 py-3 transition-colors ${
                        isActive ? 'bg-primary/5' : isDone ? 'bg-[hsl(142_71%_45%_/_0.03)]' : ''
                      }`}
                    >
                      <div className={`flex h-5 w-5 shrink-0 items-center justify-center rounded text-[9px] font-mono font-bold mt-0.5 ${
                        isActive
                          ? 'bg-primary text-primary-foreground'
                          : isDone
                            ? 'bg-[hsl(142_71%_45%_/_0.15)] text-[hsl(142_71%_45%)]'
                            : 'bg-muted text-muted-foreground/50'
                      }`}>
                        {isDone ? '✓' : step.step}
                      </div>
                      <div className="min-w-0">
                        <div className={`text-[11px] font-mono font-semibold leading-none mb-0.5 ${
                          isActive ? 'text-primary' : isDone ? 'text-[hsl(142_71%_45%)]' : 'text-muted-foreground/50'
                        }`}>
                          {step.label}
                          <span className="ml-1 font-normal text-[10px]">— {step.sublabel}</span>
                        </div>
                        <div className={`text-[10px] leading-relaxed ${
                          isActive ? 'text-foreground/70' : 'text-muted-foreground/50'
                        }`}>
                          {step.description}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* RIGHT COLUMN — Result */}
          {result && (
            <div className="min-w-0 fade-up">
              {/* Result status banner + tabs */}
              <div
                className={`rounded-t-lg border-x border-t overflow-hidden ${
                  result.success
                    ? 'border-[hsl(142_71%_45%_/_0.3)]'
                    : 'border-destructive/30'
                }`}
              >
                {/* Status row */}
                <div className={`flex items-center gap-3 px-4 py-3 font-mono text-xs ${
                  result.success
                    ? 'bg-[hsl(142_71%_45%_/_0.06)] text-[hsl(142_71%_45%)]'
                    : 'bg-destructive/5 text-destructive'
                }`}>
                  <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold border ${
                    result.success
                      ? 'bg-[hsl(142_71%_45%_/_0.15)] border-[hsl(142_71%_45%_/_0.4)] text-[hsl(142_71%_45%)]'
                      : 'bg-destructive/15 border-destructive/40 text-destructive'
                  }`}>
                    {result.success ? 'PASS' : 'FAIL'}
                  </span>
                  <span className="text-muted-foreground">
                    {result.success
                      ? '모든 규격 검사를 통과했습니다 — 완성된 모델을 아래에서 확인하세요'
                      : `${result.errors?.length ?? 0}개의 위반 항목이 발견됐습니다 — AI가 자동 수정할 수 있습니다`}
                  </span>
                  {selectedFile && (
                    <span className="text-muted-foreground/60 truncate max-w-[140px] font-mono">
                      {selectedFile.name}
                    </span>
                  )}
                  <button
                    onClick={() => {
                      setResult(null);
                      setSelectedFile(null);
                      setViewerJson(null);
                      setViewerTab('errors');
                      setFileUploadKey((k) => k + 1);
                    }}
                    className="ml-auto shrink-0 flex items-center gap-1 text-[10px] font-mono text-muted-foreground hover:text-foreground border border-border/60 hover:border-border rounded px-2 py-1 transition-colors bg-background/50 hover:bg-muted/40"
                  >
                    <RotateCcw className="h-3 w-3" />
                    새 파일 검증
                  </button>
                </div>

                {/* Tabs — only show when viewer data is available */}
                {viewerJson && (
                  <div className={`flex border-t ${
                    result.success ? 'border-[hsl(142_71%_45%_/_0.2)] bg-[hsl(142_71%_45%_/_0.03)]' : 'border-destructive/20 bg-destructive/[0.02]'
                  }`}>
                    {result.success ? null : (
                      <button
                        onClick={() => setViewerTab('errors')}
                        className={`px-4 py-2 text-[11px] font-mono font-semibold transition-colors border-b-2 ${
                          viewerTab === 'errors'
                            ? 'border-destructive text-destructive'
                            : 'border-transparent text-muted-foreground hover:text-foreground'
                        }`}
                      >
                        오류 목록
                      </button>
                    )}
                    <button
                      onClick={() => setViewerTab('viewer')}
                      className={`px-4 py-2 text-[11px] font-mono font-semibold transition-colors border-b-2 flex items-center gap-1.5 ${
                        viewerTab === 'viewer'
                          ? result.success
                            ? 'border-[hsl(142_71%_45%)] text-[hsl(142_71%_45%)]'
                            : 'border-primary text-primary'
                          : 'border-transparent text-muted-foreground hover:text-foreground'
                      }`}
                    >
                      <CheckCircle2 className="h-3 w-3" />
                      모델 뷰어
                    </button>
                    {!result.success && (
                      <button
                        onClick={() => setViewerTab('errors')}
                        className={`px-4 py-2 text-[11px] font-mono font-semibold transition-colors border-b-2 ${
                          viewerTab === 'errors'
                            ? 'border-destructive text-destructive'
                            : 'border-transparent text-muted-foreground hover:text-foreground'
                        }`}
                      >
                        오류 목록
                      </button>
                    )}
                  </div>
                )}
              </div>

              {/* Tab content */}
              {viewerJson && viewerTab === 'viewer' ? (
                <AasViewer jsonContent={viewerJson} />
              ) : (
                <VerificationResult
                  success={result.success}
                  message={result.message}
                  errors={result.errors}
                  verificationType={selectedType}
                  fileName={selectedFile?.name}
                  sourceFile={selectedFile}
                  onFixComplete={handleFixComplete}
                />
              )}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
