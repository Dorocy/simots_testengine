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
  Play,
  Zap,
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

// 에러가 많이 포함된 데모용 AAS 샘플 JSON
const DEMO_SAMPLE_JSON = JSON.stringify({
  assetAdministrationShells: [
    {
      id: "urn:demo:aas:001",
      assetInformation: {
        assetKind: "Instance",
        globalAssetId: "urn:demo:asset:001"
      },
      submodels: [
        { type: "ModelReference", keys: [{ type: "Submodel", value: "urn:demo:sm:001" }] }
      ]
    }
  ],
  submodels: [
    {
      id: "urn:demo:sm:001",
      kind: "Instance",
      semanticId: {
        type: "ExternalReference",
        keys: [{ type: "GlobalReference", value: "https://admin-shell.io/demo/1/0" }]
      },
      submodelElements: [
        {
          modelType: "Property",
          idShort: "Temperature",
          valueType: "xs:float",
          value: "23.5",
          semanticId: null
        },
        {
          modelType: "Property",
          idShort: "",
          valueType: "xs:string",
          value: "Active"
        },
        {
          modelType: "SubmodelElementCollection",
          idShort: "Measurements",
          value: [
            {
              modelType: "Property",
              idShort: "Pressure",
              valueType: "invalidType",
              value: "1013"
            }
          ]
        },
        {
          modelType: "MultiLanguageProperty",
          idShort: "Description",
          value: "should be array not string"
        }
      ]
    }
  ],
  conceptDescriptions: []
}, null, 2);

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
  const [fileUploadKey, setFileUploadKey] = useState(0); // force re-mount FileUpload on demo load

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

  // 데모 샘플 파일 자동 로드 + 즉시 검증 실행
  const handleLoadDemo = async () => {
    const blob = new Blob([DEMO_SAMPLE_JSON], { type: 'application/json' });
    const file = new File([blob], 'demo-aas-sample.json', { type: 'application/json' });
    setSelectedFile(file);
    setResult(null);
    setFileUploadKey((k) => k + 1);

    setIsVerifying(true);
    try {
      const response = await apiClient.verifyMetamodel(file);
      setResult(response);
      setSelectedType('metamodel');
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
    }
  };

  const hasErrors = result && !result.success && (result.errors?.length ?? 0) > 0;
  const activeStepIndex = getPipelineActiveStep(!!selectedFile, isVerifying, !!result, !!hasErrors);

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
            <div className="hidden md:flex items-center gap-1.5 text-[11px] font-mono text-muted-foreground">
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
              {/* Demo button */}
              <Button
                variant="outline"
                size="sm"
                onClick={handleLoadDemo}
                disabled={isVerifying}
                className="gap-1.5 text-xs shrink-0 border-primary/30 text-primary hover:bg-primary/5"
              >
                <Zap className="h-3.5 w-3.5" />
                데모 실행
              </Button>
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
                    className={`relative p-3 rounded-lg border text-left transition-all ${
                      selectedType === vt.id
                        ? 'border-primary bg-primary/5 shadow-sm'
                        : 'border-border bg-card hover:border-primary/40 hover:bg-muted/20'
                    }`}
                  >
                    {selectedType === vt.id && (
                      <div className="absolute top-0 left-0 right-0 h-0.5 bg-primary rounded-t-lg" />
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
            <div className="min-w-0">
              {/* Result status banner */}
              <div
                className={`flex items-center gap-3 px-4 py-3 rounded-t-lg border-x border-t font-mono text-xs ${
                  result.success
                    ? 'bg-[hsl(142_71%_45%_/_0.06)] border-[hsl(142_71%_45%_/_0.3)] text-[hsl(142_71%_45%)]'
                    : 'bg-destructive/5 border-destructive/30 text-destructive'
                }`}
              >
                <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold border ${
                  result.success
                    ? 'bg-[hsl(142_71%_45%_/_0.15)] border-[hsl(142_71%_45%_/_0.4)] text-[hsl(142_71%_45%)]'
                    : 'bg-destructive/15 border-destructive/40 text-destructive'
                }`}>
                  {result.success ? 'PASS' : 'FAIL'}
                </span>
                <span className="text-muted-foreground">
                  {result.success
                    ? '모든 규격 검사를 통과했습니다'
                    : `${result.errors?.length ?? 0}개의 위반 항목이 발견됐습니다 — AI가 자동 수정할 수 있습니다`}
                </span>
                {selectedFile && (
                  <span className="ml-auto text-muted-foreground/60 truncate max-w-[160px]">
                    {selectedFile.name}
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
