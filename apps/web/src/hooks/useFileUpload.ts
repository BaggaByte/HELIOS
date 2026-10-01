import { useState, useCallback } from 'react';
import { apiClient } from '../services/apiClient';
import { useProjectStore } from '../stores/projectStore';

export function useFileUpload(url?: string) {
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const projectId = useProjectStore(state => state.activeProjectId);

  const uploadFile = useCallback(async (file: File) => {
    setIsUploading(true);
    setUploadProgress(0);
    setUploadError(null);

    if (!url && !projectId) {
      setUploadError('Create or select a project before uploading files.');
      setIsUploading(false);
      return null;
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
      // For real progress tracking we'd use XMLHttpRequest, but fetch is fine for now
      // as local uploads are near instantaneous

      const result = await apiClient.post<any>(
        url ? url : `/projects/${projectId}/files/upload`,
        formData
      );

      setUploadProgress(100);
      setIsUploading(false);
      return result;
    } catch (error: any) {
      console.error('File upload error:', error);
      setUploadError(error.message);
      setIsUploading(false);
      return null;
    }
  }, [url, projectId]);

  return { uploadFile, isUploading, uploadProgress, uploadError };
}
