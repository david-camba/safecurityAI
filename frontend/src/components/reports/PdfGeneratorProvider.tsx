import { useEffect, useState } from 'react';
import type { ReactNode } from 'react';
import { marked } from 'marked';
import { Document, Page, pdf, Font } from '@react-pdf/renderer';
import Html from 'react-pdf-html';
import { launchNewPdfTab } from './launchNewPdfTab';
import DOMPurify from 'dompurify';

import JetBrainsMonoRegular from '../../fonts/JetBrainsMono-Regular.ttf';
import JetBrainsMonoBold from '../../fonts/JetBrainsMono-Bold.ttf';
import JetBrainsMonoItalic from '../../fonts/JetBrainsMono-Italic.ttf';

// Register custom fonts for PDF rendering
Font.register({
    family: 'JetBrains Mono',
    fonts: [
        { src: JetBrainsMonoRegular },
        { src: JetBrainsMonoBold, fontWeight: 'bold' },
        { src: JetBrainsMonoItalic, fontStyle: 'italic' }
    ]
});

// Styles compatible with react-pdf (React Native style object syntax)
const CYBER_THEME_STYLES = {
    h1: { fontSize: 24, fontWeight: 'bold', marginBottom: 12, paddingBottom: 6, borderBottomWidth: 1.5, borderBottomColor: '#00ff41', borderBottomStyle: 'solid', color: '#00ff41' },
    h2: { fontSize: 18, fontWeight: 'bold', marginTop: 18, marginBottom: 9, color: '#e5e5e5' },
    h3: { fontSize: 14, fontWeight: 'bold', marginTop: 15, marginBottom: 7, color: '#d4d4d4' },
    p: { fontSize: 12, lineHeight: 1.6, marginBottom: 12, color: '#cccccc' },
    ul: { marginBottom: 12, color: '#cccccc', paddingLeft: 18 },
    ol: { marginBottom: 12, color: '#cccccc', paddingLeft: 18 },
    li: { marginBottom: 4, fontSize: 12 },
    strong: { fontWeight: 'bold', color: '#00ff41' },
    em: { fontStyle: 'italic', color: '#a3a3a3' },
    a: { color: '#00ff41', textDecoration: 'underline' },
    blockquote: { borderLeftWidth: 3, borderLeftColor: '#00ff41', borderLeftStyle: 'solid', paddingLeft: 12, marginBottom: 12, color: '#a3a3a3', backgroundColor: '#141414', padding: 8 },
    code: { backgroundColor: '#141414', padding: 2, borderRadius: 3, color: '#00ff41', borderWidth: 1, borderColor: '#333333', borderStyle: 'solid' },
    pre: { backgroundColor: '#141414', padding: 12, borderRadius: 6, borderWidth: 1, borderColor: '#333333', borderStyle: 'solid', marginBottom: 12, color: '#00ff41' },
};

interface PdfState {
    status: 'processing' | 'ready' | 'error';
    pdfUrl: string | null;
    openPdf: () => void;
    retry: () => void;
}

interface PdfGeneratorProviderProps {
    report: string;
    filename?: string;
    children: (state: PdfState) => ReactNode;
}

