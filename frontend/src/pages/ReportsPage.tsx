import { FileText, AlertCircle, Loader2 } from 'lucide-react';
import type { ReportsListResponse } from '../types/reports';
import ReportListItem from '../components/reports/ReportListItem';
import { useFetch } from '../hooks/useFetch';

export default function ReportsPage() {
    const { data, isLoading, error, refetch } = useFetch<ReportsListResponse>('/reports');

    const reports = data?.reports || [];

    // Loading state
    if (isLoading) {
        return (
            <div className="flex flex-col items-center justify-center min-h-[50vh] space-y-4">
                <Loader2 className="w-8 h-8 text-cyber-accent animate-spin" />
                <p className="text-gray-400">Retrieving forensic records...</p>
            </div>
        );
    }

    // Error state
    if (error) {
        return (
            <div className="flex flex-col items-center justify-center min-h-[50vh] text-cyber-error space-y-4">
                <AlertCircle className="w-10 h-10" />
                <p>{error}</p>
                <button
                    onClick={() => refetch()}
                    className="px-4 py-2 border border-cyber-error rounded hover:bg-cyber-error/10 transition-colors text-sm"
                >
                    Retry Connection
                </button>
            </div>
        );
    }

    // Main view
    return (
        <div className="h-full flex flex-col p-6 bg-cyber-bg text-gray-300 font-mono">
            {/* Persistent Header: Matching SuggestionsPage Aesthetic */}
            <header className="mb-6 pb-4 border-b border-cyber-border">
                <div className="flex items-center space-x-3">
                    <FileText className="w-6 h-6 text-cyber-accent" />
                    <h1 className="text-2xl text-cyber-accent font-bold tracking-widest uppercase">
                        FORENSIC REPORTS
                    </h1>
                </div>
                <p className="text-gray-500 text-sm mt-2">
                    {reports.length === 0
                        ? 'System status: No forensic data detected in the current directory.'
                        : `${reports.length} analysis reports identified.`}
                </p>
            </header>

            {/* Content Area: Scrollable container */}
            <main className="flex-grow overflow-y-auto pr-2">
                {reports.length === 0 ? (
                    <div className="text-center py-12 border border-dashed border-cyber-border rounded-lg text-gray-500 italic">
                        No analysis reports available at this time.
                    </div>
                ) : (
                    <div className="flex flex-col space-y-3">
                        {reports.map((report) => (
                            <ReportListItem key={report.filename} report={report} />
                        ))}
                    </div>
                )}
            </main>
        </div>
    );
}