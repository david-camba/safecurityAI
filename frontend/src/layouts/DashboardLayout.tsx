import { useState, useEffect } from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import { Terminal, FileText, Lightbulb } from 'lucide-react';
import { config } from '../config/env';
import logoImg from '../assets/Safecurity.png';

type SystemStatus = 'ONLINE' | 'OFFLINE' | 'VERIFYING';

export default function DashboardLayout() {
    const [systemStatus, setSystemStatus] = useState<SystemStatus>('VERIFYING');

    // Health check polling
    useEffect(() => {
        const checkBackendStatus = async () => {
            try {
                // Artificial 3-second delay for UX 
                await new Promise(resolve => setTimeout(resolve, 3000));

                const response = await fetch(`${config.apiUrl}/health-check`, {
                    signal: AbortSignal.timeout(5000)
                });

                setSystemStatus(response.ok ? 'ONLINE' : 'OFFLINE');
            } catch {
                setSystemStatus('OFFLINE');
            }
        };

        checkBackendStatus();
        const intervalId = setInterval(checkBackendStatus, 30000);

        return () => clearInterval(intervalId);
    }, []);

    // UI state mapper
    const getStatusConfig = () => {
        switch (systemStatus) {
            case 'ONLINE':
                return { color: 'text-cyber-accent', bg: 'bg-cyber-accent', glow: 'drop-shadow-[0_0_8px_rgba(0,255,65,0.8)]' };
            case 'OFFLINE':
                return { color: 'text-red-500', bg: 'bg-red-500', glow: 'drop-shadow-[0_0_8px_rgba(239,68,68,0.8)]' };
            case 'VERIFYING':
            default:
                return { color: 'text-yellow-500 animate-pulse', bg: 'bg-yellow-500 animate-pulse', glow: '' };
        }
    };

    const statusConfig = getStatusConfig();

    return (
        <div className="min-h-screen bg-cyber-bg text-gray-300 font-mono flex">

            {/* Sidebar Navigation */}
            <aside className="w-64 border-r border-cyber-border bg-cyber-card flex flex-col">

                {/* Brand Header */}
                <div className="h-16 flex items-center px-6 border-b border-cyber-border bg-black">
                    <img src={logoImg} alt="Safecurity Logo" className="w-10 h-10 mr-3 flex-shrink-0 object-contain ml-[-4px]" />
                    <span className="text-lg font-bold text-white tracking-widest leading-none translate-y-[2px]">
                        SAFECURITY.AI
                    </span>
                </div>

                {/* Navigation Links */}
                <nav className="flex-1 p-4 space-y-2">
                    <NavLink
                        to="/"
                        className={({ isActive }) =>
                            `flex items-center px-4 py-3 rounded border transition-all duration-200 ${isActive
                                ? 'bg-cyber-bg text-cyber-accent border-cyber-accent/30 shadow-[0_0_10px_rgba(0,255,65,0.1)]'
                                : 'border-transparent hover:bg-cyber-bg/50 hover:text-white'
                            }`
                        }
                    >
                        <Terminal className="w-5 h-5 mr-3" />
                        Live Analysis
                    </NavLink>

                    <NavLink
                        to="/reports"
                        className={({ isActive }) =>
                            `flex items-center px-4 py-3 rounded border transition-all duration-200 ${isActive
                                ? 'bg-cyber-bg text-cyber-accent border-cyber-accent/30 shadow-[0_0_10px_rgba(0,255,65,0.1)]'
                                : 'border-transparent hover:bg-cyber-bg/50 hover:text-white'
                            }`
                        }
                    >
                        <FileText className="w-5 h-5 mr-3" />
                        Audit Reports
                    </NavLink>

                    <NavLink
                        to="/suggestions"
                        className={({ isActive }) =>
                            `flex items-center px-4 py-3 rounded border transition-all duration-200 ${isActive
                                ? 'bg-cyber-bg text-cyber-accent border-cyber-accent/30 shadow-[0_0_10px_rgba(0,255,65,0.1)]'
                                : 'border-transparent hover:bg-cyber-bg/50 hover:text-white'
                            }`
                        }
                    >
                        <Lightbulb className="w-5 h-5 mr-3" />
                        Suggestions
                    </NavLink>
                </nav>

                {/* System Status Footer */}
                <div className="p-4 border-t border-cyber-border text-xs text-gray-600 flex items-center justify-center gap-2">
                    <span>SYSTEM STATUS:</span>
                    <div className={`w-2 h-2 rounded-full ${statusConfig.bg} ${statusConfig.glow}`} />
                    <span className={`font-bold transition-colors duration-300 ${statusConfig.color}`}>
                        {systemStatus}
                    </span>
                </div>
            </aside>

            {/* Main Content Area */}
            <main className="flex-1 flex flex-col h-screen overflow-hidden">
                <div className="flex-1 overflow-y-auto">
                    <Outlet />
                </div>
            </main>

        </div>
    );
}