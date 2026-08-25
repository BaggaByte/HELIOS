import { useState } from 'react';
import { Download, ShieldCheck, ShieldAlert, FileText } from 'lucide-react';
import type { Evidence } from '../../hooks/useEvidence';
import { useEvidence } from '../../hooks/useEvidence';
import { cn } from '../../lib/utils';
import { useProjectStore } from '../../stores/projectStore';
import { API_BASE_URL } from '../../services/apiClient';

interface Props {
  evidence: Evidence;
}

export function EvidenceCard({ evidence }: Props) {
  const { verifyEvidence } = useEvidence();
  const [isVerifying, setIsVerifying] = useState(false);
  const [verificationResult, setVerificationResult] = useState<{valid: boolean; current?: string; expected?: string} | null>(null);

  const handleVerify = async () => {
    setIsVerifying(true);
    try {
      const result = await verifyEvidence(evidence.id);
      setVerificationResult({
        valid: result.valid,
        current: result.current_hash,
        expected: result.expected_hash
      });
    } catch (err) {
      console.warn('Evidence verification failed:', err);
      setVerificationResult({ valid: false });
    } finally {
      setIsVerifying(false);
    }
  };

  const isImage = evidence.original_filename?.match(/\.(jpg|jpeg|png|gif|webp)$/i);
  const projectId = useProjectStore(state => state.projectId);
  const downloadUrl = `${API_BASE_URL}/projects/${projectId}/evidence/${evidence.id}/download`;

  return (
    <div className="bg-surface-secondary border border-border-default rounded-xl overflow-hidden shadow-sm flex flex-col group transition-all hover:border-border-active">
      {/* Preview Area */}
      <div className="h-48 bg-surface-tertiary border-b border-border-default relative flex items-center justify-center overflow-hidden">
        {isImage ? (
          <img 
            src={downloadUrl} 
            alt={evidence.original_filename} 
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
          />
        ) : (
          <div className="flex flex-col items-center justify-center text-gray-500">
            <FileText size={48} className="mb-2 opacity-50" />
            <span className="text-sm font-mono">{evidence.original_filename}</span>
          </div>
        )}
        
        {/* Hover Actions */}
        <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-4">
          <a 
            href={downloadUrl}
            download={evidence.original_filename}
            className="p-2 bg-surface-secondary text-gray-200 rounded-full hover:bg-border-active hover:text-white transition-colors"
            title="Download Raw File"
          >
            <Download size={20} />
          </a>
        </div>
      </div>

      {/* Details Area */}
      <div className="p-4 flex flex-col gap-3">
        <div className="flex items-start justify-between">
          <div>
            <h3 className="font-semibold text-gray-200 truncate max-w-[200px]" title={evidence.original_filename}>
              {evidence.original_filename}
            </h3>
            <p className="text-xs text-gray-400 mt-0.5">{new Date(evidence.created_at).toLocaleString()}</p>
          </div>
          <span className="px-2 py-0.5 bg-surface-tertiary text-gray-300 text-[10px] font-bold uppercase rounded border border-border-default">
            {evidence.type}
          </span>
        </div>

        {evidence.description && (
          <p className="text-sm text-gray-400 italic line-clamp-2">{evidence.description}</p>
        )}

        {/* Chain of Custody / Integrity Section */}
        <div className="mt-2 pt-3 border-t border-border-default">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold text-gray-500 uppercase">Integrity Status</span>
            {!verificationResult && (
              <button
                onClick={handleVerify}
                disabled={isVerifying}
                className="text-xs bg-surface-tertiary hover:bg-surface-hover text-gray-300 px-2 py-1 rounded border border-border-default transition-colors disabled:opacity-50"
              >
                {isVerifying ? 'Checking...' : 'Verify Hash'}
              </button>
            )}
          </div>

          {verificationResult ? (
            <div className={cn(
              "p-2 rounded flex items-start gap-2 text-xs",
              verificationResult.valid 
                ? "bg-severity-info/10 border border-severity-info/30 text-severity-info" 
                : "bg-severity-critical/10 border border-severity-critical/30 text-severity-critical"
            )}>
              {verificationResult.valid ? <ShieldCheck size={14} className="mt-0.5 shrink-0" /> : <ShieldAlert size={14} className="mt-0.5 shrink-0" />}
              <div>
                <p className="font-bold">{verificationResult.valid ? 'Verified: Chain of Custody Intact' : 'TAMPERED: Hash Mismatch!'}</p>
                <div className="mt-1 font-mono text-[10px] opacity-80 break-all">
                  DB: {evidence.file_hash}
                </div>
              </div>
            </div>
          ) : (
            <div className="font-mono text-[10px] text-gray-500 break-all bg-surface-primary p-2 rounded border border-border-default">
              SHA256: {evidence.file_hash}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
