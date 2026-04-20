import { webcrypto } from 'node:crypto';
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
// Some Node installations (especially older Windows setups) do not expose
// globalThis.crypto.getRandomValues, which Vite expects at startup.
if (!globalThis.crypto || typeof globalThis.crypto.getRandomValues !== 'function') {
    globalThis.crypto = webcrypto;
}
export default defineConfig({
    plugins: [react()],
});
