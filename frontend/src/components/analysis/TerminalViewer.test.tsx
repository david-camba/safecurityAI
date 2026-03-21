import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { TerminalViewer } from './TerminalViewer';
import type { LogEntry } from '../../types/analysis';

// Mocking scrollIntoView to avoid JSDOM errors
window.HTMLElement.prototype.scrollIntoView = vi.fn();

describe('TerminalViewer Component', () => {
    const mockLogs: LogEntry[] = [
        { id: '1', timestamp: '10:00:00', content: 'System boot initialized' },
        { id: '2', timestamp: '10:00:01', content: 'Scanning memory blocks...' }
    ];

    // Mocking Navigator Clipboard
    const writeTextMock = vi.fn().mockResolvedValue(undefined);

    beforeEach(() => {
        Object.assign(navigator, {
            clipboard: {
                writeText: writeTextMock,
            },
        });
    });

    afterEach(() => {
        vi.clearAllMocks();
    });

    it('renders logs and current status', () => {
        render(<TerminalViewer logs={mockLogs} status="running" />);

        // Verifying logs text
        expect(screen.getByText('System boot initialized')).toBeInTheDocument();
        expect(screen.getByText('Scanning memory blocks...')).toBeInTheDocument();

        // Verifying status
        expect(screen.getByText('running')).toBeInTheDocument();
    });

    it('copies all logs to the clipboard when the copy button is clicked', async () => {
        render(<TerminalViewer logs={mockLogs} status="error" />);

        const copyButton = screen.getByRole('button', { name: /copy logs to clipboard/i });

        // We use fireEvent because UserEvent override the navigator.clipboard.writeText function
        fireEvent.click(copyButton);

        // Verifying that the clipboard API was called with the correct formatted text
        const expectedClipboardText = "[10:00:00] System boot initialized\n[10:00:01] Scanning memory blocks...";
        await waitFor(() => {
            expect(writeTextMock).toHaveBeenCalledWith(expectedClipboardText);
        });
    });
});