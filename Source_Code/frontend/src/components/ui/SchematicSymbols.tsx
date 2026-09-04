import React from 'react';

export interface SchematicComponentProps {
  x: number;
  y: number;
  rotation?: number; // Rotation angle: 0, 90, 180, 270
  id?: string;
  label?: string;      // Component designator, e.g. Q1, C_in
  subLabel?: string;   // Parameter value, e.g. 15 uH, 220 uF
  highlighted?: boolean;
  pinLength?: number;  // Pin extension length for sources (AC/DC), default 30
  onClick?: (e: React.MouseEvent) => void;
  onMouseEnter?: () => void;
  onMouseLeave?: () => void;
  onMouseDown?: (e: React.MouseEvent) => void;
  onDoubleClick?: () => void;
}

// Unified hover and highlight filter effects
const getInteractiveProps = (props: SchematicComponentProps) => {
  const { highlighted, onClick, onMouseEnter, onMouseLeave, onMouseDown, onDoubleClick } = props;
  return {
    onClick: (e: React.MouseEvent) => {
      e.stopPropagation();
      onClick?.(e);
    },
    onMouseEnter,
    onMouseLeave,
    onMouseDown: (e: React.MouseEvent) => {
      onMouseDown?.(e);
    },
    onDoubleClick: () => {
      onDoubleClick?.();
    },
    style: {
      cursor: onClick || onMouseEnter || onMouseDown ? 'pointer' : 'default',
    },
    className: `schematic-device-group ${highlighted ? 'highlighted' : ''}`,
  };
};

interface SchematicLabelProps {
  label?: string;
  subLabel?: string;
  rotation: number;
}

export const SchematicLabel: React.FC<SchematicLabelProps> = ({ label, subLabel, rotation }) => {
  if (!label && !subLabel) return null;

  // Normalize rotation to 0, 90, 180, 270
  const normRot = ((rotation % 360) + 360) % 360;

  // Determine if component is horizontal or vertical
  // horizontal: rotation is 0, 180 (parallel to X axis)
  // vertical: rotation is 90, 270 (parallel to Y axis)
  const isHorizontal = normRot === 0 || normRot === 180;

  return (
    <g transform={`rotate(${-rotation})`}>
      {isHorizontal ? (
        <>
          {label && (
            <text x="0" y="-18" textAnchor="middle" fontSize="11" fontWeight="bold" fill="currentColor">
              {label}
            </text>
          )}
          {subLabel && (
            <text x="0" y="20" textAnchor="middle" fontSize="10" fill="var(--text-secondary, #94a3b8)">
              {subLabel}
            </text>
          )}
        </>
      ) : (
        <>
          {label && (
            <text x="22" y="-6" textAnchor="start" fontSize="11" fontWeight="bold" fill="currentColor">
              {label}
            </text>
          )}
          {subLabel && (
            <text x="22" y="8" textAnchor="start" fontSize="10" fill="var(--text-secondary, #94a3b8)">
              {subLabel}
            </text>
          )}
        </>
      )}
    </g>
  );
};


// 1. Resistor Component (IEC Standard: Rectangular Box)
export const SchematicResistor: React.FC<SchematicComponentProps> = (props) => {
  const { x, y, rotation = 0, label, subLabel, highlighted } = props;
  const interactive = getInteractiveProps(props);

  return (
    <g transform={`translate(${x}, ${y}) rotate(${rotation})`} {...interactive}>
      {/* Transparent interactive target area */}
      <rect x="-40" y="-15" width="80" height="30" fill="transparent" stroke="none" />
      
      {/* Leads */}
      <line x1="-40" y1="0" x2="-15" y2="0" stroke="currentColor" strokeWidth="2" />
      <line x1="15" y1="0" x2="40" y2="0" stroke="currentColor" strokeWidth="2" />
      
      {/* Body */}
      <rect
        x="-15"
        y="-6"
        width="30"
        height="12"
        fill={highlighted ? 'var(--primary-glow-bg, rgba(59, 130, 246, 0.1))' : 'var(--bg-card, #1e293b)'}
        stroke={highlighted ? 'var(--primary-active, #3b82f6)' : 'currentColor'}
        strokeWidth="2"
      />

      <SchematicLabel label={label} subLabel={subLabel} rotation={rotation} />
    </g>
  );
};

