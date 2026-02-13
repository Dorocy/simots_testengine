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
              <Button variant="ghost">Verification</Button>
            </Link>
            <Link href="/admin">
              <Button variant="ghost">Admin</Button>
            </Link>
            <Link href="/login">
              <Button>Sign In</Button>
            </Link>
          </nav>
        </div>
      </header>

      <main className="container mx-auto px-4 py-16">
        <section className="text-center mb-16">
          <h2 className="text-5xl font-bold mb-6 text-balance">
            Professional AAS Verification Platform
          </h2>
          <p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto text-pretty">
            Validate Asset Administration Shell models with confidence. 
            Ensure compliance with AAS Part 1 Metamodel v3.0 specifications.
          </p>
          <div className="flex items-center justify-center gap-4">
            <Link href="/verify">
              <Button size="lg" className="gap-2">
                Start Verification <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
            <Link href="/docs">
              <Button size="lg" variant="outline">
                View Documentation
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
              <CardTitle>Metamodel Verification</CardTitle>
              <CardDescription>
                Validate AAS metamodel structure against official specifications
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                Comprehensive checks for idShort, semanticId, and structural compliance
              </p>
            </CardContent>
          </Card>

          <Card className="border-border hover:border-primary transition-colors">
            <CardHeader>
              <div className="h-12 w-12 rounded-lg bg-primary/10 flex items-center justify-center mb-4">
                <Shield className="h-6 w-6 text-primary" />
              </div>
              <CardTitle>Template Validation</CardTitle>
              <CardDescription>
                Ensure your AAS templates meet industry standards
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                Automated template structure verification with detailed error reporting
              </p>
            </CardContent>
          </Card>

          <Card className="border-border hover:border-primary transition-colors">
            <CardHeader>
              <div className="h-12 w-12 rounded-lg bg-primary/10 flex items-center justify-center mb-4">
                <Database className="h-6 w-6 text-primary" />
              </div>
              <CardTitle>Instance Checking</CardTitle>
              <CardDescription>
                Verify AAS instances against registered schemas
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                Real-time validation with semantic ID matching and data integrity checks
              </p>
            </CardContent>
          </Card>
        </section>

        <section className="bg-card border border-border rounded-lg p-12 text-center">
          <h3 className="text-3xl font-bold mb-4">
            Trusted by Manufacturing Leaders
          </h3>
          <p className="text-muted-foreground mb-8 max-w-2xl mx-auto">
            Built on AAS test engines and officially compliant with Asset Administration Shell specifications. 
            Ensure your digital twin data meets international standards.
          </p>
          <div className="flex items-center justify-center gap-8 text-sm text-muted-foreground">
            <div>
              <div className="text-2xl font-bold text-foreground">v3.0</div>
              <div>AAS Metamodel</div>
            </div>
            <div className="h-12 w-px bg-border" />
            <div>
              <div className="text-2xl font-bold text-foreground">100%</div>
              <div>Spec Compliant</div>
            </div>
            <div className="h-12 w-px bg-border" />
            <div>
              <div className="text-2xl font-bold text-foreground">Real-time</div>
              <div>Validation</div>
            </div>
          </div>
        </section>
      </main>

      <footer className="border-t border-border mt-24 py-8">
        <div className="container mx-auto px-4 text-center text-sm text-muted-foreground">
          <p>AAS Verify - Professional Asset Administration Shell Verification Platform</p>
        </div>
      </footer>
    </div>
  );
}
