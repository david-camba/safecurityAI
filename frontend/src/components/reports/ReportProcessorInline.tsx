import { FileDown, Loader2, AlertCircle, RotateCcw } from 'lucide-react';
import { PdfGeneratorProvider } from './PdfGeneratorProvider';

interface ReportProcessorInlineProps {
    markdownContent: string;
    originalFilename: string;
}

export function ReportProcessorInline({ markdownContent, originalFilename }: ReportProcessorInlineProps) {
    // Generate PDF filename based on source name and current date
    const baseName = originalFilename.replace(/\.[^/.]+$/, "");
    const finalFilename = `${baseName || 'Report'}_${new Date().toISOString().split('T')[0]}.pdf`;

    return (
        <PdfGeneratorProvider report={markdownContent} filename={finalFilename}>
            {/* MODIFICATION: Destructured 'retry' from the provider */}
            {({ status, openPdf, retry }) => (
                <div className="flex items-center animate-in fade-in duration-300">
                    {status === 'processing' && (
                        <div className="flex items-center gap-2 px-4 py-2 text-sm text-cyber-accent/80 font-mono">
                            <Loader2 className="w-4 h-4 animate-spin text-cyber-accent" />
                            <span>Generating PDF...</span>
                        </div>
                    )}

                    {status === 'ready' && (
                        <button
                            onClick={openPdf}
                            className="flex items-center gap-2 px-4 py-2 text-sm text-cyber-bg bg-cyber-accent border border-cyber-accent rounded hover:bg-cyber-accent/90 transition-all font-bold shadow-[0_0_10px_rgba(0,255,65,0.2)] hover:shadow-[0_0_15px_rgba(0,255,65,0.4)]"
                        >
                            <FileDown className="w-4 h-4" />
                            <span>Open PDF</span>
                        </button>
                    )}

                    {/* Fallback UI for PDF conversion errors */}
                    {status === 'error' && (
                        <div className="flex items-center gap-2 px-2 py-1">
                            <AlertCircle className="w-4 h-4 text-cyber-error" />
                            <span className="text-sm text-cyber-error/80 font-mono mr-2">PDF Error</span>
                            <button
                                onClick={retry}
                                className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-cyber-error border border-cyber-error rounded hover:bg-cyber-error/10 transition-colors font-mono"
                            >
                                <RotateCcw className="w-3 h-3" />
                                <span>Retry</span>
                            </button>
                        </div>
                    )}
                </div>
            )}
        </PdfGeneratorProvider>
    );
}