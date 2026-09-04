import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';

export interface OrthogonalWireProps {
  points: [number, number][];
  highlighted?: boolean;
  color?: string;
  dashed?: boolean;
  label?: string;
}

export const OrthogonalWire: React.FC<OrthogonalWireProps> = ({
  points,
  highlighted = false,
  color,
  dashed = false,
  label,
}) => {
  if (points.length < 2) return null;

  let pathD = `M ${points[0][0]} ${points[0][1]}`;
  for (let i = 1; i < points.length; i++) {
    pathD += ` L ${points[i][0]} ${points[i][1]}`;
  }

  const strokeColor = color 
    ? color 
    : highlighted 
      ? 'var(--primary-active, #3b82f6)' 
      : 'var(--border, #475569)';

  const strokeWidth = highlighted ? 3.5 : 2;

  const getMiddlePoint = (): [number, number] => {
    const midIdx = Math.floor(points.length / 2);
    if (points.length % 2 === 0 && midIdx > 0) {
      const p1 = points[midIdx - 1];
      const p2 = points[midIdx];
      return [(p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2];
    }
    return points[midIdx];
  };

  const mid = getMiddlePoint();

  return (
    <g className="schematic-wire-group">
      <path
        d={pathD}
        fill="none"
        stroke="transparent"
        strokeWidth="10"
        style={{ cursor: 'pointer' }}
      />
      
      <path
        d={pathD}
        fill="none"
        stroke={strokeColor}
        strokeWidth={strokeWidth}
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeDasharray={dashed ? '5 4' : 'none'}
        style={{ transition: 'stroke 0.2s, stroke-width 0.2s' }}
        filter={highlighted ? 'url(#wire-glow)' : 'none'}
      />

      {label && mid && (
        <g transform={`translate(${mid[0]}, ${mid[1] - 8})`}>
          <rect
            x={-label.length * 3.5 - 4}
            y="-10"
            width={label.length * 7 + 8}
            height="14"
            rx="3"
            fill="var(--bg-card, #0f172a)"
            stroke="none"
          />
          <text
            textAnchor="middle"
            fontSize="9"
            fill={highlighted ? 'var(--primary-active, #3b82f6)' : 'var(--text-secondary, #94a3b8)'}
            fontWeight={highlighted ? 'bold' : 'normal'}
          >
            {label}
          </text>
        </g>
      )}
    </g>
  );
};

export interface SchematicCanvasProps {
  children: React.ReactNode;
  width?: number | string;
  height?: number | string;
  viewBox?: string;
  className?: string;
}

export const SchematicCanvas: React.FC<SchematicCanvasProps> = ({
  children,
  width = '100%',
  height = '100%',
  viewBox = '0 0 800 400',
  className = '',
}) => {
  const [isZoomed, setIsZoomed] = useState(false);

  useEffect(() => {
    if (isZoomed) {
      document.body.style.overflow = 'hidden';
      const handleKeyDown = (e: KeyboardEvent) => {
        if (e.key === 'Escape') {
          setIsZoomed(false);
        }
      };
      window.addEventListener('keydown', handleKeyDown);
      return () => {
        document.body.style.overflow = '';
        window.removeEventListener('keydown', handleKeyDown);
      };
    }
  }, [isZoomed]);

  return (
    <div className={`schematic-canvas-container relative w-full border border-slate-800 rounded-xl overflow-hidden bg-slate-950 p-2 ${className}`}>
      <button
        onClick={() => setIsZoomed(true)}
        className="absolute top-3 right-3 z-10 flex items-center justify-center p-1.5 rounded-lg bg-slate-900/80 hover:bg-slate-800 border border-slate-800 text-slate-400 hover:text-white transition-all shadow-md group cursor-pointer"
        title="View High-Resolution Schematic"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-4 h-4 transition-transform group-hover:scale-110">
          <polyline points="15 3 21 3 21 9"></polyline>
          <polyline points="9 21 3 21 3 15"></polyline>
          <line x1="21" y1="3" x2="14" y2="10"></line>
          <line x1="3" y1="21" x2="10" y2="14"></line>
        </svg>
      </button>

      <style>{`
        .schematic-canvas-svg {
          color: #cbd5e1;
          user-select: none;
        }
        
        .schematic-device-group {
          transition: transform 0.2s cubic-bezier(0.4, 0, 0.2, 1), color 0.2s;
        }
        
        .schematic-device-group:hover {
          color: var(--primary-active, #3b82f6);
        }
        
        .schematic-device-group.highlighted {
          color: var(--primary-active, #3b82f6) !important;
        }

        .schematic-device-group text {
          fill: currentColor;
          font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
        }

        @keyframes pulse-ring {
          0% {
            stroke-dashoffset: 0;
            stroke-opacity: 0.8;
          }
          100% {
            stroke-dashoffset: -12;
            stroke-opacity: 0.3;
          }
        }

        .schematic-device-group.highlighted circle {
          animation: pulse-ring 2s linear infinite;
        }

        .animate-spin-slow {
          animation: spin 12s linear infinite;
        }

        @keyframes spin {
          from {
            transform: rotate(0deg);
          }
          to {
            transform: rotate(360deg);
          }
        }
      `}</style>

      <svg
        width={width}
        height={height}
        viewBox={viewBox}
        className="schematic-canvas-svg w-full h-auto block"
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          <filter id="wire-glow" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="3" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
          
          <filter id="device-glow" x="-30%" y="-30%" width="160%" height="160%">
            <feGaussianBlur stdDeviation="5" result="blur" />
            <feComponentTransfer in="blur" result="glow">
              <feFuncA type="linear" slope="0.4" />
            </feComponentTransfer>
            <feMerge>
              <feMergeNode in="glow" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        <g stroke="rgba(71, 85, 105, 0.08)" strokeWidth="0.5">
          {Array.from({ length: 30 }).map((_, i) => (
            <line key={`v-${i}`} x1={i * 40} y1={0} x2={i * 40} y2={600} />
          ))}
          {Array.from({ length: 20 }).map((_, i) => (
            <line key={`h-${i}`} x1={0} y1={i * 40} x2={1200} y2={i * 40} />
          ))}
        </g>

        {children}
      </svg>

      {isZoomed && createPortal(
        <div 
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/85 backdrop-blur-md transition-all duration-300 animate-in fade-in"
          onClick={() => setIsZoomed(false)}
        >
          <div 
            className="relative w-full max-w-6xl bg-slate-900 border border-slate-800 rounded-2xl p-6 flex flex-col gap-4 text-white shadow-2xl animate-in zoom-in-95 duration-200"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-pulse"></span>
                <h3 className="text-sm font-bold text-slate-200">Interactive Circuit Schematic (HD View)</h3>
              </div>
              
              <div className="flex items-center gap-2">
                <span className="text-[10px] text-slate-400 bg-slate-950 px-2 py-0.5 rounded border border-slate-800">Press ESC or click outside to dismiss</span>
                <button
                  onClick={() => setIsZoomed(false)}
                  className="flex items-center justify-center p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 hover:text-white transition-all cursor-pointer"
                  title="Close"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-4 h-4">
                    <line x1="18" y1="6" x2="6" y2="18"></line>
                    <line x1="6" y1="6" x2="18" y2="18"></line>
                  </svg>
                </button>
              </div>
            </div>

            <div className="w-full bg-slate-950 border border-slate-850 rounded-xl p-4 overflow-auto flex items-center justify-center min-h-[300px] max-h-[75vh]">
              <svg
                width="100%"
                height="100%"
                viewBox={viewBox}
                className="schematic-canvas-svg w-full h-auto max-h-[70vh] block"
                xmlns="http://www.w3.org/2000/svg"
              >
                <defs>
                  <filter id="wire-glow" x="-20%" y="-20%" width="140%" height="140%">
                    <feGaussianBlur stdDeviation="3" result="blur" />
                    <feMerge>
                      <feMergeNode in="blur" />
                      <feMergeNode in="SourceGraphic" />
                    </feMerge>
                  </filter>
                  
                  <filter id="device-glow" x="-30%" y="-30%" width="160%" height="160%">
                    <feGaussianBlur stdDeviation="5" result="blur" />
                    <feComponentTransfer in="blur" result="glow">
                      <feFuncA type="linear" slope="0.4" />
                    </feComponentTransfer>
                    <feMerge>
                      <feMergeNode in="glow" />
                      <feMergeNode in="SourceGraphic" />
                    </feMerge>
                  </filter>
                </defs>

                <g stroke="rgba(71, 85, 105, 0.05)" strokeWidth="0.5">
                  {Array.from({ length: 30 }).map((_, i) => (
                    <line key={`v-hd-${i}`} x1={i * 40} y1={0} x2={i * 40} y2={600} />
                  ))}
                  {Array.from({ length: 20 }).map((_, i) => (
                    <line key={`h-hd-${i}`} x1={0} y1={i * 40} x2={1200} y2={i * 40} />
                  ))}
                </g>

                {children}
              </svg>
            </div>
          </div>
        </div>,
        document.body
      )}
    </div>
  );
};
