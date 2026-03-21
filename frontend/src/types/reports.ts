/**
 * Maps to the Pydantic Literal["safe", "infected"] type
 */
export type ReportStatus = 'safe' | 'infected';

/**
 * Represents an individual report from the /api/reports endpoint
 */
export interface ReportItem {
    filename: string;
    date: string;
    time: string;
    status: ReportStatus;
}

/**
 * API response structure for the reports list
 */
export interface ReportsListResponse {
    reports: ReportItem[];
    total_count: number;
}

/**
 * API response structure for individual report details /api/reports/{filename}
 */
export interface ReportDetailResponse {
    content: string; // Markdown formatted content
    date: string;
    time: string;
}