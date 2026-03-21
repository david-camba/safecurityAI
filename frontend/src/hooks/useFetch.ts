import { useState, useEffect, useCallback } from 'react';
import { config } from '../config/env';

export function useFetch<T>(endpoint: string) {
    const [data, setData] = useState<T | null>(null);
    const [isLoading, setIsLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);

    // This function now accepts an optional signal to be testable and reusable.
    const fetchData = useCallback(async (signal?: AbortSignal) => {
        setIsLoading(true);
        setError(null);
        try {
            const response = await fetch(`${config.apiUrl}${endpoint}`, { signal });
            if (!response.ok) {
                throw new Error(`HTTP error: ${response.status}`);
            }
            const json = await response.json();
            if (!signal?.aborted) {
                setData(json);
                setIsLoading(false);
            }
        } catch (err: unknown) {
            if (err instanceof DOMException && err.name === 'AbortError') {
                return; // Fetch was intentionally aborted, so we swallow the error.
            }
            setError(err instanceof Error ? err.message : 'Unknown error occurred');
            setIsLoading(false);
        }
    }, [endpoint]);

    const refetch = useCallback(() => {
        fetchData();
    }, [fetchData]);

    useEffect(() => {
        const controller = new AbortController();
        fetchData(controller.signal);

        // This cleanup function is returned directly and synchronously to React.
        return () => {
            controller.abort();
        };
    }, [fetchData]);

    return { data, isLoading, error, refetch };
}