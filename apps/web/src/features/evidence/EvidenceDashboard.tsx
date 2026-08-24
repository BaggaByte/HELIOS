import { useState, useRef } from 'react';
import { Upload, Lock, ShieldCheck, Camera, FileText, Loader2 } from 'lucide-react';
import { useEvidence } from '../../hooks/useEvidence';
import { EvidenceCard } from './EvidenceCard';
import { cn } from '../../lib/utils';

export function EvidenceDashboard() {
  const { evidenceList, isLoading, uploadEvidence, isUploading, error } = useEvidence();
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const [description, setDescription] = useState('');
  const [type, setType] = useState('screenshot');
  const [dragActive, setDragActive] = useState(false);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      await uploadFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      await uploadFile(e.target.files[0]);
    }
  };

  const uploadFile = async (file: File) => {
    try {
      await uploadEvidence({ file, description, type });
      setDescription(''); // Reset after upload
      if (fileInputRef.current) fileInputRef.current.value = '';
    } catch (err) {
      console.error("Upload failed", err);
    }
  };

  return (
    <div className="flex flex-col h-full bg-surface-primary overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-border-default bg-surface-secondary flex-shrink-0">
        <div>
          <h1 className="text-xl font-bold text-gray-100 flex items-center gap-2">
            <Lock className="text-border-active" />
            Evidence Locker
          </h1>
          <p className="text-sm text-gray-400 mt-1">Chain of Custody & Cryptographic Verification</p>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-6 custom-scrollbar flex flex-col md:flex-row gap-6">
        
        {/* Upload Zone (Left Panel) */}
        <div className="w-full md:w-80 flex flex-col gap-4 flex-shrink-0">
          <div className="bg-surface-secondary border border-border-default rounded-xl p-5 shadow-sm">
            <h3 className="font-semibold text-gray-200 mb-4 flex items-center gap-2">
              <Upload size={18} className="text-gray-400" />
              Upload Evidence
            </h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-gray-400 uppercase tracking-wider mb-1">Evidence Type</label>
                <select 
                  value={type}
                  onChange={(e) => setType(e.target.value)}
                  className="w-full bg-surface-tertiary border border-border-default rounded p-2 text-sm text-gray-200 outline-none focus:border-border-active"
                >
                  <option value="screenshot">Screenshot / Image</option>
                  <option value="log_excerpt">Log Excerpt</option>
                  <option value="request_response">Raw HTTP Request</option>
                  <option value="command_output">Command Output</option>
                  <option value="pcap">Network Capture (PCAP)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-gray-400 uppercase tracking-wider mb-1">Description (Optional)</label>
                <textarea 
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="E.g., Proof of SQLi on /login page"
                  className="w-full h-20 bg-surface-tertiary border border-border-default rounded p-2 text-sm text-gray-200 outline-none focus:border-border-active resize-none custom-scrollbar"
                />
              </div>

              <input
                type="file"
                className="hidden"
                ref={fileInputRef}
                onChange={handleFileSelect}
              />
              
              <div 
                className={cn(
                  "border-2 border-dashed rounded-lg p-6 flex flex-col items-center justify-center text-center cursor-pointer transition-colors h-32",
                  dragActive ? "border-border-active bg-border-active/10" : "border-border-default hover:border-gray-500 hover:bg-surface-hover"
                )}
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
              >
                {isUploading ? (
                  <Loader2 className="animate-spin text-gray-400 mb-2" size={24} />
                ) : type === 'screenshot' ? (
                  <Camera className="text-gray-400 mb-2" size={24} />
                ) : (
                  <FileText className="text-gray-400 mb-2" size={24} />
                )}
                <span className="text-sm font-medium text-gray-300">
                  {isUploading ? 'Hashing & Uploading...' : 'Drag & Drop or Click to Upload'}
                </span>
              </div>

              {error && (
                <div className="text-xs text-severity-critical bg-severity-critical/10 p-2 rounded border border-severity-critical/20">
                  {error.message}
                </div>
              )}
            </div>
          </div>

          <div className="bg-surface-secondary border border-border-default rounded-xl p-5 shadow-sm text-xs text-gray-400 space-y-2">
            <h4 className="font-bold text-gray-300 uppercase tracking-wider flex items-center gap-1">
              <ShieldCheck size={14} /> Trust Protocol
            </h4>
            <p>1. Files are instantly hashed (SHA-256) upon upload.</p>
            <p>2. The hash is immutably linked to the Finding.</p>
            <p>3. Files are stored on local disk to prevent DB bloat.</p>
            <p>4. Verify integrity at any time to prove Chain of Custody.</p>
          </div>
        </div>

        {/* Evidence Gallery (Right Panel) */}
        <div className="flex-1">
          {isLoading ? (
            <div className="h-full flex items-center justify-center">
              <Loader2 className="animate-spin text-gray-500" size={32} />
            </div>
          ) : evidenceList && evidenceList.length > 0 ? (
            <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4 auto-rows-max pb-10">
              {evidenceList.map(ev => (
                <EvidenceCard key={ev.id} evidence={ev} />
              ))}
            </div>
          ) : (
            <div className="h-full flex flex-col items-center justify-center text-gray-500 animate-in fade-in">
              <Lock size={48} className="mb-4 opacity-50 text-gray-400" />
              <h3 className="text-xl font-semibold text-gray-300 mb-2">Locker is Empty</h3>
              <p className="text-sm text-center max-w-md">
                Upload screenshots, logs, or raw HTTP requests. They will be cryptographically hashed and stored securely for your final report.
              </p>
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
