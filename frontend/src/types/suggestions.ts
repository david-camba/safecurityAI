/**
 * Represents a single feature suggestion entry.
 */
export interface FeatureSuggestion {
    date: string;
    time: string;
    feature: string;
    reason: string;
}

/**
 * Represents the full API response from the /api/features endpoint.
 */
export interface FeatureSuggestionsResponse {
    count: number;
    suggestions: FeatureSuggestion[];
}