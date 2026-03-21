import { useQuery } from '@tanstack/react-query';
import { config } from '../config/env';
import SuggestionCard from '../components/suggestions/SuggestionCard';
import type { FeatureSuggestionsResponse } from '../types/suggestions';
import { Lightbulb, AlertCircle, Loader2, RotateCcw } from 'lucide-react';

export default function SuggestionsPage() {
    // React Query for caching, automatic retries, and streamlined async state management
    const { data, isLoading, isError, error, refetch } = useQuery<FeatureSuggestionsResponse>({
        queryKey: ['suggestions'],
        queryFn: async () => {
            const response = await fetch(`${config.apiUrl}/features`);
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        }
    });

    return (
        <div className="h-full flex flex-col p-6 bg-cyber-bg text-gray-300 font-mono">
            {/* Persistent Header */}
            <header className="mb-6 pb-4 border-b border-cyber-border">
                <div className="flex items-center space-x-3">
                    <Lightbulb className="w-6 h-6 text-cyber-accent" />
                    <h1 className="text-2xl text-cyber-accent font-bold tracking-widest">AGENT FEATURE SUGGESTIONS</h1>
                </div>
                <p className="text-gray-500 text-sm mt-2">
                    {isLoading
                        ? 'Analyzing system improvement vectors...'
                        : isError
                            ? 'System analysis aborted due to connection failure.'
                            : `${data?.count ?? 0} new improvement proposals identified.`}
                </p>
            </header>

            {/* Dynamic Content Area */}
            <main className="flex-grow overflow-y-auto pr-2">

                {/* 1. Loading State */}
                {isLoading && (
                    <div className="flex flex-col items-center justify-center h-[50vh] space-y-4">
                        <Loader2 className="w-8 h-8 text-cyber-accent animate-spin" />
                        <p className="text-cyber-accent animate-pulse tracking-widest text-sm">
                            ANALYZING SYSTEM VECTORS...
                        </p>
                    </div>
                )}

                {/* 2. Error Recovery State */}
                {isError && (
                    <div className="flex flex-col items-center justify-center h-[50vh] text-cyber-error space-y-4 animate-in fade-in duration-300">
                        <AlertCircle className="w-10 h-10" />
                        <p className="text-center max-w-md">
                            Failed to retrieve suggestions: {error instanceof Error ? error.message : 'Unknown exception'}
                        </p>
                        <button
                            onClick={() => refetch()}
                            className="flex items-center gap-2 px-4 py-2 mt-2 border border-cyber-error rounded hover:bg-cyber-error/10 transition-colors text-sm font-bold tracking-wider"
                        >
                            <RotateCcw className="w-4 h-4" />
                            RETRY CONNECTION
                        </button>
                    </div>
                )}

                {/* 3. Empty State */}
                {!isLoading && !isError && (!data?.suggestions || data.suggestions.length === 0) && (
                    <div className="text-center py-12 border border-dashed border-cyber-border rounded-lg text-gray-500 italic">
                        No improvement proposals available at this time.
                    </div>
                )}

                {/* 4. Success State: Render Data */}
                {!isLoading && !isError && data?.suggestions && (
                    <div className="space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
                        {data.suggestions.map((suggestion, index) => (
                            <SuggestionCard key={`suggestion-${index}`} suggestion={suggestion} />
                        ))}
                    </div>
                )}

            </main>
        </div>
    );
}