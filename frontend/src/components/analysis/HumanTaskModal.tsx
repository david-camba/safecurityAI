import { useState, FormEvent } from 'react';
import { AlertTriangle, Send } from 'lucide-react';
import type { ActionRequest } from '../../types/analysis';

interface HumanTaskModalProps {
    actionPayload: ActionRequest;
    onSubmit: (answer: string) => void;
}

export function HumanTaskModal({ actionPayload, onSubmit }: HumanTaskModalProps) {
    const [inputValue, setInputValue] = useState('');

    const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        if (!inputValue.trim()) return;

        onSubmit(inputValue);
    };

    return (
        // Fixed to lock to the viewport, bypassing parent relative scopes
        <div className="fixed inset-0 bg-cyber-bg/85 backdrop-blur-sm z-50 flex items-center justify-center">

            <div className="bg-cyber-card border border-cyber-accent p-6 rounded-lg max-w-lg w-full shadow-[0_0_40px_rgba(0,255,65,0.15)] animate-in fade-in zoom-in duration-200">
                <div className="flex items-center text-cyber-accent mb-4 border-b border-cyber-border pb-3">
                    <AlertTriangle className="w-6 h-6 mr-3 animate-pulse" />
                    <h3 className="text-lg font-bold tracking-widest">SYSTEM HALTED: HUMAN INPUT REQUIRED</h3>
                </div>

                <p className="text-gray-300 mb-6 font-mono text-sm border-l-2 border-cyber-accent pl-4 py-1 bg-cyber-bg/50 rounded-r">
                    {actionPayload.message}
                </p>

                <form onSubmit={handleSubmit} className="space-y-4">
                    {actionPayload.action_type === 'text_input' && (
                        <div>
                            <input
                                type="text"
                                autoFocus
                                value={inputValue}
                                onChange={(e) => setInputValue(e.target.value)}
                                placeholder="Type your response here..."
                                className="w-full bg-cyber-bg border border-cyber-border rounded px-4 py-3 text-white font-mono focus:outline-none focus:border-cyber-accent focus:ring-1 focus:ring-cyber-accent transition-all"
                            />
                        </div>
                    )}

                    {actionPayload.action_type === 'file_upload' && (
                        <div className="border-2 border-dashed border-cyber-border p-8 text-center text-gray-500 font-mono">
                            [FUTURE EXTENSION: File Dropzone goes here]
                        </div>
                    )}

                    <div className="flex justify-end pt-2">
                        <button
                            type="submit"
                            disabled={!inputValue.trim() && actionPayload.action_type === 'text_input'}
                            className="flex items-center px-6 py-2 bg-cyber-accent/10 text-cyber-accent border border-cyber-accent hover:bg-cyber-accent hover:text-cyber-bg disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-bold tracking-wider rounded"
                        >
                            <Send className="w-4 h-4 mr-2" />
                            TRANSMIT
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}