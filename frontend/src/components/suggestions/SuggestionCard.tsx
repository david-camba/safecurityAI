import { useState } from 'react';
import { Copy, Check } from 'lucide-react';
import type { FeatureSuggestion } from '../../types/suggestions';

interface SuggestionCardProps {
    suggestion: FeatureSuggestion;
}

export default function SuggestionCard({ suggestion }: SuggestionCardProps) {
    const [copied, setCopied] = useState(false);

    const handleCopy = async () => {
        const textToCopy = `Feature: ${suggestion.feature}\nReason: ${suggestion.reason}`;
        await navigator.clipboard.writeText(textToCopy);

        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    return (
        <div
            onClick={handleCopy}
            className="group relative bg-cyber-card border border-cyber-border rounded-lg p-4 mb-4 transition-all hover:border-cyber-accent cursor-pointer overflow-hidden"
        >
            {/* Header: Metadata */}
            <div className="flex justify-between items-center text-xs text-gray-500 mb-3 pb-2 border-b border-cyber-border">
                <span>{suggestion.date}</span>
                <span>{suggestion.time}</span>
            </div>

            {/* Content */}
            <div className="space-y-3">
                <div>
                    <h3 className="text-cyber-accent font-bold text-sm tracking-wider">FEATURE</h3>
                    <p className="text-gray-300 text-sm">{suggestion.feature}</p>
                </div>
                <div>
                    <h3 className="text-cyber-accent font-bold text-sm tracking-wider">REASON</h3>
                    <p className="text-gray-400 text-sm">{suggestion.reason}</p>
                </div>
            </div>

            {/* Action Icons: Stacked for smooth transition */}
            <div className="absolute bottom-3 right-3 w-4 h-4">
                {/* Copy Icon: Visible only on hover and when not copied */}
                <Copy
                    className={`absolute inset-0 w-full h-full text-cyber-accent transition-opacity duration-300 
                    ${copied ? 'opacity-0' : 'opacity-0 group-hover:opacity-100'}`}
                />

                {/* Check Icon: Persistent while 'copied' state is true */}
                <Check
                    className={`absolute inset-0 w-full h-full text-green-500 transition-opacity duration-300 
                    ${copied ? 'opacity-100' : 'opacity-0'}`}
                />
            </div>
        </div>
    );
}