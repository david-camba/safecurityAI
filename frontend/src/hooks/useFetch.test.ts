import { renderHook, waitFor, act } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { useFetch } from './useFetch';
import { server } from '../mocks/server';
import { http, HttpResponse, delay } from 'msw';
import { config } from '../config/env';

describe('useFetch Hook', () => {
    it('should fetch and return data successfully (uses MSW)', async () => {
        const { result } = renderHook(() => useFetch('/features'));

        // Initial state
        expect(result.current.isLoading).toBe(true);
        expect(result.current.data).toBeNull();

        // Wait for the hook to change its loading state to false
        await waitFor(() => expect(result.current.isLoading).toBe(false));

        // Verify that the data is the mock data
        expect(result.current.data).toHaveProperty('count', 2);
        expect(result.current.error).toBeNull();
    });

    it('should handle HTTP errors correctly', async () => {
        const { result } = renderHook(() => useFetch('/error-endpoint'));

        await waitFor(() => expect(result.current.isLoading).toBe(false));

        expect(result.current.data).toBeNull();
        expect(result.current.error).toBe('HTTP error: 500');
    });

    it('executes a new request when refetch is called', async () => {
        const { result } = renderHook(() => useFetch('/features'));

        await waitFor(() => {
            expect(result.current.isLoading).toBe(false);
        });

        act(() => {
            result.current.refetch();
        });

        expect(result.current.isLoading).toBe(true);

        await waitFor(() => {
            expect(result.current.isLoading).toBe(false);
        });

        expect(result.current.data).toHaveProperty('count', 2);
    });

    it('aborts the fetch request on component unmount to prevent memory leaks', async () => {
        const { result, unmount } = renderHook(() => useFetch('/delayed-endpoint'));

        expect(result.current.isLoading).toBe(true);

        // Unmount before the fetch completes
        unmount();

        // Wait to ensure the delayed response doesn't trigger a state update
        await new Promise((resolve) => setTimeout(resolve, 150));

        // State should remain frozen; no error should be set because AbortError is swallowed
        expect(result.current.error).toBeNull();
        expect(result.current.data).toBeNull();
        expect(result.current.isLoading).toBe(true);
    });

    it('aborts previous request and fetches new data when endpoint changes', async () => {
        let firstRequestAborted = false;
        server.use(
            http.get(`${config.apiUrl}/slow-endpoint`, async ({ request }) => {
                if (request.signal.aborted) {
                    firstRequestAborted = true;
                } else {
                    request.signal.addEventListener('abort', () => {
                        firstRequestAborted = true;
                    });
                }
                await delay(1500);
                return HttpResponse.json({ target: 'first' });
            }),
            http.get(`${config.apiUrl}/fast-endpoint`, async () => {
                return HttpResponse.json({ target: 'second' });
            })
        );

        const { result, rerender } = renderHook(
            ({ endpoint }) => useFetch(endpoint),
            { initialProps: { endpoint: '/slow-endpoint' } }
        );

        expect(result.current.isLoading).toBe(true);

        // Short pause to let the fetch request reach the MSW interceptor before aborting it.
        await new Promise((resolve) => setTimeout(resolve, 50));

        rerender({ endpoint: '/fast-endpoint' });

        await waitFor(() => {
            expect(result.current.isLoading).toBe(false);
        });

        expect(result.current.data).toEqual({ target: 'second' });
        expect(firstRequestAborted).toBe(true);
    });
});