// 2. Non-polarized Capacitor Component (IEC Standard: Parallel Plates)
export const SchematicCapacitor: React.FC<SchematicComponentProps> = (props) => {
  const { x, y, rotation = 0, label, subLabel, highlighted } = props;
  const interactive = getInteractiveProps(props);

  return (
    <g transform={`translate(${x}, ${y}) rotate(${rotation})`} {...interactive}>
      <rect x="-40" y="-20" width="80" height="40" fill="transparent" stroke="none" />
      
      <line x1="-40" y1="0" x2="-4" y2="0" stroke="currentColor" strokeWidth="2" />
      <line x1="4" y1="0" x2="40" y2="0" stroke="currentColor" strokeWidth="2" />
      
      {/* Dual Plates */}
      <line
        x1="-4"
        y1="-15"
        x2="-4"
        y2="15"
        stroke={highlighted ? 'var(--primary-active, #3b82f6)' : 'currentColor'}
        strokeWidth="2.5"
      />
      <line
        x1="4"
        y1="-15"
        x2="4"
        y2="15"
        stroke={highlighted ? 'var(--primary-active, #3b82f6)' : 'currentColor'}
        strokeWidth="2.5"
      />

      <SchematicLabel label={label} subLabel={subLabel} rotation={rotation} />
    </g>
  );
};

// 3. Polarized Capacitor Component (One straight plate, one curved plate with + sign)
export const SchematicCapacitorPolar: React.FC<SchematicComponentProps> = (props) => {
  const { x, y, rotation = 0, label, subLabel, highlighted } = props;
  const interactive = getInteractiveProps(props);

  return (
    <g transform={`translate(${x}, ${y}) rotate(${rotation})`} {...interactive}>
      <rect x="-40" y="-20" width="80" height="40" fill="transparent" stroke="none" />
      
      <line x1="-40" y1="0" x2="-5" y2="0" stroke="currentColor" strokeWidth="2" />
      <line x1="5" y1="0" x2="40" y2="0" stroke="currentColor" strokeWidth="2" />
      
      {/* Positive plate (straight) */}
      <line
        x1="-5"
        y1="-15"
        x2="-5"
        y2="15"
        stroke={highlighted ? 'var(--primary-active, #3b82f6)' : 'currentColor'}
        strokeWidth="2.5"
      />
      
      {/* Negative plate (curved) */}
      <path
        d="M 5 -15 Q 12 0 5 15"
        fill="none"
        stroke={highlighted ? 'var(--primary-active, #3b82f6)' : 'currentColor'}
        strokeWidth="2.5"
      />
      
      {/* Positive marker + */}
      <text x="-16" y="-8" fontSize="12" fontWeight="bold" fill={highlighted ? 'var(--primary-active, #3b82f6)' : 'currentColor'} textAnchor="middle">+</text>

      <SchematicLabel label={label} subLabel={subLabel} rotation={rotation} />
    </g>
  );
};

// 4. Inductor Component (4 consecutive semicircular turns)
export const SchematicInductor: React.FC<SchematicComponentProps> = (props) => {
  const { x, y, rotation = 0, label, subLabel, highlighted } = props;
  const interactive = getInteractiveProps(props);

  return (
    <g transform={`translate(${x}, ${y}) rotate(${rotation})`} {...interactive}>
      <rect x="-40" y="-15" width="80" height="30" fill="transparent" stroke="none" />
      
      <line x1="-40" y1="0" x2="-20" y2="0" stroke="currentColor" strokeWidth="2" />
      <line x1="20" y1="0" x2="40" y2="0" stroke="currentColor" strokeWidth="2" />
      
      {/* 4 Arc Coils */}
      <path
        d="M -20 0 A 5 5 0 0 1 -10 0 A 5 5 0 0 1 0 0 A 5 5 0 0 1 10 0 A 5 5 0 0 1 20 0"
        fill="none"
        stroke={highlighted ? 'var(--primary-active, #3b82f6)' : 'currentColor'}
        strokeWidth="2.5"
        strokeLinecap="round"
      />

      <SchematicLabel label={label} subLabel={subLabel} rotation={rotation} />
    </g>
  );
};

