export const config = {
    apiUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080/api',
    wsUrl: import.meta.env.VITE_WS_URL || 'ws://localhost:8080/ws',
};