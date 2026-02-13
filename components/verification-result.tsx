'use client';

import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { CheckCircle2, XCircle, AlertCircle } from 'lucide-react';

export interface VerificationError {
  code: string;
  message: string;
  location?: string;
}

interface VerificationResultProps {
  success: boolean;
  message?: string;
  errors?: VerificationError[];
}

export function VerificationResult({ success, message, errors }: VerificationResultProps) {
  return (
    <Card className={success ? 'border-green-500/50' : 'border-destructive/50'}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            {success ? (
              <>
                <CheckCircle2 className="h-5 w-5 text-green-500" />
                Verification Successful
              </>
            ) : (
              <>
                <XCircle className="h-5 w-5 text-destructive" />
                Verification Failed
              </>
            )}
          </CardTitle>
          <Badge variant={success ? 'success' : 'destructive'}>
            {success ? 'PASSED' : 'FAILED'}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        {message && (
          <p className="text-sm text-muted-foreground mb-4">{message}</p>
        )}
        
        {errors && errors.length > 0 && (
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-sm font-medium">
              <AlertCircle className="h-4 w-4" />
              Errors Found ({errors.length})
            </div>
            <div className="space-y-2">
              {errors.map((error, index) => (
                <div
                  key={index}
                  className="p-3 rounded-md bg-destructive/10 border border-destructive/20"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1">
                      <p className="text-sm font-medium text-destructive mb-1">
                        {error.code}
                      </p>
                      <p className="text-sm text-muted-foreground">
                        {error.message}
                      </p>
                      {error.location && (
                        <p className="text-xs text-muted-foreground mt-1 font-mono">
                          Location: {error.location}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {success && !message && (
          <p className="text-sm text-green-600 dark:text-green-400">
            All validation checks passed. Your AAS file meets the required specifications.
          </p>
        )}
      </CardContent>
    </Card>
  );
}