// 5. Diode Component (Triangle + Cathode bar)
export const SchematicDiode: React.FC<SchematicComponentProps> = (props) => {
  const { x, y, rotation = 0, label, subLabel, highlighted } = props;
  const interactive = getInteractiveProps(props);

  return (
    <g transform={`translate(${x}, ${y}) rotate(${rotation})`} {...interactive}>
      <rect x="-40" y="-20" width="80" height="40" fill="transparent" stroke="none" />
      
      <line x1="-40" y1="0" x2="-10" y2="0" stroke="currentColor" strokeWidth="2" />
      <line x1="10" y1="0" x2="40" y2="0" stroke="currentColor" strokeWidth="2" />
      
      {/* Diode Triangle */}
      <polygon
        points="-10,-12 10,0 -10,12"
        fill={highlighted ? 'var(--primary-glow-bg, rgba(59, 130, 246, 0.1))' : 'var(--bg-card, #1e293b)'}
        stroke={highlighted ? 'var(--primary-active, #3b82f6)' : 'currentColor'}
        strokeWidth="2.5"
      />
      
      {/* Cathode Vertical Bar */}
      <line
        x1="10"
        y1="-12"
        x2="10"
        y2="12"
        stroke={highlighted ? 'var(--primary-active, #3b82f6)' : 'currentColor'}
        strokeWidth="2.5"
      />

      <SchematicLabel label={label} subLabel={subLabel} rotation={rotation} />
    </g>
  );
};

// 6. Zener Diode Component (Diode with angled cathode bar)
export const SchematicZenerDiode: React.FC<SchematicComponentProps> = (props) => {
  const { x, y, rotation = 0, label, subLabel, highlighted } = props;
  const interactive = getInteractiveProps(props);

  return (
    <g transform={`translate(${x}, ${y}) rotate(${rotation})`} {...interactive}>
      <rect x="-40" y="-20" width="80" height="40" fill="transparent" stroke="none" />
      
      <line x1="-40" y1="0" x2="-10" y2="0" stroke="currentColor" strokeWidth="2" />
      <line x1="10" y1="0" x2="40" y2="0" stroke="currentColor" strokeWidth="2" />
      
      <polygon
        points="-10,-12 10,0 -10,12"
        fill={highlighted ? 'var(--primary-glow-bg, rgba(59, 130, 246, 0.1))' : 'var(--bg-card, #1e293b)'}
        stroke={highlighted ? 'var(--primary-active, #3b82f6)' : 'currentColor'}
        strokeWidth="2.5"
      />
      
      {/* Zener Folded Cathode */}
      <path
        d="M 6 -12 L 10 -12 L 10 12 L 14 12"
        fill="none"
        stroke={highlighted ? 'var(--primary-active, #3b82f6)' : 'currentColor'}
        strokeWidth="2.5"
      />

      <SchematicLabel label={label} subLabel={subLabel} rotation={rotation} />
    </g>
  );
};

