/// <reference types="vitest" />
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // @ts-expect-error - Vitest added 'test' to Vite config, but TS doesn't detect it
  test: {
    globals: true, // Allows us to use describe, it, expect without importing them every time
    environment: 'jsdom', // Simulates the browser in Node
    setupFiles: ['./src/test/setup.ts'], // File that will run before the tests
    css: false, // Ignore CSS in tests to make them run faster
    exclude: ['node_modules', 'e2e/**/*'],
  },
})