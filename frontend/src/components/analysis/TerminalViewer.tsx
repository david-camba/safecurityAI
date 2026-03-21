import { useEffect, useRef, useState } from 'react';
import { Copy, Check } from 'lucide-react';
import type { LogEntry, AnalysisStatus } from '../../types/analysis';

interface TerminalViewerProps {
    logs: LogEntry[];
    status: AnalysisStatus;
}

export function TerminalViewer({ logs, status }: TerminalViewerProps) {
    const bottomRef = useRef<HTMLDivElement>(null);
    const [isCopied, setIsCopied] = useState(false);

    // Auto-scroll to the latest log entry whenever the logs array updates
    useEffect(() => {
        if (status === 'running') {
            bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
        }
    }, [logs, status]);

    // Handler to copy all terminal output to the clipboard
    const handleCopyLogs = async () => {
        try {
            const textToCopy = logs.map(log => `[${log.timestamp}] ${log.content}`).join('\n');
            await navigator.clipboard.writeText(textToCopy);

            // Show visual feedback for 2 seconds
            setIsCopied(true);
            setTimeout(() => setIsCopied(false), 2000);
        } catch (err) {
            console.error('Failed to copy logs:', err);
        }
    };

    return (
        <div className="flex flex-col h-full bg-cyber-bg border border-cyber-border rounded-lg overflow-hidden shadow-inner">
            {/* Terminal Header */}
            <div className="flex items-center justify-between px-4 py-2 bg-cyber-card border-b border-cyber-border">
                <span className="text-xs text-gray-500 uppercase tracking-widest">sys_log_output.exe</span>

                <div className="flex items-center space-x-4">
                    {/* Copy to Clipboard Button */}
                    <button
                        onClick={handleCopyLogs}
                        title="Copy logs to clipboard"
                        className="text-gray-500 hover:text-cyber-accent transition-colors flex items-center focus:outline-none"
                    >
                        {isCopied ? <Check className="w-4 h-4 text-cyber-accent" /> : <Copy className="w-4 h-4" />}
                    </button>

                    {/* Status Indicator */}
                    <div className="flex items-center space-x-2 text-xs">
                        <span className="text-gray-500">STATUS:</span>
                        <span className={`uppercase font-bold ${status === 'error' ? 'text-cyber-error' : 'text-cyber-accent'}`}>
                            {status}
                        </span>
                    </div>
                </div>
            </div>

            {/* Logs Container */}
            <div className="flex-1 p-4 overflow-y-auto font-mono text-sm space-y-1">
                {logs.map((log) => (
                    <div key={log.id} className="flex hover:bg-white/5 transition-colors">
                        <span className="text-gray-500 w-24 flex-shrink-0">[{log.timestamp}]</span>
                        <span className="text-gray-300 break-all">{log.content}</span>
                    </div>
                ))}
                {/* Invisible anchor div for smooth auto-scrolling */}
                <div ref={bottomRef} />
            </div>
        </div>
    );
}