// 7. N-Channel MOSFET Component
export const SchematicMosfetN: React.FC<SchematicComponentProps> = (props) => {
  const { x, y, rotation = 0, label, subLabel, highlighted } = props;
  const interactive = getInteractiveProps(props);

  return (
    <g transform={`translate(${x}, ${y}) rotate(${rotation})`} {...interactive}>
      <rect x="-40" y="-40" width="80" height="80" fill="transparent" stroke="none" />
      
      {/* Drain and Source leads */}
      <line x1="0" y1="-40" x2="0" y2="-20" stroke="currentColor" strokeWidth="2" />
      <line x1="0" y1="20" x2="0" y2="40" stroke="currentColor" strokeWidth="2" />
      
      {/* Gate lead */}
      <line x1="-40" y1="10" x2="-15" y2="10" stroke="currentColor" strokeWidth="2" />
      {/* Gate plate */}
      <line x1="-15" y1="-10" x2="-15" y2="20" stroke="currentColor" strokeWidth="2.5" />
      
      {/* MOSFET insulated channel (3 segments) */}
      <line x1="-8" y1="-20" x2="-8" y2="-10" stroke="currentColor" strokeWidth="2.5" />
      <line x1="-8" y1="-5" x2="-8" y2="5" stroke="currentColor" strokeWidth="2.5" />
      <line x1="-8" y1="10" x2="-8" y2="20" stroke="currentColor" strokeWidth="2.5" />
      
      {/* Horizontal connections */}
      <line x1="-8" y1="-20" x2="0" y2="-20" stroke="currentColor" strokeWidth="2" />
      <line x1="-8" y1="20" x2="0" y2="20" stroke="currentColor" strokeWidth="2" />
      {/* Substrate lead */}
      <line x1="-8" y1="0" x2="0" y2="0" stroke="currentColor" strokeWidth="2" />
      <line x1="0" y1="0" x2="0" y2="20" stroke="currentColor" strokeWidth="2" />

      {/* N-Channel arrow pointing inward */}
      <path d="M -15 -4 L -8 0 L -15 4" fill="currentColor" />

      {/* Body Diode Loop */}
      <line x1="0" y1="-30" x2="22" y2="-30" stroke="currentColor" strokeWidth="1.5" />
      <line x1="22" y1="-30" x2="22" y2="-10" stroke="currentColor" strokeWidth="1.5" />
      <line x1="0" y1="30" x2="22" y2="30" stroke="currentColor" strokeWidth="1.5" />
      <line x1="22" y1="30" x2="22" y2="10" stroke="currentColor" strokeWidth="1.5" />
      
      {/* Body Diode symbol */}
      <polygon
        points="16,10 28,10 22,-6"
        fill={highlighted ? 'var(--primary-glow-bg, rgba(59, 130, 246, 0.1))' : 'var(--bg-card, #1e293b)'}
        stroke={highlighted ? 'var(--primary-active, #3b82f6)' : 'currentColor'}
        strokeWidth="1.5"
      />
      <line
        x1="16"
        y1="-6"
        x2="28"
        y2="-6"
        stroke={highlighted ? 'var(--primary-active, #3b82f6)' : 'currentColor'}
        strokeWidth="1.5"
      />

      {highlighted && (
        <circle cx="0" cy="0" r="32" fill="none" stroke="var(--primary-active, #3b82f6)" strokeWidth="1.5" strokeDasharray="4 3" className="animate-pulse" />
      )}

      <g transform={`rotate(${-rotation})`}>
        {label && (
          <text x="-38" y="-24" textAnchor="end" fontSize="11" fontWeight="bold" fill="currentColor">
            {label}
          </text>
        )}
        {subLabel && (
          <text x="-38" y="-10" textAnchor="end" fontSize="9" fill="var(--text-secondary, #94a3b8)">
            {subLabel}
          </text>
        )}
      </g>
    </g>
  );
};

// 8. P-Channel MOSFET Component
export const SchematicMosfetP: React.FC<SchematicComponentProps> = (props) => {
  const { x, y, rotation = 0, label, subLabel, highlighted } = props;
  const interactive = getInteractiveProps(props);

  return (
    <g transform={`translate(${x}, ${y}) rotate(${rotation})`} {...interactive}>
      <rect x="-40" y="-40" width="80" height="80" fill="transparent" stroke="none" />
      
      <line x1="0" y1="-40" x2="0" y2="-20" stroke="currentColor" strokeWidth="2" />
      <line x1="0" y1="20" x2="0" y2="40" stroke="currentColor" strokeWidth="2" />
      
      <line x1="-40" y1="10" x2="-15" y2="10" stroke="currentColor" strokeWidth="2" />
      <line x1="-15" y1="-10" x2="-15" y2="20" stroke="currentColor" strokeWidth="2.5" />
      
      <line x1="-8" y1="-20" x2="-8" y2="-10" stroke="currentColor" strokeWidth="2.5" />
      <line x1="-8" y1="-5" x2="-8" y2="5" stroke="currentColor" strokeWidth="2.5" />
      <line x1="-8" y1="10" x2="-8" y2="20" stroke="currentColor" strokeWidth="2.5" />
      
      <line x1="-8" y1="-20" x2="0" y2="-20" stroke="currentColor" strokeWidth="2" />
      <line x1="-8" y1="20" x2="0" y2="20" stroke="currentColor" strokeWidth="2" />
      <line x1="-8" y1="0" x2="0" y2="0" stroke="currentColor" strokeWidth="2" />
      <line x1="0" y1="0" x2="0" y2="20" stroke="currentColor" strokeWidth="2" />

      {/* P-Channel arrow pointing outward */}
      <path d="M -8 -4 L -15 0 L -8 4" fill="currentColor" />

      <line x1="0" y1="-30" x2="22" y2="-30" stroke="currentColor" strokeWidth="1.5" />
      <line x1="22" y1="-30" x2="22" y2="-10" stroke="currentColor" strokeWidth="1.5" />
      <line x1="0" y1="30" x2="22" y2="30" stroke="currentColor" strokeWidth="1.5" />
      <line x1="22" y1="30" x2="22" y2="10" stroke="currentColor" strokeWidth="1.5" />
      
      <polygon
        points="16,-10 28,-10 22,6"
        fill={highlighted ? 'var(--primary-glow-bg, rgba(59, 130, 246, 0.1))' : 'var(--bg-card, #1e293b)'}
        stroke={highlighted ? 'var(--primary-active, #3b82f6)' : 'currentColor'}
        strokeWidth="1.5"
      />
      <line
        x1="16"
        y1="6"
        x2="28"
        y2="6"
        stroke={highlighted ? 'var(--primary-active, #3b82f6)' : 'currentColor'}
        strokeWidth="1.5"
      />

      {highlighted && (
        <circle cx="0" cy="0" r="32" fill="none" stroke="var(--primary-active, #3b82f6)" strokeWidth="1.5" strokeDasharray="4 3" className="animate-pulse" />
      )}

      <g transform={`rotate(${-rotation})`}>
        {label && (
          <text x="-38" y="-24" textAnchor="end" fontSize="11" fontWeight="bold" fill="currentColor">
            {label}
          </text>
        )}
        {subLabel && (
          <text x="-38" y="-10" textAnchor="end" fontSize="9" fill="var(--text-secondary, #94a3b8)">
            {subLabel}
          </text>
        )}
      </g>
    </g>
  );
};

