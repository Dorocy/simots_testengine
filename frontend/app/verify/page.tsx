'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { BrandLogo } from '@/components/brand-logo';
import { FileUpload } from '@/components/file-upload';
import { VerificationResult } from '@/components/verification-result';
import { apiClient, type VerificationResult as VerificationResultType } from '@/lib/api-client';
import { useAuth } from '@/lib/auth-context';
import {
  FileCheck,
  Database,
  Layers,
  LogOut,
  ArrowRight,
  Cpu,
  ShieldCheck,
  CheckCircle2,
  Circle,
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

// 파이프라인 스텝 정의
const PIPELINE_STEPS = [
  { id: 'upload', step: '01', label: 'INPUT', sublabel: '파일 업로드' },
  { id: 'verify', step: '02', label: 'VERIFY', sublabel: '규격 검증' },
  { id: 'analyze', step: '03', label: 'ANALYZE', sublabel: '오류 분석' },
  { id: 'fix', step: '04', label: 'AI FIX', sublabel: 'LLM 자동 수정' },
];

function getPipelineActiveStep(hasFile: boolean, isVerifying: boolean, hasResult: boolean): number {
  if (!hasFile) return 0;
  if (isVerifying) return 1;
  if (hasResult) return 2;
  return 1;
}

export default function VerifyPage() {
  const { user, logout } = useAuth();
  const router = useRouter();
  const [selectedType, setSelectedType] = useState<VerificationType>('metamodel');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isVerifying, setIsVerifying] = useState(false);
  const [result, setResult] = useState<VerificationResultType | null>(null);

  const handleLogout = () => {
    logout();
    router.push('/');
  };

  const handleFileSelect = (file: File) => {
    setSelectedFile(file);
    setResult(null);
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

  const activeStepIndex = getPipelineActiveStep(!!selectedFile, isVerifying, !!result);
  const hasErrors = result && !result.success && (result.errors?.length ?? 0) > 0;

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Header */}
      <header className="border-b border-border bg-card sticky top-0 z-20">
        <div className="max-w-screen-xl mx-auto px-6 h-13 flex items-center justify-between">
          <div className="flex items-center gap-6">
            <Link href="/">
              <BrandLogo
                title="ezAAS Verify"
                imageClassName="h-7 w-auto"
                titleClassName="text-base font-semibold tracking-tight"
              />
            </Link>
            <div className="hidden md:flex items-center gap-1 text-[11px] font-mono text-muted-foreground">
              <ShieldCheck className="h-3 w-3 text-primary" />
              <span>AAS VERIFICATION ENGINE</span>
            </div>
          </div>
          <nav className="flex items-center gap-1">
            <Link href="/verify">
              <Button variant="ghost" size="sm" className="text-xs font-medium text-primary">
                검증
              </Button>
            </Link>
            {user?.role === 'admin' && (
              <Link href="/admin">
                <Button variant="ghost" size="sm" className="text-xs font-medium">
                  관리자
                </Button>
              </Link>
            )}
            {user ? (
              <Button variant="outline" size="sm" onClick={handleLogout} className="gap-1.5 text-xs ml-2">
                <LogOut className="h-3.5 w-3.5" />
                로그아웃
              </Button>
            ) : (
              <Link href="/login">
                <Button size="sm" className="text-xs ml-2">로그인</Button>
              </Link>
            )}
          </nav>
        </div>
      </header>

      {/* Pipeline bar — full width, sticky below header */}
      <div className="border-b border-border bg-card/80 backdrop-blur-sm sticky top-[52px] z-10">
        <div className="max-w-screen-xl mx-auto px-6">
          <div className="flex items-stretch h-14">
            {PIPELINE_STEPS.map((node, i) => {
              const isDone = i < activeStepIndex;
              const isActive = i === activeStepIndex;
              const isVerifyingStep = isVerifying && i === 1;
              return (
                <div key={node.id} className="flex items-center flex-1 min-w-0">
                  {/* Node */}
                  <div
                    className={`flex-1 flex items-center gap-2.5 px-4 h-full transition-all relative ${
                      isActive
                        ? 'text-primary'
                        : isDone
                          ? 'text-[hsl(var(--success))]'
                          : 'text-muted-foreground/40'
                    }`}
                  >
                    {/* Active underline */}
                    {isActive && (
                      <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary" />
                    )}
                    {isDone && (
                      <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-[hsl(var(--success)_/_0.4)]" />
                    )}

                    {/* Step indicator */}
                    <div
                      className={`flex h-7 w-7 shrink-0 items-center justify-center rounded border text-[10px] font-mono font-bold transition-all ${
                        isActive
                          ? 'bg-primary text-primary-foreground border-primary'
                          : isDone
                            ? 'bg-[hsl(var(--success)_/_0.1)] text-[hsl(var(--success))] border-[hsl(var(--success)_/_0.3)]'
                            : 'bg-muted/30 border-border'
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

                    {/* Label */}
                    <div className="hidden sm:block min-w-0">
                      <div className={`text-xs font-semibold font-mono leading-none mb-0.5 ${isActive ? 'text-primary' : ''}`}>
                        {node.label}
                      </div>
                      <div className="text-[10px] text-muted-foreground truncate">{node.sublabel}</div>
                    </div>
                  </div>

                  {/* Connector */}
                  {i < PIPELINE_STEPS.length - 1 && (
                    <div className="shrink-0 px-1">
                      <svg width="20" height="10" viewBox="0 0 20 10" fill="none">
                        <line
                          x1="0" y1="5" x2="16" y2="5"
                          stroke={isDone ? 'hsl(var(--success) / 0.5)' : 'hsl(var(--border))'}
                          strokeWidth="1.5"
                          strokeDasharray={isDone ? '3 2' : 'none'}
                        />
                        <polyline
                          points="12,2 17,5 12,8"
                          fill="none"
                          stroke={isDone ? 'hsl(var(--success) / 0.5)' : 'hsl(var(--border))'}
                          strokeWidth="1.5"
                          strokeLinejoin="round"
                          strokeLinecap="round"
                        />
                      </svg>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Main content — full width, two-column when result is present */}
      <main className="flex-1 max-w-screen-xl mx-auto w-full px-6 py-6">
        <div className={`grid gap-6 transition-all ${result ? 'lg:grid-cols-[420px_1fr]' : 'max-w-2xl'}`}>

          {/* LEFT COLUMN — Controls */}
          <div className="space-y-4">
            {/* Heading */}
            <div>
              <h1 className="text-xl font-semibold tracking-tight">AAS 파일 검증</h1>
              <p className="text-xs text-muted-foreground mt-0.5">
                JSON 파일을 업로드하고 규격 적합성을 검사합니다
              </p>
            </div>

            {/* Verification type */}
            <div className="space-y-2">
              <label className="text-[11px] font-mono font-semibold text-muted-foreground uppercase tracking-wide">
                검증 유형
              </label>
              <div className="grid grid-cols-3 gap-2">
                {VERIFICATION_TYPES.map((vt) => (
                  <button
                    key={vt.id}
                    onClick={() => { setSelectedType(vt.id); setResult(null); }}
                    className={`relative p-3 rounded-lg border text-left transition-all group ${
                      selectedType === vt.id
                        ? 'border-primary bg-primary/5 shadow-sm'
                        : 'border-border bg-card hover:border-primary/40 hover:bg-muted/30'
                    }`}
                  >
                    {selectedType === vt.id && (
                      <div className="absolute top-0 left-0 right-0 h-0.5 bg-primary rounded-t-lg" />
                    )}
                    <div className={`mb-2 ${selectedType === vt.id ? 'text-primary' : 'text-muted-foreground'}`}>
                      {vt.icon}
                    </div>
                    <div className="text-xs font-semibold leading-none mb-1">{vt.label}</div>
                    <div className="text-[10px] text-muted-foreground leading-relaxed">{vt.description}</div>
                    {selectedType === vt.id && (
                      <div className="mt-1.5 font-mono text-[9px] text-primary/70">
                        mode: {vt.tag.toLowerCase()}
                      </div>
                    )}
                  </button>
                ))}
              </div>
            </div>

            {/* File upload + verify */}
            <div className="bg-card border border-border rounded-lg overflow-hidden">
              <div className="px-4 py-3 border-b border-border bg-muted/20">
                <span className="text-[11px] font-mono font-semibold text-muted-foreground uppercase tracking-wide">
                  파일 업로드
                </span>
              </div>
              <div className="p-4 space-y-3">
                <FileUpload onFileSelect={handleFileSelect} />
                <Button
                  onClick={handleVerify}
                  disabled={!selectedFile || isVerifying}
                  className="w-full gap-2"
                  size="default"
                >
                  {isVerifying ? (
                    <>
                      <Cpu className="h-4 w-4 animate-pulse" />
                      검증 실행 중...
                    </>
                  ) : (
                    <>
                      <ArrowRight className="h-4 w-4" />
                      검증 실행
                    </>
                  )}
                </Button>
              </div>
            </div>

            {/* Guide box */}
            <div className="rounded-lg border border-border bg-card p-4 space-y-3">
              <div className="text-[11px] font-mono font-semibold text-muted-foreground uppercase tracking-wide">
                파이프라인 안내
              </div>
              <div className="space-y-2.5">
                {[
                  {
                    icon: <Circle className="h-3 w-3 fill-primary text-primary" />,
                    text: 'JSON 파일 업로드 후 검증 유형을 선택합니다',
                  },
                  {
                    icon: <Circle className="h-3 w-3 fill-primary text-primary" />,
                    text: '규격 엔진이 AAS 구조를 자동으로 분석합니다',
                  },
                  {
                    icon: <Circle className="h-3 w-3 fill-primary text-primary" />,
                    text: '오류 발견 시 LLM이 자동으로 수정안을 생성합니다',
                  },
                  {
                    icon: <Circle className="h-3 w-3 fill-primary text-primary" />,
                    text: '수정된 파일을 다운로드해 바로 활용합니다',
                  },
                ].map((item, i) => (
                  <div key={i} className="flex items-start gap-2.5">
                    <span className="mt-0.5 shrink-0 text-primary">{item.icon}</span>
                    <span className="text-xs text-muted-foreground leading-relaxed">{item.text}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* RIGHT COLUMN — Result (only when result exists) */}
          {result && (
            <div className="min-w-0">
              {/* Result status banner */}
              <div
                className={`flex items-center gap-3 px-4 py-3 rounded-t-lg border-x border-t font-mono text-xs ${
                  result.success
                    ? 'bg-[hsl(var(--success)_/_0.06)] border-[hsl(var(--success)_/_0.3)] text-[hsl(var(--success))]'
                    : 'bg-destructive/5 border-destructive/30 text-destructive'
                }`}
              >
                <span className="font-bold text-[11px]">
                  {result.success ? 'PASS' : 'FAIL'}
                </span>
                <span className="text-muted-foreground">
                  {result.success
                    ? '모든 규격 검사를 통과했습니다'
                    : `${result.errors?.length ?? 0}개의 위반 항목이 발견됐습니다`}
                </span>
                {!result.success && hasErrors && (
                  <span className="ml-auto opacity-60">
                    {selectedFile?.name}
                  </span>
                )}
              </div>

              <VerificationResult
                success={result.success}
                message={result.message}
                errors={result.errors}
                verificationType={selectedType}
                fileName={selectedFile?.name}
                sourceFile={selectedFile}
              />
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
