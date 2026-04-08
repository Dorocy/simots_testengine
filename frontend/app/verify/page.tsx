'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { BrandLogo } from '@/components/brand-logo';
import { FileUpload } from '@/components/file-upload';
import { VerificationResult } from '@/components/verification-result';
import { apiClient, type VerificationResult as VerificationResultType } from '@/lib/api-client';
import { useAuth } from '@/lib/auth-context';
import { FileCheck, Database, Layers, LogOut } from 'lucide-react';

type VerificationType = 'metamodel' | 'template' | 'instance';

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

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border bg-card/50 backdrop-blur-sm sticky top-0 z-10">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <Link href="/">
            <BrandLogo title="ezAAS Verify" />
          </Link>
          <nav className="flex items-center gap-4">
            <Link href="/verify">
              <Button variant="ghost">검증</Button>
            </Link>
            {user?.role === 'admin' && (
              <Link href="/admin">
                <Button variant="ghost">관리자</Button>
              </Link>
            )}
            {user ? (
              <Button variant="outline" onClick={handleLogout} className="gap-2">
                <LogOut className="h-4 w-4" />
                로그아웃
              </Button>
            ) : (
              <Link href="/login">
                <Button>로그인</Button>
              </Link>
            )}
          </nav>
        </div>
      </header>

      <main className="container mx-auto px-4 py-6">
        <div className="mb-4">
          <h2 className="text-2xl font-bold mb-1">AAS 검증</h2>
          <p className="text-muted-foreground">
            AAS 파일을 업로드하고 검증 유형을 선택해 규격 적합성을 확인하세요
          </p>
        </div>

        <div className="grid lg:grid-cols-3 gap-5">
          <div className="lg:col-span-2 space-y-4">
            <Card>
              <CardHeader className="pb-2 pt-4 px-4">
                <CardTitle>검증 유형 선택</CardTitle>
                <CardDescription>
                  파일에 맞는 검증 방식을 선택하세요
                </CardDescription>
              </CardHeader>
              <CardContent className="px-4 pb-4 pt-0">
                <div className="grid md:grid-cols-3 gap-3">
                  <button
                    onClick={() => setSelectedType('metamodel')}
                    className={`p-2.5 rounded-lg border-2 transition-all text-left ${
                      selectedType === 'metamodel'
                        ? 'border-primary bg-primary/5'
                        : 'border-border hover:border-primary/50'
                    }`}
                  >
                    <FileCheck className="h-5 w-5 text-primary mb-2" />
                    <div className="font-medium mb-1">메타모델</div>
                    <div className="text-xs text-muted-foreground">
                      AAS 구조 검증
                    </div>
                  </button>

                  <button
                    onClick={() => setSelectedType('template')}
                    className={`p-2.5 rounded-lg border-2 transition-all text-left ${
                      selectedType === 'template'
                        ? 'border-primary bg-primary/5'
                        : 'border-border hover:border-primary/50'
                    }`}
                  >
                    <Layers className="h-5 w-5 text-primary mb-2" />
                    <div className="font-medium mb-1">템플릿</div>
                    <div className="text-xs text-muted-foreground">
                      템플릿 형식 검증
                    </div>
                  </button>

                  <button
                    onClick={() => setSelectedType('instance')}
                    className={`p-2.5 rounded-lg border-2 transition-all text-left ${
                      selectedType === 'instance'
                        ? 'border-primary bg-primary/5'
                        : 'border-border hover:border-primary/50'
                    }`}
                  >
                    <Database className="h-5 w-5 text-primary mb-2" />
                    <div className="font-medium mb-1">인스턴스</div>
                    <div className="text-xs text-muted-foreground">
                      스키마 기준 검사
                    </div>
                  </button>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2 pt-4 px-4">
                <CardTitle>파일 업로드</CardTitle>
                <CardDescription>
                  검증할 AAS JSON 파일을 업로드하세요
                </CardDescription>
              </CardHeader>
              <CardContent className="px-4 pb-4 pt-0">
                <FileUpload onFileSelect={handleFileSelect} />
                <div className="mt-2.5">
                  <Button
                    onClick={handleVerify}
                    disabled={!selectedFile || isVerifying}
                    className="w-full h-10"
                  >
                    {isVerifying ? '검증 중...' : '파일 검증'}
                  </Button>
                </div>
              </CardContent>
            </Card>

            {result && (
              <VerificationResult
                success={result.success}
                message={result.message}
                errors={result.errors}
                verificationType={selectedType}
                fileName={selectedFile?.name}
                sourceFile={selectedFile}
              />
            )}
          </div>

          <div className="space-y-4">
            <Card>
              <CardHeader className="pb-2 pt-4 px-4">
                <CardTitle className="text-lg">검증 안내</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm px-4 pb-4 pt-0">
                <div>
                    <div className="font-medium mb-1">메타모델 검증</div>
                  <p className="text-muted-foreground text-xs">
                      AAS Metamodel v3.0 규격 기준으로 기본 구조와 적합성을 검증합니다
                  </p>
                </div>
                <div>
                    <div className="font-medium mb-1">템플릿 검증</div>
                  <p className="text-muted-foreground text-xs">
                      템플릿이 요구 형식을 따르고 필수 필드를 포함하는지 확인합니다
                  </p>
                </div>
                <div>
                    <div className="font-medium mb-1">인스턴스 검증</div>
                  <p className="text-muted-foreground text-xs">
                      semantic ID 매칭을 기준으로 등록된 스키마와 대조합니다
                  </p>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2 pt-4 px-4">
                <CardTitle className="text-lg">파일 요구사항</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm px-4 pb-4 pt-0">
                <div className="flex items-start gap-2">
                  <div className="h-1.5 w-1.5 rounded-full bg-primary mt-1.5" />
                  <span className="text-muted-foreground">JSON 형식만 지원</span>
                </div>
                <div className="flex items-start gap-2">
                  <div className="h-1.5 w-1.5 rounded-full bg-primary mt-1.5" />
                  <span className="text-muted-foreground">최대 파일 크기: 10MB</span>
                </div>
                <div className="flex items-start gap-2">
                  <div className="h-1.5 w-1.5 rounded-full bg-primary mt-1.5" />
                  <span className="text-muted-foreground">유효한 AAS 구조 필요</span>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
    </div>
  );
}