// 9. Dual-Winding Transformer Component
export interface SchematicTransformerProps extends SchematicComponentProps {
  dotPosition?: 'top-top' | 'top-bottom';
}

export const SchematicTransformer: React.FC<SchematicTransformerProps> = (props) => {
  const { x, y, rotation = 0, label, subLabel, highlighted, dotPosition = 'top-top' } = props;
  const interactive = getInteractiveProps(props);

  return (
    <g transform={`translate(${x}, ${y}) rotate(${rotation})`} {...interactive}>
      <rect x="-50" y="-40" width="100" height="80" fill="transparent" stroke="none" />
      
      {/* Magnetic Core (center dual lines) */}
      <line x1="-3" y1="-30" x2="-3" y2="30" stroke="currentColor" strokeWidth="2.5" />
      <line x1="3" y1="-30" x2="3" y2="30" stroke="currentColor" strokeWidth="2.5" />
      
      {/* Primary Coil */}
      <line x1="-40" y1="-25" x2="-20" y2="-25" stroke="currentColor" strokeWidth="2" />
      <line x1="-40" y1="25" x2="-20" y2="25" stroke="currentColor" strokeWidth="2" />
      
      <path
        d="M -20 -25 A 6.25 6.25 0 0 1 -20 -12.5 A 6.25 6.25 0 0 1 -20 0 A 6.25 6.25 0 0 1 -20 12.5 A 6.25 6.25 0 0 1 -20 25"
        fill="none"
        stroke={highlighted ? 'var(--primary-active, #3b82f6)' : 'currentColor'}
        strokeWidth="2.5"
        strokeLinecap="round"
      />
      
      {/* Secondary Coil */}
      <line x1="20" y1="-25" x2="40" y2="-25" stroke="currentColor" strokeWidth="2" />
      <line x1="20" y1="25" x2="40" y2="25" stroke="currentColor" strokeWidth="2" />
      
      <path
        d="M 20 -25 A 6.25 6.25 0 0 0 20 -12.5 A 6.25 6.25 0 0 0 20 0 A 6.25 6.25 0 0 0 20 12.5 A 6.25 6.25 0 0 0 20 25"
        fill="none"
        stroke={highlighted ? 'var(--primary-active, #3b82f6)' : 'currentColor'}
        strokeWidth="2.5"
        strokeLinecap="round"
      />

      {/* Polarity Dot */}
      <circle cx="-28" cy="-33" r="3" fill={highlighted ? 'var(--primary-active, #3b82f6)' : 'currentColor'} />
      
      {dotPosition === 'top-top' ? (
        <circle cx="28" cy="-33" r="3" fill={highlighted ? 'var(--primary-active, #3b82f6)' : 'currentColor'} />
      ) : (
        <circle cx="28" cy="33" r="3" fill={highlighted ? 'var(--primary-active, #3b82f6)' : 'currentColor'} />
      )}

      <g transform={`rotate(${-rotation})`}>
        {label && (
          <text x="-48" y="-5" textAnchor="end" fontSize="11" fontWeight="bold" fill="currentColor">
            {label}
          </text>
        )}
        {subLabel && (
          <text x="-48" y="10" textAnchor="end" fontSize="10" fill="var(--text-secondary, #94a3b8)">
            {subLabel}
          </text>
        )}
      </g>
    </g>
  );
};

