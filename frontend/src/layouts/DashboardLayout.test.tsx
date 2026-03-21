import { render, screen, act } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import type { Mock } from 'vitest';
import DashboardLayout from './DashboardLayout';

describe('DashboardLayout Integration', () => {
    let fetchMock: Mock;

    beforeEach(() => {
        // Mock fetch
        fetchMock = vi.fn();
        vi.stubGlobal('fetch', fetchMock);

        // Mock AbortSignal.timeout to avoid conflicts with fake timers
        vi.spyOn(AbortSignal, 'timeout').mockImplementation(() => new AbortController().signal);

        vi.useFakeTimers();
    });

    afterEach(() => {
        vi.useRealTimers();
        vi.unstubAllGlobals();
        vi.restoreAllMocks();
    });

    const renderWithRouter = () => {
        return render(
            <MemoryRouter>
                <DashboardLayout />
            </MemoryRouter>
        );
    };

    it('renders the sidebar with all navigation links', () => {
        renderWithRouter();

        expect(screen.getByText('SAFECURITY.AI')).toBeInTheDocument();
        expect(screen.getByRole('link', { name: /live analysis/i })).toBeInTheDocument();
        expect(screen.getByRole('link', { name: /audit reports/i })).toBeInTheDocument();
        expect(screen.getByRole('link', { name: /suggestions/i })).toBeInTheDocument();
    });

    it('handles health check polling lifecycle (VERIFYING -> ONLINE -> OFFLINE)', async () => {
        // Initial OK Ping Mock
        fetchMock.mockResolvedValueOnce({ ok: true });

        render(
            <MemoryRouter>
                <DashboardLayout />
            </MemoryRouter>
        );

        // Initial State
        expect(screen.getByText('VERIFYING')).toBeInTheDocument();

        // Advance Time (3s initial delay)
        await act(async () => {
            await vi.advanceTimersByTimeAsync(3000);
        });

        expect(screen.getByText('ONLINE')).toBeInTheDocument();

        // Prepare NO-OK Ping Mock
        fetchMock.mockResolvedValueOnce({ ok: false });

        // Advance Time until polling (30s interval + 3s internal delay = 33000ms)
        await act(async () => {
            await vi.advanceTimersByTimeAsync(33000);
        });

        expect(screen.getByText('OFFLINE')).toBeInTheDocument();
    });
});