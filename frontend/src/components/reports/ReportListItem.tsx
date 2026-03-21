import { useState } from 'react';
import { Download, Loader2, AlertCircle, RotateCcw } from 'lucide-react';
import { ReportProcessorInline } from './ReportProcessorInline';
import type { ReportItem, ReportDetailResponse } from '../../types/reports';
import { config } from '../../config/env';

interface ReportListItemProps {
    report: ReportItem;
}

type DownloadStatus = 'idle' | 'downloading' | 'processing' | 'error';

export default function ReportListItem({ report }: ReportListItemProps) {
    const [status, setStatus] = useState<DownloadStatus>('idle');
    const [markdownContent, setMarkdownContent] = useState<string>('');

    const handleDownload = async () => {
        try {
            setStatus('downloading');

            // Fetch report details
            const response = await fetch(`${config.apiUrl}/reports/${report.filename}`);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data: ReportDetailResponse = await response.json();

            setMarkdownContent(data.content);
            setStatus('processing');
        } catch (error) {
            console.error("Report download failed:", error);
            setStatus('error');
        }
    };

    const isSafe = report.status === 'safe';

    return (
        <div className="p-4 bg-cyber-card border border-cyber-border rounded flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 transition-colors hover:border-cyber-accent/30 min-h-[75px]">

            {/* Report Metadata */}
            <div className="flex items-center gap-4">
                {/* Status badge */}
                <div className={`px-3 py-1 text-xs font-bold rounded uppercase tracking-wider
                    ${isSafe
                        ? 'bg-cyber-accent/10 text-cyber-accent border border-cyber-accent/20'
                        : 'bg-cyber-error/10 text-cyber-error border border-cyber-error/20'
                    }`}
                >
                    {report.status}
                </div>

                {/* Timestamp */}
                <div className="flex flex-col">
                    <span className="text-gray-200 font-mono text-sm">{report.date}</span>
                    <span className="text-gray-500 font-mono text-xs">{report.time}</span>
                </div>

                {/* Filename */}
                <div className="hidden md:block text-gray-600 font-mono text-xs truncate max-w-[300px] ml-4">
                    {report.filename}
                </div>
            </div>

            {/* Action Interface */}
            <div className="w-full sm:w-auto flex justify-end font-mono">
                {status === 'idle' && (
                    <button
                        onClick={handleDownload}
                        className="flex items-center gap-2 px-4 py-2 text-sm text-cyber-accent border border-cyber-accent/50 rounded hover:bg-cyber-accent/10 transition-colors"
                    >
                        <Download className="w-4 h-4" />
                        <span>Download</span>
                    </button>
                )}

                {status === 'downloading' && (
                    <div className="flex items-center gap-2 px-4 py-2 text-sm text-gray-400">
                        <Loader2 className="w-4 h-4 animate-spin text-cyber-accent" />
                        <span>Downloading...</span>
                    </div>
                )}

                {status === 'processing' && (
                    <ReportProcessorInline
                        markdownContent={markdownContent}
                        originalFilename={report.filename}
                    />
                )}

                {status === 'error' && (
                    <div className="flex items-center gap-3">
                        <div className="flex items-center gap-2 px-2 py-2 text-sm text-cyber-error">
                            <AlertCircle className="w-4 h-4" />
                            <span>Download failed</span>
                        </div>
                        <button
                            onClick={handleDownload}
                            className="flex items-center gap-2 px-3 py-1.5 text-sm border border-cyber-error text-cyber-error rounded hover:bg-cyber-error/10 transition-colors"
                        >
                            <RotateCcw className="w-4 h-4" />
                            <span>Retry</span>
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
}