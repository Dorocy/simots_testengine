'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { apiClient, type Schema } from '@/lib/api-client';
import { useAuth } from '@/lib/auth-context';
import { Shield, Search, Trash2, Upload, FileJson, Plus, Eye, LogOut } from 'lucide-react';

export default function AdminPage() {
  const { user, logout, isLoading: authLoading } = useAuth();
  const router = useRouter();
  const [schemas, setSchemas] = useState<Schema[]>([]);
  const [filteredSchemas, setFilteredSchemas] = useState<Schema[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchSemanticId, setSearchSemanticId] = useState('');
  const [searchUploadedBy, setSearchUploadedBy] = useState('');
  const [selectedSchema, setSelectedSchema] = useState<Schema | null>(null);
  const [isViewDialogOpen, setIsViewDialogOpen] = useState(false);
  const [isUploadDialogOpen, setIsUploadDialogOpen] = useState(false);
  const [uploadFile, setUploadFile] = useState<File | null>(null);

  useEffect(() => {
    if (!authLoading && (!user || user.role !== 'admin')) {
      router.push('/login');
    }
  }, [user, authLoading, router]);

  useEffect(() => {
    if (user?.role === 'admin') {
      loadSchemas();
    }
  }, [user]);

  useEffect(() => {
    filterSchemas();
  }, [searchSemanticId, searchUploadedBy, schemas]);

  const loadSchemas = async () => {
    setIsLoading(true);
    try {
      const data = await apiClient.searchSchemas();
      setSchemas(data);
      setFilteredSchemas(data);
    } catch (error) {
      console.error('[v0] Failed to load schemas:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const filterSchemas = () => {
    let filtered = schemas;

    if (searchSemanticId) {
      filtered = filtered.filter((schema) =>
        schema.semanticId.toLowerCase().includes(searchSemanticId.toLowerCase())
      );
    }

    if (searchUploadedBy) {
      filtered = filtered.filter((schema) =>
        schema.uploadedBy.toLowerCase().includes(searchUploadedBy.toLowerCase())
      );
    }

    setFilteredSchemas(filtered);
  };

  const handleDelete = async (semanticId: string) => {
    if (!confirm('Are you sure you want to delete this schema?')) return;

    try {
      await apiClient.deleteSchema(semanticId);
      await loadSchemas();
    } catch (error) {
      console.error('[v0] Failed to delete schema:', error);
      alert('Failed to delete schema');
    }
  };

  const handleViewSchema = (schema: Schema) => {
    setSelectedSchema(schema);
    setIsViewDialogOpen(true);
  };

  const handleUploadSchema = async () => {
    if (!uploadFile) return;

    try {
      await apiClient.createSchema(uploadFile);
      setIsUploadDialogOpen(false);
      setUploadFile(null);
      await loadSchemas();
    } catch (error) {
      console.error('[v0] Failed to upload schema:', error);
      alert('Failed to upload schema');
    }
  };

  const handleLogout = () => {
    logout();
    router.push('/');
  };

  if (authLoading || !user || user.role !== 'admin') {
    return null;
  }

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border bg-card/50 backdrop-blur-sm sticky top-0 z-10">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2">
            <Shield className="h-6 w-6 text-primary" />
            <h1 className="text-xl font-bold">AAS Verify - Admin</h1>
          </Link>
          <nav className="flex items-center gap-4">
            <Link href="/verify">
              <Button variant="ghost">Verification</Button>
            </Link>
            <Link href="/admin">
              <Button variant="ghost">Admin</Button>
            </Link>
            <Button variant="outline" onClick={handleLogout} className="gap-2">
              <LogOut className="h-4 w-4" />
              Sign Out
            </Button>
          </nav>
        </div>
      </header>

      <main className="container mx-auto px-4 py-12">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h2 className="text-3xl font-bold mb-2">Schema Management</h2>
            <p className="text-muted-foreground">
              Manage AAS schemas, search by semantic ID or manufacturer
            </p>
          </div>
          <Button onClick={() => setIsUploadDialogOpen(true)} className="gap-2">
            <Plus className="h-4 w-4" />
            Add Schema
          </Button>
        </div>

        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Search Schemas</CardTitle>
            <CardDescription>Filter schemas by semantic ID or uploaded by</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-2 gap-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search by Semantic ID"
                  value={searchSemanticId}
                  onChange={(e) => setSearchSemanticId(e.target.value)}
                  className="pl-9"
                />
              </div>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search by Manufacturer"
                  value={searchUploadedBy}
                  onChange={(e) => setSearchUploadedBy(e.target.value)}
                  className="pl-9"
                />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Registered Schemas</CardTitle>
              <Badge variant="secondary">{filteredSchemas.length} total</Badge>
            </div>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="text-center py-12 text-muted-foreground">
                Loading schemas...
              </div>
            ) : filteredSchemas.length === 0 ? (
              <div className="text-center py-12 text-muted-foreground">
                No schemas found
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Semantic ID</TableHead>
                    <TableHead>Uploaded By</TableHead>
                    <TableHead>Created At</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredSchemas.map((schema, index) => (
                    <TableRow key={index}>
                      <TableCell className="font-mono text-sm">
                        {schema.semanticId}
                      </TableCell>
                      <TableCell>{schema.uploadedBy}</TableCell>
                      <TableCell className="text-muted-foreground">
                        {schema.createdAt
                          ? new Date(schema.createdAt).toLocaleDateString()
                          : 'N/A'}
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-2">
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => handleViewSchema(schema)}
                          >
                            <Eye className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => handleDelete(schema.semanticId)}
                          >
                            <Trash2 className="h-4 w-4 text-destructive" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </main>

      <Dialog open={isViewDialogOpen} onOpenChange={setIsViewDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Schema Details</DialogTitle>
            <DialogDescription>View schema information and structure</DialogDescription>
          </DialogHeader>
          {selectedSchema && (
            <div className="space-y-4">
              <div>
                <div className="text-sm font-medium mb-1">Semantic ID</div>
                <div className="text-sm text-muted-foreground font-mono bg-muted p-2 rounded">
                  {selectedSchema.semanticId}
                </div>
              </div>
              <div>
                <div className="text-sm font-medium mb-1">Uploaded By</div>
                <div className="text-sm text-muted-foreground">
                  {selectedSchema.uploadedBy}
                </div>
              </div>
              <div>
                <div className="text-sm font-medium mb-1">Schema Structure</div>
                <pre className="text-xs bg-muted p-3 rounded overflow-auto max-h-64 font-mono">
                  {JSON.stringify(selectedSchema.schema, null, 2)}
                </pre>
              </div>
              <Button onClick={() => setIsViewDialogOpen(false)} className="w-full">
                Close
              </Button>
            </div>
          )}
        </DialogContent>
      </Dialog>

      <Dialog open={isUploadDialogOpen} onOpenChange={setIsUploadDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add New Schema</DialogTitle>
            <DialogDescription>Upload a new AAS schema JSON file</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="border-2 border-dashed border-border rounded-lg p-6 text-center">
              <FileJson className="h-12 w-12 mx-auto mb-3 text-muted-foreground" />
              <Input
                type="file"
                accept=".json"
                onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                className="cursor-pointer"
              />
            </div>
            {uploadFile && (
              <div className="text-sm text-muted-foreground">
                Selected: {uploadFile.name}
              </div>
            )}
            <div className="flex gap-2">
              <Button
                onClick={handleUploadSchema}
                disabled={!uploadFile}
                className="flex-1 gap-2"
              >
                <Upload className="h-4 w-4" />
                Upload Schema
              </Button>
              <Button
                variant="outline"
                onClick={() => {
                  setIsUploadDialogOpen(false);
                  setUploadFile(null);
                }}
              >
                Cancel
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
