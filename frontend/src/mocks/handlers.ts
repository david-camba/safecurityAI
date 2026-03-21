import { http, HttpResponse, delay } from 'msw'
import { config } from '../config/env'

const API = config.apiUrl;

export const handlers = [
    // 1. Health check (DashboardLayout)
    http.get(`${API}/health-check`, async () => {
        return HttpResponse.text('OK', { status: 200 })
    }),

    // 2. Suggestions (SuggestionsPage)
    http.get(`${API}/features`, async () => {
        return HttpResponse.json({
            count: 2,
            suggestions: [
                {
                    date: '2026-03-17',
                    time: '10:00:00',
                    feature: 'Mocked Feature 1',
                    reason: 'Because testing is awesome'
                },
                {
                    date: '2026-03-17',
                    time: '10:05:00',
                    feature: 'Mocked Feature 2',
                    reason: 'To show MSW working'
                }
            ]
        })
    }),

    // 3. Reports List (ReportsPage)
    http.get(`${API}/reports`, async () => {
        return HttpResponse.json({
            total_count: 1,
            reports: [
                {
                    filename: 'Mocked_Report_01.pdf',
                    date: '2026-03-17',
                    time: '11:00:00',
                    status: 'safe'
                }
            ]
        })
    }),

    // 4. Report Detail (ReportListItem)
    http.get(`${API}/reports/:filename`, async ({ params }) => {
        return HttpResponse.json({
            content: `# Mocked Content for ${params.filename}\nThis is a mocked report generated for testing purposes.`,
            date: '2026-03-17',
            time: '11:00:00'
        })
    }),

    // 5. Error endpoint
    http.get(`${config.apiUrl}/error-endpoint`, () => {
        return new HttpResponse(null, { status: 500 });
    }),

    // 6. Delayed endpoint
    http.get(`${config.apiUrl}/delayed-endpoint`, async () => {
        await delay(100);
        return HttpResponse.json({ success: true });
    })

]