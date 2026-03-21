import { createRoot } from 'react-dom/client';
import { PdfViewerUI } from './PdfViewerUI';

/**
 * Bootstraps a React component tree into a newly opened browser tab.
 * Handles DOM initialization and lifecycle cleanup.
 */
export function launchNewPdfTab(pdfUrl: string, filename: string): void {
    const newTab = window.open('', '_blank');
    if (!newTab) {
        console.warn('Browser blocked the new tab creation.');
        return;
    }

    // Initialize environment
    newTab.document.title = filename;
    newTab.document.body.style.margin = '0';
    newTab.document.body.style.backgroundColor = '#0a0a0a';

    // Create React mounting point
    const rootContainer = newTab.document.createElement('div');
    rootContainer.id = 'cyber-pdf-root';
    newTab.document.body.appendChild(rootContainer);

    // Render application tree
    const root = createRoot(rootContainer);
    root.render(<PdfViewerUI pdfUrl={pdfUrl} filename={filename} />);

    // Prevent memory leaks on tab close
    newTab.addEventListener('beforeunload', () => {
        root.unmount();
    });
}