import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { useAnalysisWorkflow } from './AnalysisWorkflow';

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

    // Mocked Callbacks
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    onopen: any = null;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    onmessage: any = null;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    onerror: any = null;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    onclose: any = null;

    constructor() {
        // Store the Hook's WebSocket instance globally to trigger events during tests.
        // eslint-disable-next-line @typescript-eslint/no-this-alias
        mockWebSocketInstance = this;
    }
}

describe('useAnalysisWorkflow Hook', () => {
    beforeEach(() => {
        mockWebSocketInstance = null;
        vi.stubGlobal('WebSocket', MockWebSocket);
    });

    afterEach(() => {
        // Restore WebSocket
        vi.unstubAllGlobals();
    });

    it('should start with idle state and no logs', () => {
        const { result } = renderHook(() => useAnalysisWorkflow());
        expect(result.current.status).toBe('idle');
        expect(result.current.logs).toEqual([]);
    });

    it('should change to running and register the connection attempt when starting', () => {
        const { result } = renderHook(() => useAnalysisWorkflow());

        // We open the connection
        act(() => {
            result.current.startAnalysis();
        });

        expect(result.current.status).toBe('running');
        expect(result.current.logs[0].content).toContain('Initializing connection');

        // Simulate that the backend accepted the WebSocket connection
        act(() => {
            mockWebSocketInstance.onopen();
        });

        expect(result.current.logs[1].content).toContain('Connection established');
    });

    it('should ask for human intervention when receiving an action_request', () => {
        const { result } = renderHook(() => useAnalysisWorkflow());

        act(() => result.current.startAnalysis());

        // Simulate an incoming message from the backend server
        act(() => {
            const messageEvent = {
                data: JSON.stringify({
                    type: 'action_request',
                    action_type: 'text_input',
                    message: 'Please provide the decryption key'
                })
            } as MessageEvent;

            mockWebSocketInstance.onmessage(messageEvent);
        });

        expect(result.current.status).toBe('waiting_human');
        expect(result.current.currentAction?.message).toBe('Please provide the decryption key');
    });

    it('appends log entries when receiving a log message', () => {
        const { result } = renderHook(() => useAnalysisWorkflow());
        act(() => result.current.startAnalysis());

        act(() => {
            mockWebSocketInstance.onmessage({
                data: JSON.stringify({ type: 'log', content: 'Scanning memory space...' })
            } as MessageEvent);
        });

        expect(result.current.logs).toHaveLength(2);
        expect(result.current.logs[1].content).toBe('Scanning memory space...');
    });

    it('transmits human response and resumes workflow on acknowledgment', () => {
        const { result } = renderHook(() => useAnalysisWorkflow());
        act(() => result.current.startAnalysis());

        act(() => {
            mockWebSocketInstance.onmessage({
                data: JSON.stringify({
                    type: 'action_request',
                    action_type: 'text_input',
                    message: 'Auth required'
                })
            } as MessageEvent);
        });

        act(() => {
            result.current.submitHumanResponse('admin123');
        });

        expect(mockWebSocketInstance.send).toHaveBeenCalledWith(
            JSON.stringify({ type: 'human_text_answer', answer: 'admin123' })
        );

        act(() => {
            mockWebSocketInstance.onmessage({
                data: JSON.stringify({ type: 'action_ack', accepted_action: 'admin123' })
            } as MessageEvent);
        });

        expect(result.current.status).toBe('running');
        expect(result.current.currentAction).toBeNull();
        expect(result.current.logs.some(l => l.content.includes('User input accepted'))).toBe(true);
    });

    it('transitions to completed state and stores final report', () => {
        const { result } = renderHook(() => useAnalysisWorkflow());
        act(() => result.current.startAnalysis());

        act(() => {
            mockWebSocketInstance.onmessage({
                data: JSON.stringify({ type: 'complete', report: '# Final Audit' })
            } as MessageEvent);
        });

        expect(result.current.status).toBe('completed');
        expect(result.current.finalReport).toBe('# Final Audit');
    });

    it('handles unexpected WebSocket closure', () => {
        const { result } = renderHook(() => useAnalysisWorkflow());
        act(() => result.current.startAnalysis());

        act(() => {
            mockWebSocketInstance.onclose();
        });

        expect(result.current.status).toBe('error');
        expect(result.current.logs.some(l => l.content.includes('Transport disconnected'))).toBe(true);
    });

    it('aborts connection and sets error if timeout is reached', () => {
        vi.useFakeTimers();
        const { result } = renderHook(() => useAnalysisWorkflow());

        act(() => {
            result.current.startAnalysis();
        });

        // Socket simulate trying to connect (state 0)
        mockWebSocketInstance.readyState = MockWebSocket.CONNECTING;

        // Fast-forward to trigger the internal 5000ms connection timeout
        act(() => {
            vi.advanceTimersByTime(5000);
        });

        expect(result.current.status).toBe('error');
        expect(result.current.logs.some(l => l.content.includes('Connection timeout'))).toBe(true);
        expect(mockWebSocketInstance.close).toHaveBeenCalled();

        vi.useRealTimers();
    });

    it('resets workflow to initial state', () => {
        const { result } = renderHook(() => useAnalysisWorkflow());
        act(() => result.current.startAnalysis());

        act(() => {
            result.current.resetWorkflow();
        });

        expect(result.current.status).toBe('idle');
        expect(result.current.logs).toHaveLength(0);
        expect(result.current.finalReport).toBeNull();
        expect(result.current.currentAction).toBeNull();
    });
});