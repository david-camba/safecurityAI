/**
 * Represents the internal state of the Analysis Machine.
 */
export type AnalysisStatus = 'idle' | 'running' | 'waiting_human' | 'completed' | 'error';

/**
 * Individual log entry for the UI terminal.
 */
export interface LogEntry {
    readonly id: string;
    readonly timestamp: string;
    readonly content: string;
}

/**
 * Valid action types that the Backend can request from the Frontend.
 */
export type ActionType = 'text_input' | 'file_upload';

// --- SERVER TO CLIENT MESSAGES (Inbound) ---

export type ServerMessageType = 'log' | 'action_request' | 'action_ack' | 'error' | 'complete';

interface BaseServerMessage {
    type: ServerMessageType;
}

export interface LogMessage extends BaseServerMessage {
    type: 'log';
    content: string;
}

export interface ActionRequest extends BaseServerMessage {
    type: 'action_request';
    action_type: ActionType;
    message: string;
}

export interface ActionAcknowledgmentMessage extends BaseServerMessage {
    type: 'action_ack';
    accepted_action: string;
}

export interface ErrorMessage extends BaseServerMessage {
    type: 'error';
    content: string;
}

export interface CompletionMessage extends BaseServerMessage {
    type: 'complete';
    report: string;
}

/**
 * Union type for all possible messages received from the server.
 */
export type ServerMessage =
    | LogMessage
    | ActionRequest
    | ActionAcknowledgmentMessage
    | ErrorMessage
    | CompletionMessage;


// --- CLIENT TO SERVER MESSAGES (Outbound) ---

export type ClientMessageType = 'human_text_answer' | 'human_file_upload';

export interface HumanTextResponse {
    type: 'human_text_answer';
    answer: string;
}

/**
 * Union type for all possible messages sent to the server.
 */
export type ClientMessage = HumanTextResponse;