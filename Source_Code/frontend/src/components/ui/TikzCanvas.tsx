import React, { useEffect, useRef, useState } from 'react';

interface TikzCanvasProps {
  code: string;
  className?: string;
}

export const TikzCanvas: React.FC<TikzCanvasProps> = ({ code, className }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    // Clear previous contents
    containerRef.current.innerHTML = '';
    setError(null);
    setLoading(true);

    // Double check if tikzjax script is loaded on the page
    if (!(window as any).postMessage) {
      setError('TikZJax script not found on the page.');
      setLoading(false);
      return;
    }

    // Create the script element
    const script = document.createElement('script');
    script.type = 'text/tikz';
    
    // Wrap in standard circuitikz package configuration
    script.textContent = `
\\usepackage[american, europeanresistors, cuteinductors]{circuitikz}
\\begin{document}
\\begin{circuitikz}[scale=1.2, transform shape]
${code}
\\end{circuitikz}
\\end{document}
`;

    containerRef.current.appendChild(script);

    // Set a timeout in case tikzjax fails to load or compile (e.g. offline)
    const timeout = setTimeout(() => {
      if (loading) {
        setLoading(false);
        setError('LaTeX rendering timed out. Please check network connection for LaTeX Circuitikz assets.');
      }
    }, 8000);

    // Polling to detect when script is replaced by SVG
    const checkInterval = setInterval(() => {
      if (containerRef.current) {
        const svg = containerRef.current.querySelector('svg');
        if (svg) {
          setLoading(false);
          setError(null);
          clearInterval(checkInterval);
          clearTimeout(timeout);
          
          // Apply responsive/style adjustments to the generated SVG
          svg.setAttribute('width', '100%');
          svg.setAttribute('height', '100%');
          svg.style.maxWidth = '100%';
          svg.style.height = 'auto';
          svg.style.color = '#f1f5f9'; // text slate-100 color
          
          // Style all paths/lines to fit dark theme
          const paths = svg.querySelectorAll('path');
          paths.forEach((path) => {
            const stroke = path.getAttribute('stroke');
            if (stroke && stroke !== 'none') {
              path.setAttribute('stroke', '#cbd5e1'); // slate-300 lines
            }
          });
          
          const texts = svg.querySelectorAll('text');
          texts.forEach((text) => {
            text.setAttribute('fill', '#f1f5f9'); // slate-100 texts
            text.style.fontFamily = 'Outfit, Inter, sans-serif';
          });
        }
      }
    }, 100);

    return () => {
      clearInterval(checkInterval);
      clearTimeout(timeout);
    };
  }, [code]);

  return (
    <div className={`relative flex items-center justify-center min-h-[280px] bg-[#0b0f19]/40 rounded-lg p-6 border border-slate-800 ${className}`}>
      {loading && (
        <div className="absolute inset-0 flex flex-col items-center justify-center bg-slate-950/70 z-10 text-xs text-cyan-400 font-medium gap-3 rounded-lg">
          <div className="w-6 h-6 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin"></div>
          <span className="animate-pulse">Rendering publication-grade schematic via LaTeX Circuitikz engine...</span>
        </div>
      )}
      {error && (
        <div className="absolute inset-0 flex flex-col items-center justify-center bg-slate-950/80 z-10 text-xs text-amber-500 font-medium gap-2 p-4 text-center rounded-lg">
          <span>⚠️ {error}</span>
          <span className="text-[10px] text-slate-400">
            (If offline, configure local assets or click another tab to reload)
          </span>
        </div>
      )}
      <div ref={containerRef} className="w-full h-full flex justify-center items-center overflow-auto tikzjax-container" />
    </div>
  );
};
