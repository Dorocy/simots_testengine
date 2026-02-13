const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://te.amrc.kr';

export interface VerificationResult {
  success: boolean;
  message?: string;
  errors?: Array<{
    code: string;
    message: string;
    location?: string;
  }>;
}

export interface Schema {
  semanticId: string;
  uploadedBy: string;
  schema: Record<string, unknown>;
  createdAt?: string;
}

export const apiClient = {
  async verifyMetamodel(file: File): Promise<VerificationResult> {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch(`${API_BASE_URL}/verify/metamodel`, {
      method: 'POST',
      body: formData,
    });
    
    return response.json();
  },

  async verifyTemplate(file: File): Promise<VerificationResult> {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch(`${API_BASE_URL}/verify/template`, {
      method: 'POST',
      body: formData,
    });
    
    return response.json();
  },

  async verifyInstance(file: File): Promise<VerificationResult> {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch(`${API_BASE_URL}/verify/instance`, {
      method: 'POST',
      body: formData,
    });
    
    return response.json();
  },

  async createSchema(file: File): Promise<VerificationResult> {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch(`${API_BASE_URL}/verify/schema`, {
      method: 'POST',
      body: formData,
    });
    
    return response.json();
  },

  async searchSchemas(params?: { semanticId?: string; uploadedBy?: string }): Promise<Schema[]> {
    const searchParams = new URLSearchParams();
    if (params?.semanticId) searchParams.append('semanticId', params.semanticId);
    if (params?.uploadedBy) searchParams.append('uploadedBy', params.uploadedBy);
    
    const response = await fetch(`${API_BASE_URL}/verify/schema/search?${searchParams}`);
    return response.json();
  },

  async deleteSchema(semanticId: string): Promise<{ success: boolean; message: string }> {
    const response = await fetch(`${API_BASE_URL}/verify/schema/delete/${encodeURIComponent(semanticId)}`, {
      method: 'DELETE',
    });
    
    return response.json();
  },

  async updateSchemaPut(file: File): Promise<VerificationResult> {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch(`${API_BASE_URL}/verify/schema`, {
      method: 'PUT',
      body: formData,
    });
    
    return response.json();
  },

  async updateSchemaPatch(file: File): Promise<VerificationResult> {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch(`${API_BASE_URL}/verify/schema`, {
      method: 'PATCH',
      body: formData,
    });
    
    return response.json();
  },
};
