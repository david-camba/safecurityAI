import * as fs from 'fs';
import { E2E_ENV } from './e2e-env.config.ts';

export default async function globalTeardown() {
    // Teardown seeded report
    if (fs.existsSync(E2E_ENV.TEST_REPORT_PATH)) {
        fs.unlinkSync(E2E_ENV.TEST_REPORT_PATH);
    }

    // Revert feature log based on setup state across process boundary
    if (process.env.MODIFIED_FEATURE_LOG === 'true' && fs.existsSync(E2E_ENV.FEATURE_LOG_PATH)) {
        fs.writeFileSync(E2E_ENV.FEATURE_LOG_PATH, '', 'utf-8');
    }
}