// 10. AC Voltage Source
export const SchematicACSource: React.FC<SchematicComponentProps> = (props) => {
  const { x, y, rotation = 0, label, subLabel, highlighted, pinLength = 30 } = props;
  const interactive = getInteractiveProps(props);

  return (
    <g transform={`translate(${x}, ${y}) rotate(${rotation})`} {...interactive}>
      <rect x={-pinLength} y="-30" width={pinLength * 2} height="60" fill="transparent" stroke="none" />
      
      <line x1={-pinLength} y1="0" x2="-20" y2="0" stroke="currentColor" strokeWidth="2" />
      <line x1="20" y1="0" x2={pinLength} y2="0" stroke="currentColor" strokeWidth="2" />
      
      <circle
        cx="0"
        cy="0"
        r="20"
        fill={highlighted ? 'var(--primary-glow-bg, rgba(59, 130, 246, 0.1))' : 'var(--bg-card, #1e293b)'}
        stroke={highlighted ? 'var(--primary-active, #3b82f6)' : 'currentColor'}
        strokeWidth="2.5"
      />
      
      <path
        d="M -10 0 Q -5 -8 0 0 Q 5 8 10 0"
        fill="none"
        stroke={highlighted ? 'var(--primary-active, #3b82f6)' : 'currentColor'}
        strokeWidth="2"
      />

      <SchematicLabel label={label} subLabel={subLabel} rotation={rotation} />
    </g>
  );
};

// 11. DC Voltage Source
export const SchematicDCSource: React.FC<SchematicComponentProps> = (props) => {
  const { x, y, rotation = 0, label, subLabel, highlighted, pinLength = 30 } = props;
  const interactive = getInteractiveProps(props);

  return (
    <g transform={`translate(${x}, ${y}) rotate(${rotation})`} {...interactive}>
      <rect x={-pinLength} y="-30" width={pinLength * 2} height="60" fill="transparent" stroke="none" />
      
      <line x1={-pinLength} y1="0" x2="-6" y2="0" stroke="currentColor" strokeWidth="2" />
      <line x1="6" y1="0" x2={pinLength} y2="0" stroke="currentColor" strokeWidth="2" />
      
      {/* Positive Plate */}
      <line
        x1="-6"
        y1="-15"
        x2="-6"
        y2="15"
        stroke={highlighted ? 'var(--primary-active, #3b82f6)' : 'currentColor'}
        strokeWidth="2.5"
      />
      
      {/* Negative Plate */}
      <line
        x1="6"
        y1="-8"
        x2="6"
        y2="8"
        stroke={highlighted ? 'var(--primary-active, #3b82f6)' : 'currentColor'}
        strokeWidth="4"
      />

      <SchematicLabel label={label} subLabel={subLabel} rotation={rotation} />
    </g>
  );
};

// 12. Ground (3 horizontal lines)
export const SchematicGround: React.FC<Omit<SchematicComponentProps, 'rotation'>> = (props) => {
  const { x, y, label, highlighted } = props;
  const interactive = getInteractiveProps(props as SchematicComponentProps);

  return (
    <g transform={`translate(${x}, ${y})`} {...interactive}>
      <rect x="-20" y="0" width="40" height="25" fill="transparent" stroke="none" />
      
      <line x1="0" y1="0" x2="0" y2="8" stroke="currentColor" strokeWidth="2" />
      
      <line
        x1="-15"
        y1="8"
        x2="15"
        y2="8"
        stroke={highlighted ? 'var(--primary-active, #3b82f6)' : 'currentColor'}
        strokeWidth="2.5"
      />
      <line
        x1="-9"
        y1="13"
        x2="9"
        y2="13"
        stroke={highlighted ? 'var(--primary-active, #3b82f6)' : 'currentColor'}
        strokeWidth="2.5"
      />
      <line
        x1="-3"
        y1="18"
        x2="3"
        y2="18"
        stroke={highlighted ? 'var(--primary-active, #3b82f6)' : 'currentColor'}
        strokeWidth="2.5"
      />

      {label && (
        <text x="0" y="28" textAnchor="middle" fontSize="9" fill="currentColor">
          {label}
        </text>
      )}
    </g>
  );
};

