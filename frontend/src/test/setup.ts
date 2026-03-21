import '@testing-library/jest-dom/vitest'
import { beforeAll, afterEach, afterAll, vi } from 'vitest'
import { server } from '../mocks/server'

// 1. Run MSW before tests
beforeAll(() => server.listen({ onUnhandledRequest: 'error' }))

// 2. Reset handlers after each test
afterEach(() => {
    server.resetHandlers()
    vi.clearAllMocks()
})

// 3. Close MSW after all tests
afterAll(() => server.close())

// Polyfill for window.matchMedia
Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: vi.fn().mockImplementation(query => ({
        matches: false,
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
    })),
})