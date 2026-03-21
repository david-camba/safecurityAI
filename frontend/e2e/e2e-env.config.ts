import * as path from 'path';
import { fileURLToPath } from 'node:url';

// Resolve paths relative to this file's location
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export const E2E_ENV = {
    ROOT_DIR: path.resolve(__dirname, '../../'),
    get LOGS_DIR() { return path.join(this.ROOT_DIR, 'logs'); },
    get FEATURE_LOG_PATH() { return path.join(this.ROOT_DIR, 'agent_feature_suggestions.log'); },
    TEST_REPORT_FILENAME: 'audit_report_29991231_235959_safe.md',
    get TEST_REPORT_PATH() { return path.join(this.LOGS_DIR, this.TEST_REPORT_FILENAME); }
};