export function PdfGeneratorProvider({
    report,
    filename = 'Cyber_Report.pdf',
    children
}: PdfGeneratorProviderProps) {
    const [status, setStatus] = useState<'processing' | 'ready' | 'error'>('processing');
    const [pdfUrl, setPdfUrl] = useState<string | null>(null);

    useEffect(() => {
        if (!report || status !== 'processing') return;

        const generatePdf = async () => {
            try {
                // Convert Markdown content to HTML
                const rawHtml = await marked.parse(report);
                const cleanHtml = DOMPurify.sanitize(rawHtml)

                // Build the document structure for React-PDF
                const MyDocument = (
                    <Document>
                        <Page
                            size="A4"
                            style={{
                                backgroundColor: '#0a0a0a',
                                padding: '40px 60px',
                                fontFamily: 'JetBrains Mono'
                            }}
                        >
                            <Html stylesheet={CYBER_THEME_STYLES}>
                                {cleanHtml}
                            </Html>
                        </Page>
                    </Document>
                );

                // Generate PDF blob and create a downloadable URL
                const pdfBlob = await pdf(MyDocument).toBlob();

                const url = URL.createObjectURL(pdfBlob);

                setPdfUrl(url);
                setStatus('ready');
            } catch (error) {
                setStatus('error');
                console.error("Failed to generate PDF:", error);
            }
        };

        generatePdf();
    }, [report, status]);

    /**
     * @deprecated Old imperative method.
     * Demonstrates manual DOM manipulation.
     */
    const openPdfViewerTab = (pdfUrl: string, filename: string): void => {
        const newTab = window.open('', '_blank');
        if (!newTab) return;

        const { document } = newTab;

        // 1. Base layout & theme initialization
        document.title = filename;
        document.body.style.margin = '0';
        document.body.style.overflow = 'hidden';
        document.body.style.backgroundColor = '#0a0a0a'; // cyber.bg
        document.body.style.display = 'flex';
        document.body.style.flexDirection = 'column';
        document.body.style.height = '100vh';
        document.body.style.fontFamily = "'JetBrains Mono', 'Fira Code', ui-monospace, monospace";

        // 2. Custom toolbar construction
        const topBar = document.createElement('div');
        topBar.style.padding = '12px 24px';
        topBar.style.backgroundColor = '#141414'; // cyber.card
        topBar.style.borderBottom = '1px solid #333333'; // cyber.border
        topBar.style.display = 'flex';
        topBar.style.justifyContent = 'space-between';
        topBar.style.alignItems = 'center';
        topBar.style.zIndex = '10';

        const titleDiv = document.createElement('div');
        titleDiv.textContent = filename;
        titleDiv.style.color = '#00ff41'; // cyber.accent
        titleDiv.style.fontSize = '14px';
        titleDiv.style.letterSpacing = '0.5px';

        // 3. Download handler
        const downloadBtn = document.createElement('button');
        downloadBtn.textContent = '[ DOWNLOAD ]';
        downloadBtn.style.padding = '6px 16px';
        downloadBtn.style.cursor = 'pointer';
        downloadBtn.style.backgroundColor = 'transparent';
        downloadBtn.style.border = '1px solid #00ff41'; // cyber.accent
        downloadBtn.style.color = '#00ff41'; // cyber.accent
        downloadBtn.style.fontFamily = 'inherit';
        downloadBtn.style.fontSize = '13px';
        downloadBtn.style.transition = 'all 0.2s ease';

        // Hover effects for the cyber button
        downloadBtn.onmouseover = () => {
            downloadBtn.style.backgroundColor = '#00ff41';
            downloadBtn.style.color = '#0a0a0a';
        };
        downloadBtn.onmouseout = () => {
            downloadBtn.style.backgroundColor = 'transparent';
            downloadBtn.style.color = '#00ff41';
        };

        // Force download overriding native blob behavior
        downloadBtn.onclick = () => {
            const anchor = document.createElement('a');
            anchor.href = pdfUrl;
            anchor.download = filename;
            anchor.click();
        };

        topBar.appendChild(titleDiv);
        topBar.appendChild(downloadBtn);

        // 4. PDF Viewer (Iframe)
        const iframe = document.createElement('iframe');
        // #toolbar=0 disables the native viewer controls
        iframe.src = `${pdfUrl}#toolbar=0&navpanes=0`;
        iframe.style.flexGrow = '1';
        iframe.style.border = 'none';
        iframe.style.width = '100%';
        iframe.style.backgroundColor = '#0a0a0a';
        iframe.title = filename;

        // 5. Mount components
        document.body.appendChild(topBar);
        document.body.appendChild(iframe);
    };

    /**
     * Opens the PDF in a new tab, wrapped in an iframe to solve the "UUID Title" issue.
     */
    const openPdf = () => {
        if (!pdfUrl) return;
        launchNewPdfTab(pdfUrl, filename);
    };

    /**
     * Retry logic forces the effect to re-run
     */
    const retry = () => setStatus('processing');

    return (
        <>
            {children({ status, pdfUrl, openPdf, retry })}
        </>
    );
}