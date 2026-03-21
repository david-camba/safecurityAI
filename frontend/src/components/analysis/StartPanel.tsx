import { Play } from 'lucide-react';

interface StartPanelProps {
    onStart: () => void;
}

export function StartPanel({ onStart }: StartPanelProps) {
    return (
        <div className="flex flex-col items-center justify-center h-full space-y-6">
            <div className="text-center space-y-2">
                <h2 className="text-2xl text-white tracking-widest">SYSTEM READY</h2>
                <p className="text-gray-400">Awaiting command to initiate SafecurityAI analysis sequence...</p>
            </div>

            <button
                onClick={onStart}
                className="group relative flex items-center px-8 py-4 bg-cyber-bg border-2 border-cyber-accent text-cyber-accent font-bold text-lg uppercase tracking-widest hover:bg-cyber-accent hover:text-cyber-bg transition-all duration-300 shadow-[0_0_15px_rgba(0,255,65,0.2)] hover:shadow-[0_0_25px_rgba(0,255,65,0.5)]"
            >
                <Play className="w-6 h-6 mr-3 group-hover:animate-pulse" />
                Initiate Audit
            </button>
        </div>
    );
}