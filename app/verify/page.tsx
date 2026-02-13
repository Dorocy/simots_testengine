'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { FileUpload } from '@/components/file-upload';
import { VerificationResult } from '@/components/verification-result';
import { apiClient, type VerificationResult as VerificationResultType } from '@/lib/api-client';
import { useAuth } from '@/lib/auth-context';
import { Shield, FileCheck, Database, Layers, LogOut } from 'lucide-react';

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
        message: 'Verification failed. Please check your file and try again.',
        errors: [
          {
            code: 'NETWORK_ERROR',
            message: error instanceof Error ? error.message : 'Unknown error occurred',
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
          <Link href="/" className="flex items-center gap-2">
            <Shield className="h-6 w-6 text-primary" />
            <h1 className="text-xl font-bold">AAS Verify</h1>
          </Link>
          <nav className="flex items-center gap-4">
            <Link href="/verify">
              <Button variant="ghost">Verification</Button>
            </Link>
            {user?.role === 'admin' && (
              <Link href="/admin">
                <Button variant="ghost">Admin</Button>
              </Link>
            )}
            {user ? (
              <Button variant="outline" onClick={handleLogout} className="gap-2">
                <LogOut className="h-4 w-4" />
                Sign Out
              </Button>
            ) : (
              <Link href="/login">
                <Button>Sign In</Button>
              </Link>
            )}
          </nav>
        </div>
      </header>

      <main className="container mx-auto px-4 py-12">
        <div className="mb-8">
          <h2 className="text-3xl font-bold mb-2">AAS Verification</h2>
          <p className="text-muted-foreground">
            Upload your AAS file and select the verification type to validate against official specifications
          </p>
        </div>

        <div className="grid lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Select Verification Type</CardTitle>
                <CardDescription>
                  Choose the appropriate verification method for your AAS file
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid md:grid-cols-3 gap-4">
                  <button
                    onClick={() => setSelectedType('metamodel')}
                    className={`p-4 rounded-lg border-2 transition-all text-left ${
                      selectedType === 'metamodel'
                        ? 'border-primary bg-primary/5'
                        : 'border-border hover:border-primary/50'
                    }`}
                  >
                    <FileCheck className="h-6 w-6 text-primary mb-2" />
                    <div className="font-medium mb-1">Metamodel</div>
                    <div className="text-xs text-muted-foreground">
                      Validate AAS structure
                    </div>
                  </button>

                  <button
                    onClick={() => setSelectedType('template')}
                    className={`p-4 rounded-lg border-2 transition-all text-left ${
                      selectedType === 'template'
                        ? 'border-primary bg-primary/5'
                        : 'border-border hover:border-primary/50'
                    }`}
                  >
                    <Layers className="h-6 w-6 text-primary mb-2" />
                    <div className="font-medium mb-1">Template</div>
                    <div className="text-xs text-muted-foreground">
                      Verify template format
                    </div>
                  </button>

                  <button
                    onClick={() => setSelectedType('instance')}
                    className={`p-4 rounded-lg border-2 transition-all text-left ${
                      selectedType === 'instance'
                        ? 'border-primary bg-primary/5'
                        : 'border-border hover:border-primary/50'
                    }`}
                  >
                    <Database className="h-6 w-6 text-primary mb-2" />
                    <div className="font-medium mb-1">Instance</div>
                    <div className="text-xs text-muted-foreground">
                      Check against schema
                    </div>
                  </button>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Upload File</CardTitle>
                <CardDescription>
                  Upload your AAS JSON file for verification
                </CardDescription>
              </CardHeader>
              <CardContent>
                <FileUpload onFileSelect={handleFileSelect} />
                <div className="mt-4">
                  <Button
                    onClick={handleVerify}
                    disabled={!selectedFile || isVerifying}
                    className="w-full"
                    size="lg"
                  >
                    {isVerifying ? 'Verifying...' : 'Verify File'}
                  </Button>
                </div>
              </CardContent>
            </Card>

            {result && (
              <VerificationResult
                success={result.success}
                message={result.message}
                errors={result.errors}
              />
            )}
          </div>

          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Verification Guide</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4 text-sm">
                <div>
                  <div className="font-medium mb-1">Metamodel Verification</div>
                  <p className="text-muted-foreground text-xs">
                    Validates the basic structure and compliance with AAS Metamodel v3.0 specifications
                  </p>
                </div>
                <div>
                  <div className="font-medium mb-1">Template Verification</div>
                  <p className="text-muted-foreground text-xs">
                    Checks if your template follows the required format and contains necessary fields
                  </p>
                </div>
                <div>
                  <div className="font-medium mb-1">Instance Verification</div>
                  <p className="text-muted-foreground text-xs">
                    Verifies instances against registered schemas using semantic ID matching
                  </p>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">File Requirements</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                <div className="flex items-start gap-2">
                  <div className="h-1.5 w-1.5 rounded-full bg-primary mt-1.5" />
                  <span className="text-muted-foreground">JSON format only</span>
                </div>
                <div className="flex items-start gap-2">
                  <div className="h-1.5 w-1.5 rounded-full bg-primary mt-1.5" />
                  <span className="text-muted-foreground">Maximum file size: 10MB</span>
                </div>
                <div className="flex items-start gap-2">
                  <div className="h-1.5 w-1.5 rounded-full bg-primary mt-1.5" />
                  <span className="text-muted-foreground">Valid AAS structure required</span>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
    </div>
  );
}
