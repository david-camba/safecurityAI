import * as fs from 'fs';
import { E2E_ENV } from './e2e-env.config.ts'; // Adjust path if needed

export default async function globalSetup() {
    // Validate structural integrity
    if (!fs.existsSync(E2E_ENV.LOGS_DIR) || !fs.statSync(E2E_ENV.LOGS_DIR).isDirectory()) {
        throw new Error(`CRITICAL: Logs directory missing at ${E2E_ENV.LOGS_DIR}.`);
    }

    if (!fs.existsSync(E2E_ENV.FEATURE_LOG_PATH) || !fs.statSync(E2E_ENV.FEATURE_LOG_PATH).isFile()) {
        throw new Error(`CRITICAL: Feature log file missing at ${E2E_ENV.FEATURE_LOG_PATH}.`);
    }

    // Seed Report Data
    const dummyReportContent = [
        '# E2E Automated Test Report',
        'This report was generated for testing purposes.',
        '<!-- END-OF-REPORT -->\n'
    ].join('\n');

    fs.writeFileSync(E2E_ENV.TEST_REPORT_PATH, dummyReportContent, 'utf-8');

    // Seed Feature Log Data
    const featureLogStats = fs.statSync(E2E_ENV.FEATURE_LOG_PATH);
    if (featureLogStats.size === 0) {
        const fallbackLogLine = '[2026-03-16 12:22:12] FEATURE: Implement automatic blocking of VBS script execution in scheduled tasks without a valid digital signature | REASON: Prevent the execution of obfuscated malicious scripts used for persistence.\n';
        fs.writeFileSync(E2E_ENV.FEATURE_LOG_PATH, fallbackLogLine, 'utf-8');

        // Pass state to teardown process via environment variable
        process.env.MODIFIED_FEATURE_LOG = 'true';
    } else {
        process.env.MODIFIED_FEATURE_LOG = 'false';
    }
}