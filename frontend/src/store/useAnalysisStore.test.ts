import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { useAnalysisStore } from './useAnalysisStore'; // Adjust the import path

// eslint-disable-next-line @typescript-eslint/no-explicit-any
let mockWebSocketInstance: any = null;

class MockWebSocket {
    static CONNECTING = 0;
    static OPEN = 1;
    static CLOSING = 2;
    static CLOSED = 3;

    send = vi.fn();
    close = vi.fn();
    readyState = MockWebSocket.OPEN;

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    onopen: any = null;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    onmessage: any = null;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    onerror: any = null;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    onclose: any = null;

    constructor() {
        // Expose the internal instance to trigger events from the test
        // eslint-disable-next-line @typescript-eslint/no-this-alias
        mockWebSocketInstance = this;
    }
}

describe('useAnalysisStore', () => {
    // Capture the initial state to reset the store between tests
    const initialStoreState = useAnalysisStore.getState();

    beforeEach(() => {
        mockWebSocketInstance = null;
        vi.stubGlobal('WebSocket', MockWebSocket);

        // Reset store state to guarantee test isolation
        useAnalysisStore.setState(initialStoreState, true);
    });

    afterEach(() => {
        vi.unstubAllGlobals();
        vi.useRealTimers();
    });

    it('should start with idle state and no logs', () => {
        const state = useAnalysisStore.getState();

        expect(state.status).toBe('idle');
        expect(state.logs).toEqual([]);
    });

    it('should change to running and register the connection attempt when starting', () => {
        useAnalysisStore.getState().startAnalysis();

        let state = useAnalysisStore.getState();
        expect(state.status).toBe('running');
        expect(state.logs[0].content).toContain('Initializing connection');

        // Simulate successful transport connection
        mockWebSocketInstance.onopen();

        state = useAnalysisStore.getState();
        expect(state.logs[1].content).toContain('Connection established');
    });

    it('should ask for human intervention when receiving an action_request', () => {
        useAnalysisStore.getState().startAnalysis();

        // Dispatch simulated backend request
        mockWebSocketInstance.onmessage({
            data: JSON.stringify({
                type: 'action_request',
                action_type: 'text_input',
                message: 'Please provide the decryption key'
            })
        } as MessageEvent);

        const state = useAnalysisStore.getState();
        expect(state.status).toBe('waiting_human');
        expect(state.currentAction?.message).toBe('Please provide the decryption key');
    });

    it('appends log entries when receiving a log message', () => {
        useAnalysisStore.getState().startAnalysis();

        mockWebSocketInstance.onmessage({
            data: JSON.stringify({ type: 'log', content: 'Scanning memory space...' })
        } as MessageEvent);

        const state = useAnalysisStore.getState();
        expect(state.logs).toHaveLength(2); // 1 init + 1 incoming log
        expect(state.logs[1].content).toBe('Scanning memory space...');
    });

    it('transmits human response and resumes workflow on acknowledgment', () => {
        const store = useAnalysisStore.getState();
        store.startAnalysis();

        mockWebSocketInstance.onmessage({
            data: JSON.stringify({
                type: 'action_request',
                action_type: 'text_input',
                message: 'Auth required'
            })
        } as MessageEvent);

        // Transmit analyst input
        useAnalysisStore.getState().submitHumanResponse('admin123');

        expect(mockWebSocketInstance.send).toHaveBeenCalledWith(
            JSON.stringify({ type: 'human_text_answer', answer: 'admin123' })
        );

        // Acknowledge input reception
        mockWebSocketInstance.onmessage({
            data: JSON.stringify({ type: 'action_ack', accepted_action: 'admin123' })
        } as MessageEvent);

        const state = useAnalysisStore.getState();
        expect(state.status).toBe('running');
        expect(state.currentAction).toBeNull();
        expect(state.logs.some(l => l.content.includes('User input accepted'))).toBe(true);
    });

    it('transitions to completed state and stores final report', () => {
        useAnalysisStore.getState().startAnalysis();

        mockWebSocketInstance.onmessage({
            data: JSON.stringify({ type: 'complete', report: '# Final Audit' })
        } as MessageEvent);

        const state = useAnalysisStore.getState();
        expect(state.status).toBe('completed');
        expect(state.finalReport).toBe('# Final Audit');
    });

    it('handles unexpected WebSocket closure', () => {
        useAnalysisStore.getState().startAnalysis();

        mockWebSocketInstance.onclose();

        const state = useAnalysisStore.getState();
        expect(state.status).toBe('error');
        expect(state.logs.some(l => l.content.includes('Transport disconnected'))).toBe(true);
    });

    it('aborts connection and sets error if timeout is reached', () => {
        vi.useFakeTimers();
        useAnalysisStore.getState().startAnalysis();

        // Simulate unresolved connection attempt
        mockWebSocketInstance.readyState = MockWebSocket.CONNECTING;

        // Advance past the 5000ms threshold
        vi.advanceTimersByTime(5000);

        const state = useAnalysisStore.getState();
        expect(state.status).toBe('error');
        expect(state.logs.some(l => l.content.includes('Connection timeout'))).toBe(true);
        expect(mockWebSocketInstance.close).toHaveBeenCalled();
    });

    it('resets workflow to initial state', () => {
        useAnalysisStore.getState().startAnalysis();

        // Pass 'false' to prevent immediate auto-restart during test assertions
        useAnalysisStore.getState().resetWorkflow(false);

        const state = useAnalysisStore.getState();
        expect(state.status).toBe('idle');
        expect(state.logs).toHaveLength(0);
        expect(state.finalReport).toBeNull();
        expect(state.currentAction).toBeNull();
    });
});