import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import { resolve } from 'path';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: [resolve(__dirname, 'setup.tsx')],
    include: [resolve(__dirname, '**/*.{test,spec}.?(c|m)[jt]s?(x)')],
  },
  resolve: {
    alias: {
      '@': resolve(__dirname, '../../../frontend/src'),
    },
  },
});
