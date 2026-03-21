import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';
import { HumanTaskModal } from './HumanTaskModal';
import type { ActionRequest } from '../../types/analysis';

describe('HumanTaskModal Component', () => {
    const mockActionPayload: ActionRequest = {
        type: 'action_request',
        action_type: 'text_input',
        message: 'Provide authorization code'
    };

    it('renders the message sent by the server', () => {
        render(<HumanTaskModal actionPayload={mockActionPayload} onSubmit={vi.fn()} />);

        expect(screen.getByRole('heading', { name: /system halted/i })).toBeInTheDocument();
        expect(screen.getByText('Provide authorization code')).toBeInTheDocument();
    });

    it('handles button state and submits the form correctly', async () => {
        const onSubmitMock = vi.fn();
        const user = userEvent.setup();

        render(<HumanTaskModal actionPayload={mockActionPayload} onSubmit={onSubmitMock} />);

        const inputElement = screen.getByPlaceholderText(/type your response here/i);
        const submitButton = screen.getByRole('button', { name: /transmit/i });

        // By default, the button is disabled
        expect(submitButton).toBeDisabled();

        // User types in the input
        await user.type(inputElement, 'admin123');

        // The button is now enabled
        expect(submitButton).toBeEnabled();

        // User clicks submit
        await user.click(submitButton);

        // Verify that the onSubmit function was called with the correct value
        expect(onSubmitMock).toHaveBeenCalledWith('admin123');
        expect(onSubmitMock).toHaveBeenCalledTimes(1);
    });
});