// 19. Fuse Component (IEC Standard: Rectangular box with axial center line)
export const SchematicFuse: React.FC<SchematicComponentProps> = (props) => {
  const { x, y, rotation = 0, label, subLabel, highlighted } = props;
  const interactive = getInteractiveProps(props);

  return (
    <g transform={`translate(${x}, ${y}) rotate(${rotation})`} {...interactive}>
      <rect x="-40" y="-15" width="80" height="30" fill="transparent" stroke="none" />
      <line x1="-40" y1="0" x2="-15" y2="0" stroke="currentColor" strokeWidth="2" />
      <line x1="15" y1="0" x2="40" y2="0" stroke="currentColor" strokeWidth="2" />
      <rect
        x="-15"
        y="-6"
        width="30"
        height="12"
        fill={highlighted ? 'var(--primary-glow-bg, rgba(59, 130, 246, 0.1))' : 'var(--bg-card, #1e293b)'}
        stroke={highlighted ? 'var(--primary-active, #3b82f6)' : 'currentColor'}
        strokeWidth="2"
      />
      <line x1="-15" y1="0" x2="15" y2="0" stroke="currentColor" strokeWidth="1.5" />
      <SchematicLabel label={label} subLabel={subLabel} rotation={rotation} />
    </g>
  );
};

// 20. NTC Thermistor Component
export const SchematicNtc: React.FC<SchematicComponentProps> = (props) => {
  const { x, y, rotation = 0, label, subLabel, highlighted } = props;
  const interactive = getInteractiveProps(props);

  return (
    <g transform={`translate(${x}, ${y}) rotate(${rotation})`} {...interactive}>
      <rect x="-40" y="-15" width="80" height="30" fill="transparent" stroke="none" />
      <line x1="-40" y1="0" x2="-15" y2="0" stroke="currentColor" strokeWidth="2" />
      <line x1="15" y1="0" x2="40" y2="0" stroke="currentColor" strokeWidth="2" />
      <rect
        x="-15"
        y="-6"
        width="30"
        height="12"
        fill={highlighted ? 'var(--primary-glow-bg, rgba(59, 130, 246, 0.1))' : 'var(--bg-card, #1e293b)'}
        stroke={highlighted ? 'var(--primary-active, #3b82f6)' : 'currentColor'}
        strokeWidth="2"
      />
      <line x1="-20" y1="10" x2="20" y2="-10" stroke="currentColor" strokeWidth="1.5" />
      <line x1="-20" y1="10" x2="-14" y2="10" stroke="currentColor" strokeWidth="1.5" />
      <text x="8" y="-12" fill="currentColor" fontSize="8" fontStyle="italic" fontWeight="bold">-t°</text>
      <SchematicLabel label={label} subLabel={subLabel} rotation={rotation} />
    </g>
  );
};

// 21. TVS Transient Voltage Suppressor Diode
export const SchematicTvsDiode: React.FC<SchematicComponentProps> = (props) => {
  const { x, y, rotation = 0, label, subLabel, highlighted } = props;
  const interactive = getInteractiveProps(props);

  return (
    <g transform={`translate(${x}, ${y}) rotate(${rotation})`} {...interactive}>
      <rect x="-40" y="-20" width="80" height="40" fill="transparent" stroke="none" />
      <line x1="-40" y1="0" x2="-10" y2="0" stroke="currentColor" strokeWidth="2" />
      <line x1="10" y1="0" x2="40" y2="0" stroke="currentColor" strokeWidth="2" />
      <polygon
        points="-10,-10 0,0 -10,10"
        fill={highlighted ? 'var(--primary-glow-bg, rgba(59, 130, 246, 0.1))' : 'var(--bg-card, #1e293b)'}
        stroke={highlighted ? 'var(--primary-active, #3b82f6)' : 'currentColor'}
        strokeWidth="2"
      />
      <polygon
        points="10,-10 0,0 10,10"
        fill={highlighted ? 'var(--primary-glow-bg, rgba(59, 130, 246, 0.1))' : 'var(--bg-card, #1e293b)'}
        stroke={highlighted ? 'var(--primary-active, #3b82f6)' : 'currentColor'}
        strokeWidth="2"
      />
      <path
        d="M -4 -10 L 0 -10 L 0 10 L 4 10"
        fill="none"
        stroke={highlighted ? 'var(--primary-active, #3b82f6)' : 'currentColor'}
        strokeWidth="2"
      />
      <SchematicLabel label={label} subLabel={subLabel} rotation={rotation} />
    </g>
  );
};
