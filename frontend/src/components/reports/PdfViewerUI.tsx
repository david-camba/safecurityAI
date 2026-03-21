import { useState } from 'react';

interface PdfViewerUIProps {
    pdfUrl: string;
    filename: string;
}

export function PdfViewerUI({ pdfUrl, filename }: PdfViewerUIProps) {
    const [isHovered, setIsHovered] = useState(false);

    const handleDownload = () => {
        const anchor = document.createElement('a');
        anchor.href = pdfUrl;
        anchor.download = filename;
        anchor.click();
    };

    return (
        <div style={{
            display: 'flex',
            flexDirection: 'column',
            height: '100vh',
            backgroundColor: '#0a0a0a',
            fontFamily: "'JetBrains Mono', 'Fira Code', 'IBM Plex Mono', ui-monospace, monospace",
            margin: 0,
            overflow: 'hidden'
        }}>
            {/* Top Bar */}
            <div style={{
                padding: '12px 24px',
                backgroundColor: '#141414',
                borderBottom: '1px solid #333333',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                zIndex: 10
            }}>
                <div style={{ color: '#00ff41', fontSize: '14px', letterSpacing: '0.5px' }}>
                    {filename}
                </div>

                {/* Download Action */}
                <button
                    onClick={handleDownload}
                    onMouseEnter={() => setIsHovered(true)}
                    onMouseLeave={() => setIsHovered(false)}
                    style={{
                        padding: '6px 16px',
                        cursor: 'pointer',
                        backgroundColor: isHovered ? '#00ff41' : 'transparent',
                        border: '1px solid #00ff41',
                        color: isHovered ? '#0a0a0a' : '#00ff41',
                        fontFamily: 'inherit',
                        fontSize: '13px',
                        transition: 'all 0.2s ease',
                    }}
                >
                    [ DOWNLOAD ]
                </button>
            </div>

            {/* Viewer */}
            <iframe
                src={`${pdfUrl}#toolbar=0&navpanes=0`}
                title={filename}
                style={{ flexGrow: 1, border: 'none', width: '100%', backgroundColor: '#0a0a0a' }}
            />
        </div>
    );
}