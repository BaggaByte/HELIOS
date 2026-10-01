import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { Bot, User, Copy, Check, AlertCircle, Loader2 } from 'lucide-react';
import { cn } from '../../lib/utils';
import { type ChatMessage } from '../../hooks/useChat';

interface MessageBubbleProps {
  message: ChatMessage;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user';
  const isStreaming = message.status === 'streaming';
  const isError = message.status === 'error';

  const [copied, setCopied] = useState(false);

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const displayContent = message.content.replace(/<\|im_end\|>/g, '').replace(/<\|endoftext\|>/g, '');

  return (
    <div className={cn(
      "flex w-full gap-4 p-6 transition-all animate-in fade-in slide-in-from-bottom-2 duration-300 relative",
      isUser ? "bg-transparent" : "bg-surface-secondary/20  border-y border-border-default/20 shadow-[inset_0_1px_0_rgba(255,255,255,0.02)]",
      isError && "bg-severity-critical/5 border-severity-critical/20"
    )}>
      <div className="flex-shrink-0 mt-1 relative z-10">
        {isUser ? (
          <div className="w-8 h-8 rounded-full bg-surface-tertiary/50  flex items-center justify-center border border-border-default shadow-md">
            <User size={18} className="text-gray-300" />
          </div>
        ) : (
          <div className={cn(
            "w-8 h-8 rounded-full flex items-center justify-center border shadow-lg relative",
            isError ? "bg-severity-critical/20 border-severity-critical/50 text-severity-critical" : "bg-border-active/10 border-border-active/50 text-border-active shadow-[0_0_15px_rgb(var(--border-active)/0.3)]"
          )}>
            {/* Ambient glow behind the bot icon */}
            {!isError && <div className="absolute inset-0 bg-border-active blur-md opacity-30 rounded-full" />}
            {isError ? <AlertCircle size={18} /> : <Bot size={18} className="relative z-10" />}
          </div>
        )}
      </div>

      <div className={cn(
        "flex-1 min-w-0 prose prose-invert max-w-none text-gray-200 prose-pre:bg-surface-primary/80 prose-pre: prose-pre:border prose-pre:border-border-default/50 prose-pre:shadow-md relative z-10",
        isStreaming && "streaming-cursor"
      )}>
        {message.agentStatus && (
          <div className="mb-4 flex items-center gap-3 text-sm text-severity-info bg-surface-tertiary/40 border border-border-default/50 rounded-lg p-3 w-fit shadow-md animate-in slide-in-from-top-2 fade-in">
            <Loader2 size={16} className="animate-spin text-border-active" />
            <span className="font-medium tracking-wide">{message.agentStatus}</span>
          </div>
        )}
        
        {displayContent ? (
          <ReactMarkdown
            components={{
              code({ className, children, ...props }: any) {
                const match = /language-(\w+)/.exec(className || '')
                const isInline = props.inline ?? (!match && !String(children).includes('\n'));
                const codeString = String(children).replace(/\n$/, '')

                return !isInline && match ? (
                  <div className="relative group rounded-xl bg-surface-primary/80  border border-border-default/50 my-4 overflow-hidden not-prose shadow-lg transition-all hover:shadow-md hover:border-border-default">
                    <div className="flex items-center justify-between px-4 py-2.5 bg-surface-tertiary/40 border-b border-border-default/50 ">
                      <span className="text-xs text-gray-400 font-mono uppercase tracking-wider">{match[1]}</span>
                      <button
                        onClick={() => handleCopy(codeString)}
                        className="flex items-center gap-1.5 text-xs text-gray-400 hover:text-gray-200 transition-colors"
                      >
                        {copied ? <><Check size={14} className="text-severity-low" /> Copied</> : <><Copy size={14} /> Copy code</>}
                      </button>
                    </div>
                    <pre className="p-4 overflow-x-auto text-sm bg-transparent">
                      <code className={className} {...props}>
                        {children}
                      </code>
                    </pre>
                  </div>
                ) : (
                  <code className="bg-border-active/10 px-1.5 py-0.5 rounded text-sm font-mono text-border-active border border-border-active/20" {...props}>
                    {children}
                  </code>
                )
              },
              p: ({ ...props }) => <p className="mb-4 last:mb-0 leading-relaxed text-gray-300" {...props} />,
              a: ({ ...props }) => <a className="text-border-active hover:text-white hover:underline transition-colors shadow-border-active/20 drop-shadow-sm" target="_blank" rel="noopener noreferrer" {...props} />,
            }}
          >
            {message.content}
          </ReactMarkdown>
        ) : (
          // Fallback loading block if streaming just started and content is empty
          isStreaming && <span className="inline-block w-2 h-4 bg-border-active animate-pulse rounded-sm" />
        )}
      </div>
    </div>
  );
}
