// import { useAnalysisWorkflow } from '../hooks/AnalysisWorkflow'; //DEPRECATED
import { useAnalysisStore } from '../store/useAnalysisStore';
import { StartPanel } from '../components/analysis/StartPanel';
import { TerminalViewer } from '../components/analysis/TerminalViewer';
import { HumanTaskModal } from '../components/analysis/HumanTaskModal';
import { ReportProcessor } from '../components/reports/ReportProcessor';
import { RefreshCw, Terminal } from 'lucide-react';
import { useEffect, useRef } from 'react';

export default function AnalysisPage() {
    // Workflow state management
    /*const {
        status,
        logs,
        currentAction,
        finalReport,
        startAnalysis,
        submitHumanResponse,
        //resetWorkflow
    } = useAnalysisWorkflow();*/

    const {
        status,
        logs,
        currentAction,
        finalReport,
        startAnalysis,
        submitHumanResponse,
        resetWorkflow
    } = useAnalysisStore();

    const reportRef = useRef<HTMLDivElement>(null);
    // Init as "true" to avoid unwanted scrolls when returning to the tab
    const hasScrolledRef = useRef(true);

    useEffect(() => {
        if (status === 'completed' && finalReport && !hasScrolledRef.current) {
            // Delay slightly to ensure DOM is fully painted before scrolling
            setTimeout(() => {
                reportRef.current?.scrollIntoView({ behavior: 'smooth' });
            }, 100);
            hasScrolledRef.current = true; // Lock scrolling for this session
        } else if (status !== 'completed') {
            hasScrolledRef.current = false; // Reset lock for future analysis
        }
    }, [status, finalReport]);

    return (
        <div className="h-full flex flex-col p-6 relative">

            {/* Header section */}
            <header className="mb-6 flex justify-between items-end">
                <div>
                    <div className="flex items-center space-x-3">
                        <Terminal className="w-6 h-6 text-cyber-accent" />
                        <h1 className="text-2xl text-cyber-accent font-bold tracking-widest">LIVE ANALYSIS TERMINAL</h1>
                    </div>
                    <p className="text-gray-500 text-sm mt-1">Real-time telemetry and AI-EDR execution trace</p>
                </div>
            </header>

            {/* Error recovery handler */}
            {status === 'error' && (
                <div className="absolute top-6 right-6 z-10 animate-in fade-in">
                    <button
                        onClick={startAnalysis}
                        className="flex items-center px-4 py-2 bg-cyber-error/10 border border-cyber-error text-cyber-error hover:bg-cyber-error hover:text-white transition-colors text-sm font-bold tracking-wider rounded shadow-[0_0_15px_rgba(255,49,49,0.3)]"
                    >
                        <RefreshCw className="w-4 h-4 mr-2" />
                        RESET CONNECTION
                    </button>
                </div>
            )}

            {/* Post-analysis reset handler */}
            {status === 'completed' && (
                <div className="absolute top-6 right-6 z-10 animate-in fade-in">
                    <button
                        onClick={() => resetWorkflow()}
                        className="flex items-center px-4 py-2 bg-cyber-accent/10 border border-cyber-accent text-cyber-accent hover:bg-cyber-accent hover:text-cyber-bg transition-colors text-sm font-bold tracking-wider rounded shadow-[0_0_15px_rgba(0,255,65,0.3)]"
                    >
                        <RefreshCw className="w-4 h-4 mr-2" />
                        NEW ANALYSIS
                    </button>
                </div>
            )}

            {/* Main state-driven view container */}
            <main className="flex-1 relative">

                {/* Initial state view */}
                {status === 'idle' && (
                    <StartPanel onStart={startAnalysis} />
                )}

                {/* Active session log viewer */}
                {status !== 'idle' && (
                    <TerminalViewer logs={logs} status={status} />
                )}
            </main>

            {/* Human intervention modal */}
            {status === 'waiting_human' && currentAction && (
                <HumanTaskModal
                    actionPayload={currentAction}
                    onSubmit={submitHumanResponse}
                />
            )}

            {/* Post-analysis report processing */}
            {status === 'completed' && finalReport && (
                <div ref={reportRef}>
                    <ReportProcessor report={finalReport} />
                </div>
            )}
        </div>
    );
}