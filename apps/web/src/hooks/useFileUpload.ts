import { useState, useCallback } from 'react';
import { useProjectStore } from '../stores/projectStore';
import { API_BASE_URL } from '../services/apiClient';

export function useFileUpload(customUrl?: string) {
  const projectId = useProjectStore(state => state.projectId);
  const url = customUrl || (projectId ? `${API_BASE_URL}/projects/${projectId}/files/upload` : '');
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const uploadFile = useCallback(async (file: File) => {
    setIsUploading(true);
    setUploadProgress(0);
    setUploadError(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      // For real progress tracking we'd use XMLHttpRequest, but fetch is fine for now
      // as local uploads are near instantaneous
      const response = await fetch(url, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Upload failed with status ${response.status}`);
      }

      const result = await response.json();
      setUploadProgress(100);
      setIsUploading(false);
      return result;
    } catch (error: any) {
      console.error('File upload error:', error);
      setUploadError(error.message);
      setIsUploading(false);
      return null;
    }
  }, [url]);

  return { uploadFile, isUploading, uploadProgress, uploadError };
}
