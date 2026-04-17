import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import { resolve } from 'path';

// frontend/node_modules is the authoritative module root.
// Test files live outside that directory, so we alias all packages that
// Vite's resolver would otherwise fail to find by walking up from testing/.
const frontendModules = resolve(__dirname, '../../../frontend/node_modules');
const r = (pkg: string) => resolve(frontendModules, pkg);

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: [resolve(__dirname, 'setup.ts')],
    include: [resolve(__dirname, '**/*.{test,spec}.?(c|m)[jt]s?(x)')],
  },
  resolve: {
    alias: {
      '@': resolve(__dirname, '../../../frontend/src'),
      'react': r('react'),
      'react-dom': r('react-dom'),
      'react/jsx-dev-runtime': r('react/jsx-dev-runtime'),
      'react/jsx-runtime': r('react/jsx-runtime'),
      '@testing-library/react': r('@testing-library/react'),
      '@testing-library/jest-dom': r('@testing-library/jest-dom'),
      '@testing-library/user-event': r('@testing-library/user-event'),
      '@monaco-editor/react': r('@monaco-editor/react'),
      'vitest': r('vitest'),
    },
  },
});
