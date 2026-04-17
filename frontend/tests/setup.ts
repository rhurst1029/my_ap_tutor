import '@testing-library/jest-dom';
import { vi } from 'vitest';

// Monaco stub — returns null to avoid JSX / react/jsx-dev-runtime resolution issues
// from outside frontend/. JSX mocks should live in individual test files if needed.
vi.mock('@monaco-editor/react', () => ({
  default: () => null,
}));
