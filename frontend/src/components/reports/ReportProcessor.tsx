// MODIFICATION: Imported RotateCcw and AlertCircle
import { FileDown, Loader2, RotateCcw } from 'lucide-react';
import { PdfGeneratorProvider } from './PdfGeneratorProvider';

interface ReportProcessorProps {
    report: string;
}

export function ReportProcessor({ report }: ReportProcessorProps) {
    const finalFilename = `SafecurityAI_Audit_Report_${new Date().toISOString().split('T')[0]}.pdf`;

    return (
        <PdfGeneratorProvider report={report} filename={finalFilename}>
            {/* MODIFICATION: Destructured 'retry' from the provider */}
            {({ status, openPdf, retry }) => (
                <div className="my-4 p-4 border border-cyber-border bg-cyber-card rounded-lg flex justify-between items-center animate-in fade-in slide-in-from-bottom-4 duration-500">

                    <span className={`font-bold tracking-widest flex items-center ${status === 'error' ? 'text-cyber-error' : 'text-cyber-accent'}`}>
                        {status === 'processing' && 'SYSTEM: COMPILING REPORT DATA...'}
                        {status === 'ready' && 'SYSTEM: ANALYSIS COMPLETED SUCCESSFULLY.'}
                        {status === 'error' && 'SYSTEM: CRITICAL ERROR IN PDF COMPILATION.'}
                    </span>

                    <div className="flex items-center">
                        {status === 'processing' && (
                            <div className="flex items-center px-6 py-2 text-cyber-accent font-mono text-sm opacity-80">
                                <Loader2 className="w-5 h-5 mr-3 animate-spin" />
                                GENERATING PDF...
                            </div>
                        )}
                        {/* Open PDF button when ready */}
                        {status === 'ready' && (
                            <button
                                onClick={openPdf}
                                className="flex items-center px-6 py-2 bg-cyber-accent/10 border border-cyber-accent text-cyber-accent font-bold hover:bg-cyber-accent hover:text-cyber-bg transition-all tracking-wider shadow-[0_0_15px_rgba(0,255,65,0.1)] hover:shadow-[0_0_25px_rgba(0,255,65,0.4)]"
                            >
                                <FileDown className="w-5 h-5 mr-3" />
                                OPEN PDF
                            </button>
                        )}

                        {/* Retry block for generation failure */}
                        {status === 'error' && (
                            <button
                                onClick={retry}
                                className="flex items-center px-6 py-2 bg-cyber-error/10 border border-cyber-error text-cyber-error font-bold hover:bg-cyber-error hover:text-white transition-all tracking-wider shadow-[0_0_15px_rgba(255,0,0,0.1)]"
                            >
                                <RotateCcw className="w-5 h-5 mr-3" />
                                RETRY GENERATION
                            </button>
                        )}
                    </div>

                </div>
            )}
        </PdfGeneratorProvider>
    );
}