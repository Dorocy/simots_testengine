import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { FileCheck, Shield, Database, ArrowRight } from 'lucide-react';

export default function HomePage() {
  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border bg-card/50 backdrop-blur-sm sticky top-0 z-10">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Shield className="h-6 w-6 text-primary" />
            <h1 className="text-xl font-bold">AAS Verify</h1>
          </div>
          <nav className="flex items-center gap-4">
            <Link href="/verify">
              <Button variant="ghost">검증</Button>
            </Link>
            <Link href="/admin">
              <Button variant="ghost">관리자</Button>
            </Link>
            <Link href="/login">
              <Button>로그인</Button>
            </Link>
          </nav>
        </div>
      </header>

      <main className="container mx-auto px-4 py-16">
        <section className="text-center mb-16">
          <h2 className="text-5xl font-bold mb-6 text-balance">
            AAS 검증 플랫폼
          </h2>
          <p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto text-pretty">
            Asset Administration Shell 모델을 신뢰성 있게 검증하세요.
            AAS Part 1 Metamodel v3.0 규격 준수 여부를 빠르게 확인할 수 있습니다.
          </p>
          <div className="flex items-center justify-center gap-4">
            <Link href="/verify">
              <Button size="lg" className="gap-2">
                검증 시작 <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
            <Link href="/docs">
              <Button size="lg" variant="outline">
                문서 보기
              </Button>
            </Link>
          </div>
        </section>

        <section className="grid md:grid-cols-3 gap-6 mb-16">
          <Card className="border-border hover:border-primary transition-colors">
            <CardHeader>
              <div className="h-12 w-12 rounded-lg bg-primary/10 flex items-center justify-center mb-4">
                <FileCheck className="h-6 w-6 text-primary" />
              </div>
              <CardTitle>메타모델 검증</CardTitle>
              <CardDescription>
                공식 규격을 기준으로 AAS 메타모델 구조를 검증합니다
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                idShort, semanticId, 구조 적합성까지 종합적으로 점검합니다
              </p>
            </CardContent>
          </Card>

          <Card className="border-border hover:border-primary transition-colors">
            <CardHeader>
              <div className="h-12 w-12 rounded-lg bg-primary/10 flex items-center justify-center mb-4">
                <Shield className="h-6 w-6 text-primary" />
              </div>
              <CardTitle>템플릿 검증</CardTitle>
              <CardDescription>
                AAS 템플릿이 요구 형식과 규격을 만족하는지 확인합니다
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                상세 오류와 함께 템플릿 구조를 자동으로 검증합니다
              </p>
            </CardContent>
          </Card>

          <Card className="border-border hover:border-primary transition-colors">
            <CardHeader>
              <div className="h-12 w-12 rounded-lg bg-primary/10 flex items-center justify-center mb-4">
                <Database className="h-6 w-6 text-primary" />
              </div>
              <CardTitle>인스턴스 검증</CardTitle>
              <CardDescription>
                등록된 스키마를 기준으로 AAS 인스턴스를 검증합니다
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                semantic ID 매칭과 데이터 무결성 검사를 함께 수행합니다
              </p>
            </CardContent>
          </Card>
        </section>

        <section className="bg-card border border-border rounded-lg p-12 text-center">
          <h3 className="text-3xl font-bold mb-4">
            산업 현장을 위한 검증 워크플로
          </h3>
          <p className="text-muted-foreground mb-8 max-w-2xl mx-auto">
            AAS 테스트 엔진을 기반으로 구축되었으며 Asset Administration Shell 규격에 맞춘 검증 흐름을 제공합니다.
            디지털 트윈 데이터의 국제 표준 적합성을 빠르게 점검할 수 있습니다.
          </p>
          <div className="flex items-center justify-center gap-8 text-sm text-muted-foreground">
            <div>
              <div className="text-2xl font-bold text-foreground">v3.0</div>
              <div>AAS 메타모델</div>
            </div>
            <div className="h-12 w-px bg-border" />
            <div>
              <div className="text-2xl font-bold text-foreground">100%</div>
              <div>규격 준수</div>
            </div>
            <div className="h-12 w-px bg-border" />
            <div>
              <div className="text-2xl font-bold text-foreground">실시간</div>
              <div>검증</div>
            </div>
          </div>
        </section>
      </main>

      <footer className="border-t border-border mt-24 py-8">
        <div className="container mx-auto px-4 text-center text-sm text-muted-foreground">
          <p>AAS Verify - Asset Administration Shell 검증 플랫폼</p>
        </div>
      </footer>
    </div>
  );
}
