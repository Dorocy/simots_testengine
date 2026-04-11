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
  ChevronRight,
  ArrowRight,
  Cpu,
  ShieldCheck,
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
    description: 'AAS Metamodel v3.0 규격 기준 구조 검증',
    tag: 'METAMODEL',
  },
  {
    id: 'template',
    icon: <Layers className="h-4 w-4" />,
    label: '템플릿',
    description: '필수 필드 및 템플릿 형식 준수 확인',
    tag: 'TEMPLATE',
  },
  {
    id: 'instance',
    icon: <Database className="h-4 w-4" />,
    label: '인스턴스',
    description: 'Semantic ID 기반 스키마 대조 검사',
    tag: 'INSTANCE',
  },
];

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
            message:
              error instanceof Error ? error.message : '알 수 없는 오류가 발생했습니다.',
          },
        ],
      });
    } finally {
      setIsVerifying(false);
    }
  };

  const selectedTypeInfo = VERIFICATION_TYPES.find((t) => t.id === selectedType)!;

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card sticky top-0 z-20">
        <div className="container mx-auto px-4 h-14 flex items-center justify-between">
          <Link href="/">
            <BrandLogo title="ezAAS Verify" imageClassName="h-7 w-auto" titleClassName="text-base font-semibold tracking-tight" />
          </Link>
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

      <main className="container mx-auto px-4 py-8 max-w-6xl">

        {/* Pipeline flow header */}
        <div className="mb-8">
          <div className="flex items-center gap-2 text-xs font-mono text-muted-foreground mb-3">
            <ShieldCheck className="h-3.5 w-3.5 text-primary" />
            <span>AAS VERIFICATION ENGINE</span>
          </div>
          <h1 className="text-2xl font-semibold tracking-tight mb-1">AAS 파일 검증</h1>
          <p className="text-sm text-muted-foreground">
            JSON 파일을 업로드하고 규격 적합성을 AI로 분석합니다
          </p>

          {/* Pipeline visual */}
          <div className="mt-5 flex items-center gap-0 overflow-x-auto pb-1">
            {[
              { step: '01', label: 'INPUT', sublabel: '파일 업로드', active: !!selectedFile },
              { step: '02', label: 'PARSE', sublabel: '구조 파싱', active: !!selectedFile },
              { step: '03', label: 'VERIFY', sublabel: `${selectedTypeInfo.tag}`, active: isVerifying || !!result },
              { step: '04', label: 'OUTPUT', sublabel: '결과 분석', active: !!result },
            ].map((node, i) => (
              <div key={node.step} className="flex items-center">
                <div
                  className={`flex items-center gap-2 px-3 py-2 rounded border text-xs font-mono transition-colors whitespace-nowrap ${
                    node.active
                      ? 'bg-primary/10 border-primary/40 text-primary'
                      : 'bg-card border-border text-muted-foreground'
                  }`}
                >
                  <span className={`text-[10px] font-semibold ${node.active ? 'text-primary' : 'text-muted-foreground/60'}`}>
                    {node.step}
                  </span>
                  <div>
                    <div className="font-semibold leading-none mb-0.5">{node.label}</div>
                    <div className="text-[10px] opacity-70">{node.sublabel}</div>
                  </div>
                  {isVerifying && node.step === '03' && (
                    <Cpu className="h-3 w-3 animate-pulse" />
                  )}
                </div>
                {i < 3 && (
                  <div className="flex items-center px-1">
                    <svg width="32" height="12" viewBox="0 0 32 12" fill="none" className="overflow-visible">
                      <line
                        x1="0" y1="6" x2="24" y2="6"
                        stroke="hsl(var(--connector))"
                        strokeWidth="1.5"
                        className={node.active ? 'pipeline-flow' : ''}
                        strokeDasharray={node.active ? '4 4' : 'none'}
                      />
                      <polyline
                        points="20,2 26,6 20,10"
                        fill="none"
                        stroke="hsl(var(--connector))"
                        strokeWidth="1.5"
                        strokeLinejoin="round"
                        strokeLinecap="round"
                      />
                    </svg>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        <div className="grid lg:grid-cols-[1fr_280px] gap-6">
          {/* Left — main controls */}
          <div className="space-y-5">

            {/* Step 1: Verification type */}
            <section>
              <div className="flex items-center gap-2 mb-3">
                <span className="text-[10px] font-mono font-semibold text-muted-foreground bg-muted px-1.5 py-0.5 rounded">STEP 1</span>
                <h2 className="text-sm font-semibold">검증 유형 선택</h2>
              </div>
              <div className="grid grid-cols-3 gap-2">
                {VERIFICATION_TYPES.map((vt) => (
                  <button
                    key={vt.id}
                    onClick={() => setSelectedType(vt.id)}
                    className={`relative p-3.5 rounded-lg border text-left transition-all group ${
                      selectedType === vt.id
                        ? 'border-primary bg-primary/5 shadow-sm'
                        : 'border-border bg-card hover:border-primary/40 hover:bg-muted/40'
                    }`}
                  >
                    {selectedType === vt.id && (
                      <span className="absolute top-2 right-2 text-[9px] font-mono font-bold text-primary bg-primary/10 px-1.5 py-0.5 rounded">
                        ACTIVE
                      </span>
                    )}
                    <div className={`mb-2.5 ${selectedType === vt.id ? 'text-primary' : 'text-muted-foreground group-hover:text-foreground'}`}>
                      {vt.icon}
                    </div>
                    <div className="text-xs font-semibold mb-1">{vt.label}</div>
                    <div className="text-[11px] text-muted-foreground leading-relaxed">{vt.description}</div>
                  </button>
                ))}
              </div>
            </section>

            {/* Step 2: File upload */}
            <section>
              <div className="flex items-center gap-2 mb-3">
                <span className="text-[10px] font-mono font-semibold text-muted-foreground bg-muted px-1.5 py-0.5 rounded">STEP 2</span>
                <h2 className="text-sm font-semibold">파일 업로드</h2>
              </div>
              <div className="bg-card border border-border rounded-lg p-4 space-y-3">
                <FileUpload onFileSelect={handleFileSelect} />
                <Button
                  onClick={handleVerify}
                  disabled={!selectedFile || isVerifying}
                  className="w-full gap-2"
                >
                  {isVerifying ? (
                    <>
                      <Cpu className="h-4 w-4 animate-pulse" />
                      검증 중...
                    </>
                  ) : (
                    <>
                      <ArrowRight className="h-4 w-4" />
                      파일 검증 실행
                    </>
                  )}
                </Button>
              </div>
            </section>

            {/* Step 3: Result */}
            {result && (
              <section>
                <div className="flex items-center gap-2 mb-3">
                  <span className="text-[10px] font-mono font-semibold text-muted-foreground bg-muted px-1.5 py-0.5 rounded">STEP 3</span>
                  <h2 className="text-sm font-semibold">검증 결과</h2>
                </div>
                <VerificationResult
                  success={result.success}
                  message={result.message}
                  errors={result.errors}
                  verificationType={selectedType}
                  fileName={selectedFile?.name}
                  sourceFile={selectedFile}
                />
              </section>
            )}
          </div>

          {/* Right — info panel */}
          <aside className="space-y-4">
            <div className="bg-card border border-border rounded-lg p-4">
              <h3 className="text-xs font-semibold font-mono text-muted-foreground mb-3 uppercase tracking-wide">
                검증 모드 안내
              </h3>
              <div className="space-y-3">
                {VERIFICATION_TYPES.map((vt) => (
                  <div
                    key={vt.id}
                    className={`flex gap-2.5 p-2.5 rounded-md transition-colors ${
                      selectedType === vt.id ? 'bg-primary/5 border border-primary/20' : ''
                    }`}
                  >
                    <div className={`mt-0.5 shrink-0 ${selectedType === vt.id ? 'text-primary' : 'text-muted-foreground'}`}>
                      {vt.icon}
                    </div>
                    <div>
                      <div className="text-xs font-semibold mb-0.5">{vt.label}</div>
                      <p className="text-[11px] text-muted-foreground leading-relaxed">{vt.description}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-card border border-border rounded-lg p-4">
              <h3 className="text-xs font-semibold font-mono text-muted-foreground mb-3 uppercase tracking-wide">
                파일 요구사항
              </h3>
              <ul className="space-y-2">
                {['JSON 형식만 지원', '최대 파일 크기: 10MB', '유효한 AAS 구조 필요'].map((req) => (
                  <li key={req} className="flex items-start gap-2 text-xs text-muted-foreground">
                    <ChevronRight className="h-3.5 w-3.5 shrink-0 mt-0.5 text-primary" />
                    {req}
                  </li>
                ))}
              </ul>
            </div>

            {/* Active type details */}
            <div className="bg-primary/5 border border-primary/20 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-primary">{selectedTypeInfo.icon}</span>
                <span className="text-xs font-semibold text-primary">{selectedTypeInfo.label} 검증</span>
              </div>
              <p className="text-[11px] text-muted-foreground leading-relaxed">
                {selectedTypeInfo.description}
              </p>
              <div className="mt-2.5 font-mono text-[10px] text-primary/60 bg-primary/5 rounded px-2 py-1 inline-block">
                mode: {selectedTypeInfo.tag.toLowerCase()}
              </div>
            </div>
          </aside>
        </div>
      </main>
    </div>
  );
}
