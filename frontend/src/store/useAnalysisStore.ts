import { create } from 'zustand';
import { config } from '../config/env';
import type {
    AnalysisStatus,
    LogEntry,
    ActionRequest,
    ServerMessage,
    HumanTextResponse
} from '../types/analysis';

interface AnalysisStore {
    status: AnalysisStatus;
    logs: LogEntry[];
    currentAction: ActionRequest | null;
    finalReport: string | null;
    socket: WebSocket | null;

    appendLog: (content: string) => void;
    startAnalysis: () => void;
    submitHumanResponse: (answer: string) => void;
    resetWorkflow: (restart?: boolean) => void;
}

export const useAnalysisStore = create<AnalysisStore>((set, get) => ({
    status: 'idle',
    logs: [],
    currentAction: null,
    finalReport: null,
    socket: null,

    appendLog: (content: string) => {
        set((state) => ({
            logs: [
                ...state.logs,
                {
                    id: crypto.randomUUID(),
                    timestamp: new Date().toLocaleTimeString(),
                    content,
                }
            ]
        }));
    },

    startAnalysis: () => {
        const { status, socket: existingSocket, appendLog } = get();

        // Prevent multiple connections
        if (status === 'running' || status === 'waiting_human') return;

        if (existingSocket) existingSocket.close();

        set({
            status: 'running',
            finalReport: null,
            currentAction: null,
            logs: [{
                id: crypto.randomUUID(),
                timestamp: new Date().toLocaleTimeString(),
                content: "Initializing connection to AI-EDR Backend..."
            }]
        });

        const socket = new WebSocket(`${config.wsUrl}/analyze`);
        set({ socket });

        const connectionTimeout = setTimeout(() => {
            if (socket.readyState !== WebSocket.OPEN) {
                set({ status: 'error' });
                appendLog("Connection timeout. SafecurityAI Backend is unreachable.");
                socket.close();
            }
        }, 5000);

        socket.onopen = () => {
            clearTimeout(connectionTimeout);
            appendLog("Connection established. Analysis sequence initiated.");
        };

        socket.onmessage = (event: MessageEvent) => {
            try {
                const data: ServerMessage = JSON.parse(event.data);
                console.log("⬇️ WS RECV:", data);

                switch (data.type) {
                    case 'log':
                        appendLog(data.content);
                        break;
                    case 'action_request':
                        set({
                            currentAction: {
                                type: 'action_request',
                                action_type: data.action_type,
                                message: data.message
                            },
                            status: 'waiting_human'
                        });
                        break;
                    case 'action_ack':
                        set({ status: 'running', currentAction: null });
                        appendLog("User input accepted. Resuming analysis...");
                        break;
                    case 'complete':
                        set({ finalReport: data.report, status: 'completed' });
                        appendLog("Analysis workflow completed successfully.");
                        socket.close(); // Clean up on expected completion
                        set({ socket: null });
                        break;
                    case 'error':
                        appendLog(`ERROR: ${data.content}`);
                        set({ status: 'error' });
                        break;
                }
            } catch (err) {
                console.error("Failed to parse server message:", err);
            }
        };

        socket.onclose = () => {
            clearTimeout(connectionTimeout);
            const currentStatus = get().status;
            appendLog("Transport disconnected.");

            if (currentStatus !== 'completed' && currentStatus !== 'error') {
                set({ status: 'error' });
            }
            set({ socket: null });
        };
    },

    submitHumanResponse: (answer: string) => {
        const { socket, appendLog } = get();
        if (!socket || socket.readyState !== WebSocket.OPEN) {
            appendLog("Error: Cannot send response. Socket is not connected.");
            return;
        }

        const payload: HumanTextResponse = {
            type: 'human_text_answer',
            answer
        };

        socket.send(JSON.stringify(payload));
    },

    resetWorkflow: (restart = true) => {
        const { socket } = get();
        if (socket) {
            socket.onmessage = null;
            socket.onclose = null;
            socket.onerror = null;
            socket.close();
        }
        set({
            status: 'idle',
            logs: [],
            finalReport: null,
            currentAction: null,
            socket: null
        });
        if (restart) {
            get().startAnalysis();
        }
    }
}));