import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, it, expect, beforeEach } from 'vitest';
import { http, HttpResponse } from 'msw';
import SuggestionsPage from './SuggestionsPage';
import { server } from '../mocks/server';
import { config } from '../config/env';

describe('SuggestionsPage Integration', () => {
    let queryClient: QueryClient;

    // New QueryClient for each test
    beforeEach(() => {
        queryClient = new QueryClient({
            defaultOptions: {
                queries: { retry: false }, //no retry on failure
            },
        });
    });

    // Helper to wrap the component with its dependencies
    const renderWithProviders = () => {
        return render(
            <QueryClientProvider client={queryClient}>
                <SuggestionsPage />
            </QueryClientProvider>
        );
    };

    it('should show the loader and then render the suggestions (Happy Path)', async () => {
        renderWithProviders();

        // 1. Check initial state is "Loading"
        expect(screen.getByText(/ANALYZING SYSTEM VECTORS/i)).toBeInTheDocument();

        // 2. Wait for the network (MSW) to respond and the UI to update
        await waitFor(() => {
            expect(screen.getByText('Mocked Feature 1')).toBeInTheDocument();
        });

        // 3. Check that the two mock cards were rendered
        expect(screen.getByText('Because testing is awesome')).toBeInTheDocument();
        expect(screen.getByText('To show MSW working')).toBeInTheDocument();

        // The loader should no longer be in the DOM
        expect(screen.queryByText(/ANALYZING SYSTEM VECTORS/i)).not.toBeInTheDocument();
    });

    it('should show the error UI if the API fails', async () => {
        // FORCE MSW to return a 500 error only for this test
        server.use(
            http.get(`${config.apiUrl}/features`, () => {
                return new HttpResponse(null, { status: 500 });
            })
        );

        renderWithProviders();

        // Wait for the hook to process the error and show the retry button
        await waitFor(() => {
            expect(screen.getByRole('button', { name: /RETRY CONNECTION/i })).toBeInTheDocument();
        });

        // Check the error message on screen
        expect(screen.getByText(/Failed to retrieve suggestions/i)).toBeInTheDocument();
    });

    it('should show the empty state if the API returns an empty array', async () => {
        // Force empty response
        server.use(
            http.get(`${config.apiUrl}/features`, () => {
                return HttpResponse.json({ count: 0, suggestions: [] });
            })
        );

        renderWithProviders();

        await waitFor(() => {
            expect(screen.getByText(/No improvement proposals available at this time/i)).toBeInTheDocument();
        });
    });
});