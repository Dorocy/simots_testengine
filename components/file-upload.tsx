'use client';

import { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, File, X } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';

interface FileUploadProps {
  onFileSelect: (file: File) => void;
  accept?: Record<string, string[]>;
  maxSize?: number;
}

export function FileUpload({ onFileSelect, accept = { 'application/json': ['.json'] }, maxSize = 10485760 }: FileUploadProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      const file = acceptedFiles[0];
      setSelectedFile(file);
      onFileSelect(file);
    }
  }, [onFileSelect]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept,
    maxSize,
    multiple: false,
  });

  const clearFile = () => {
    setSelectedFile(null);
  };

  return (
    <div className="space-y-2.5">
      <div
        {...getRootProps()}
        className={cn(
          'border-2 border-dashed rounded-lg p-4 text-center cursor-pointer transition-colors',
          isDragActive ? 'border-primary bg-primary/5' : 'border-border hover:border-primary/50',
          selectedFile && 'border-primary bg-primary/5'
        )}
      >
        <input {...getInputProps()} />
        <div className="flex flex-col items-center gap-2">
          <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center">
            <Upload className="h-5 w-5 text-primary" />
          </div>
          {isDragActive ? (
            <p className="text-sm font-medium">여기에 파일을 놓으세요</p>
          ) : (
            <div>
              <p className="text-sm font-medium mb-1">
                파일을 여기로 드래그하거나
              </p>
              <p className="text-xs text-muted-foreground">
                클릭해서 선택하세요 (JSON만 가능, 최대 10MB)
              </p>
            </div>
          )}
        </div>
      </div>

      {selectedFile && (
        <div className="flex items-center justify-between p-2.5 bg-card border border-border rounded-lg">
          <div className="flex items-center gap-3">
            <div className="h-8 w-8 rounded-lg bg-primary/10 flex items-center justify-center">
              <File className="h-4 w-4 text-primary" />
            </div>
            <div>
              <p className="text-sm font-medium">{selectedFile.name}</p>
              <p className="text-xs text-muted-foreground">
                {(selectedFile.size / 1024).toFixed(2)} KB
              </p>
            </div>
          </div>
          <Button variant="ghost" size="icon" onClick={clearFile}>
            <X className="h-4 w-4" />
          </Button>
        </div>
      )}
    </div>
  );
}
