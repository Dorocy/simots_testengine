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
    <div className="space-y-2">
      <div
        {...getRootProps()}
        className={cn(
          'border border-dashed rounded-md p-5 text-center cursor-pointer transition-all',
          isDragActive
            ? 'border-primary bg-primary/5'
            : 'border-border hover:border-primary/50 hover:bg-muted/30',
          selectedFile && 'border-primary/40 bg-primary/5'
        )}
      >
        <input {...getInputProps()} />
        <div className="flex flex-col items-center gap-2">
          <div className="h-9 w-9 rounded-lg bg-primary/10 flex items-center justify-center">
            <Upload className="h-4 w-4 text-primary" />
          </div>
          {isDragActive ? (
            <p className="text-xs font-medium text-primary">여기에 파일을 놓으세요</p>
          ) : (
            <div>
              <p className="text-xs font-medium mb-0.5">
                파일을 드래그하거나 클릭해서 선택
              </p>
              <p className="text-[11px] text-muted-foreground font-mono">
                JSON · 최대 10MB
              </p>
            </div>
          )}
        </div>
      </div>

      {selectedFile && (
        <div className="flex items-center justify-between p-2.5 bg-muted/30 border border-border rounded-md">
          <div className="flex items-center gap-2.5">
            <div className="h-7 w-7 rounded bg-primary/10 flex items-center justify-center shrink-0">
              <File className="h-3.5 w-3.5 text-primary" />
            </div>
            <div>
              <p className="text-xs font-medium font-mono truncate max-w-[200px]">{selectedFile.name}</p>
              <p className="text-[10px] text-muted-foreground">
                {(selectedFile.size / 1024).toFixed(1)} KB
              </p>
            </div>
          </div>
          <Button variant="ghost" size="icon" className="h-7 w-7" onClick={clearFile}>
            <X className="h-3.5 w-3.5" />
          </Button>
        </div>
      )}
    </div>
  );
}
