import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';
import { StartPanel } from './StartPanel';

describe('StartPanel', () => {
    it('renders the UI correctly', () => {
        render(<StartPanel onStart={vi.fn()} />);

        expect(screen.getByRole('heading', { name: /system ready/i })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /initiate audit/i })).toBeInTheDocument();
    });

    it('calls onStart when the user clicks the button', async () => {
        const onStartMock = vi.fn();
        const user = userEvent.setup();

        render(<StartPanel onStart={onStartMock} />);

        const startButton = screen.getByRole('button', { name: /initiate audit/i });

        await user.click(startButton);

        expect(onStartMock).toHaveBeenCalledOnce();
    });
});