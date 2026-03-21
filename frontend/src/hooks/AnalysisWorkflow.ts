import { useState, useRef, useEffect, useEffectEvent } from 'react';
import { config } from '../config/env';
import type {
    AnalysisStatus,
    LogEntry,
    ActionRequest,
    ServerMessage,
    HumanTextResponse
} from '../types/analysis';

export const useAnalysisWorkflow = () => {
    // --- State Management ---
    const [status, setStatus] = useState<AnalysisStatus>('idle');
    const [logs, setLogs] = useState<LogEntry[]>([]);
    const [currentAction, setCurrentAction] = useState<ActionRequest | null>(null);
    const [finalReport, setFinalReport] = useState<string | null>(null);

    // Connection intent state driving the declarative WebSocket synchronization
    const [isConnecting, setIsConnecting] = useState(false);

    // Mutable reference to the active WebSocket instance
    const socketRef = useRef<WebSocket | null>(null);

    /**
     * Appends a new log entry to the execution trace.
     */
    const appendLog = (content: string) => {
        setLogs((prev) => [
            ...prev,
            {
                id: crypto.randomUUID(),
                timestamp: new Date().toLocaleTimeString(),
                content,
            }
        ]);
    };

    // --- Stable Event Handlers ---

    /**
     * Processes incoming WebSocket messages and transitions the workflow state.
     */
    const onSocketMessage = useEffectEvent((event: MessageEvent) => {
        try {
            const data: ServerMessage = JSON.parse(event.data);

            console.log("⬇️ WS RECV:", data);

            switch (data.type) {
                case 'log':
                    appendLog(data.content);
                    break;

                case 'action_request':
                    setCurrentAction({
                        type: 'action_request',
                        action_type: data.action_type,
                        message: data.message
                    });
                    setStatus('waiting_human');
                    break;

                case 'action_ack':
                    setStatus('running');
                    setCurrentAction(null);
                    appendLog("User input accepted. Resuming analysis...");
                    break;

                case 'complete':
                    setFinalReport(data.report);
                    setStatus('completed');
                    appendLog("Analysis workflow completed successfully.");
                    break;

                case 'error':
                    appendLog(`ERROR: ${data.content}`);
                    break;
            }
        } catch (err) {
            console.error("Failed to parse server message:", err);
        }
    });

    /**
     * Handles the termination of the WebSocket connection.
     * Updates connection state and logs the disconnection event.
     */
    const onSocketClose = useEffectEvent(() => {
        // Log the transport disconnection
        appendLog("Transport disconnected.");

        // Reset connection attempt flag
        setIsConnecting(false);

        // Update status with the latest state from React
        setStatus((prev) => {
            // Preserve terminal states (completed or error) if already set
            if (prev === 'completed' || prev === 'error') {
                return prev;
            }
            // Transition to 'error' if connection was unexpectedly terminated while running
            return 'error';
        });
    });

    // --- Synchronization Effect ---

    /**
     * Declarative WebSocket connection lifecycle management.
     */
    useEffect(() => {
        if (!isConnecting) return;

        const socket = new WebSocket(`${config.wsUrl}/analyze`);
        socketRef.current = socket;

        const connectionTimeout = setTimeout(() => {
            if (socket.readyState !== WebSocket.OPEN) {
                setStatus('error');
                appendLog("Connection timeout. SafecurityAI Backend is unreachable.");
                socket.close(); // Forcefully abort
            }
        }, 5000);

        socket.onopen = () => {
            clearTimeout(connectionTimeout); // We connected! Cancel the timeout
            appendLog("Connection established. Analysis sequence initiated.");
        };

        socket.onmessage = onSocketMessage;
        socket.onerror = () => {
            setStatus('error');
            appendLog("WebSocket transport error occurred.");
        };
        socket.onclose = () => {
            clearTimeout(connectionTimeout);
            onSocketClose();
        };

        // Cleanup function for when intent changes or component unmounts
        return () => {
            clearTimeout(connectionTimeout);
            socket.close();
            socketRef.current = null;
        };
    }, [isConnecting]);

    // --- Public API ---

    /**
     * Initiates the analysis workflow by asserting the connection intent.
     */
    const startAnalysis = () => {
        if (isConnecting) return;

        // Start with a new state
        setStatus('running');
        setFinalReport(null);
        setCurrentAction(null);

        setLogs([{
            id: crypto.randomUUID(),
            timestamp: new Date().toLocaleTimeString(),
            content: "Initializing connection to AI-EDR Backend..."
        }]);

        // Assert intent to connect, which triggers the useEffect to open the WebSocket
        setIsConnecting(true);
    };

    /**
     * Dispatches a human response back to the analyst.
     */
    const submitHumanResponse = (answer: string) => {
        if (!socketRef.current || socketRef.current.readyState !== WebSocket.OPEN) {
            appendLog("Error: Cannot send response. Socket is not connected.");
            return;
        }

        const payload: HumanTextResponse = {
            type: 'human_text_answer',
            answer
        };

        socketRef.current.send(JSON.stringify(payload));
    };

    /**
     * Resets the workflow back to its initial state (e.g., after a critical error).
     */
    const resetWorkflow = () => {
        setStatus('idle');
        setLogs([]);
        setFinalReport(null);
        setCurrentAction(null);
        setIsConnecting(false);
    };

    return {
        status,
        logs,
        currentAction,
        finalReport,
        startAnalysis,
        submitHumanResponse,
        resetWorkflow
    };
};