import { useState, useRef, useEffect, useCallback } from 'react';
import { Send, Terminal, Sparkles, Paperclip, File as FileIcon, Loader2 } from 'lucide-react';
import { useLocation } from 'react-router-dom';
import { MessageBubble } from '../../components/chat/MessageBubble';
import { useChat } from '../../hooks/useChat';
import { useFileUpload } from '../../hooks/useFileUpload';
import { cn } from '../../lib/utils';

export function ChatPanel() {
  const location = useLocation();
  const [input, setInput] = useState(() => location.state?.initialPrompt || '');
  const { messages, isConnected, sendUserMessage } = useChat();
  const { uploadFile, isUploading } = useFileUpload();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);

  // Clear navigation state so it doesn't persist on page refresh
  useEffect(() => {
    if (location.state?.initialPrompt) {
      window.history.replaceState({}, document.title);
    }
  }, [location]);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Auto-resize textarea based on content
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [input]);

  const handleFileUpload = useCallback(async (file: File) => {
    const result = await uploadFile(file);
    if (result) {
      // Send a system message indicating file upload
      sendUserMessage(`[System: Uploaded file "${file.name}" to context]`);
    }
  }, [uploadFile, sendUserMessage]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(async (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      await handleFileUpload(file);
    }
  }, [handleFileUpload]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && isConnected) {
      sendUserMessage(input);
      setInput('');
      // Reset textarea height after submit
      if (textareaRef.current) textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e as any);
    }
  };

  const suggestedPrompts = [
    "Analyze the SQL injection vulnerability found in the login portal.",
    "Explain the reverse engineering findings of the malware sample.",
    "Generate a remediation plan for the exposed AWS S3 buckets.",
  ];

  return (
    <div 
      className="flex flex-col h-full relative bg-transparent"
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      {/* Drag Overlay */}
      {isDragging && (
        <div className="absolute inset-0 z-50 bg-bg-primary/80 backdrop-blur-sm border-2 border-dashed border-border-active flex flex-col items-center justify-center rounded-lg m-4">
          <FileIcon size={48} className="text-border-active mb-4 animate-bounce" />
          <h2 className="text-2xl font-semibold text-gray-200">Drop files to upload</h2>
          <p className="text-gray-400 mt-2">Logs, PCAPs, scripts, or reports</p>
        </div>
      )}

      {/* Header */}
      <div className="flex-shrink-0 h-14 border-b border-border-default/50 flex items-center px-6 glass-panel sticky top-0 z-10">
        <Terminal size={20} className="text-border-active mr-3 shadow-[0_0_10px_rgb(var(--border-active))]" />
        <h2 className="text-sm font-semibold text-gray-100 tracking-wide neon-text">HELIOS Offensive Copilot</h2>
        <div className="ml-auto flex items-center gap-2">
          <div className={cn(
            "w-2 h-2 rounded-full shadow-[0_0_8px]",
            isConnected ? 'bg-severity-low shadow-severity-low' : 'bg-severity-critical shadow-severity-critical animate-pulse'
          )} />
          <span className="text-xs font-medium text-gray-400">{isConnected ? 'NPU Active' : 'Disconnected'}</span>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto scroll-smooth">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-gray-400 px-6 animate-in fade-in duration-500">
            <div className="w-16 h-16 rounded-2xl bg-surface-secondary border border-border-default flex items-center justify-center mb-6 shadow-lg">
              <Sparkles size={28} className="text-severity-info" />
            </div>
            <h3 className="text-xl font-semibold text-gray-100 mb-2">How can I assist your operation?</h3>
            <p className="text-sm text-gray-500 mb-8 text-center max-w-md">
              I can analyze vulnerabilities, write exploits, summarize recon data, or explain complex malware behavior.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 max-w-3xl w-full">
              {suggestedPrompts.map((prompt, i) => (
                <button
                  key={i}
                  onClick={() => {
                    setInput(prompt);
                    textareaRef.current?.focus();
                  }}
                  className="text-left p-4 rounded-xl border border-border-default/50 bg-surface-secondary/40 backdrop-blur hover:bg-surface-tertiary/60 hover:border-border-active/50 transition-all text-sm text-gray-300 shadow-lg hover:-translate-y-1 hover:shadow-xl hover:shadow-border-active/10 duration-300"
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="pb-4">
            {messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} />
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="flex-shrink-0 p-4 glass-panel border-t border-border-default/50 relative mt-auto">
        <form onSubmit={handleSubmit} className="relative max-w-4xl mx-auto">
          {isUploading && (
            <div className="absolute -top-8 left-0 flex items-center gap-2 text-xs text-border-active glass-panel px-3 py-1.5 rounded-full border border-border-default animate-slide-up">
              <Loader2 size={12} className="animate-spin" /> Uploading and encrypting file...
            </div>
          )}
          <div className={cn(
            "flex items-end gap-2 bg-surface-secondary/40 backdrop-blur rounded-2xl transition-all duration-300 shadow-lg",
            isConnected ? "border border-border-default/50 focus-within:border-border-active focus-within:bg-surface-tertiary/40 focus-within:shadow-[0_0_15px_rgb(var(--border-active)/0.2)]" : "border border-severity-critical/50 bg-severity-critical/5"
          )}>
            <input 
              type="file" 
              ref={fileInputRef} 
              className="hidden" 
              onChange={(e) => {
                if (e.target.files && e.target.files[0]) {
                  handleFileUpload(e.target.files[0]);
                }
              }} 
            />
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              disabled={!isConnected || isUploading}
              className="flex-shrink-0 m-2 p-2.5 rounded-lg text-gray-400 hover:text-gray-200 hover:bg-surface-tertiary disabled:opacity-30 transition-all"
              title="Attach File"
            >
              <Paperclip size={18} />
            </button>
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={isConnected ? "Ask HELIOS to analyze an exploit or explain a finding..." : "System offline..."}
              className="flex-1 bg-transparent border-none pl-1 pr-2 py-3.5 text-sm text-gray-200 placeholder:text-gray-500 focus:outline-none resize-none min-h-[52px] max-h-48"
              rows={1}
              disabled={!isConnected}
            />
            <button
              type="submit"
              disabled={!input.trim() || !isConnected}
              className="flex-shrink-0 m-2 p-2.5 rounded-lg bg-severity-info text-bg-primary hover:opacity-90 disabled:opacity-30 disabled:bg-surface-tertiary disabled:text-gray-500 transition-all shadow-sm"
            >
              <Send size={16} />
            </button>
          </div>
        </form>
        <div className="text-center mt-3">
          <span className="text-xs text-gray-500">
            HELIOS uses Phi-4-mini running locally. No data leaves your machine.
          </span>
        </div>
      </div>
    </div>
  );
}