import React, { useState, useEffect, useRef } from 'react';
import { Button } from './ui/Button';
import { OrthogonalWire } from './ui/SchematicCanvas';
import {
  SchematicResistor,
  SchematicCapacitor,
  SchematicDCSource,
  SchematicGround,
  SchematicLabel
} from './ui/SchematicSymbols';
import type { SchematicComponentProps } from './ui/SchematicSymbols';
import { RefreshCw, Cpu } from 'lucide-react';

const getInteractiveProps = (props: any) => {
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

export const SchematicOpAmp: React.FC<SchematicComponentProps> = (props) => {
  const { x, y, rotation = 0, label, subLabel, highlighted } = props;
  const interactive = getInteractiveProps(props);
  return (
    <g transform={`translate(${x}, ${y}) rotate(${rotation})`} {...interactive}>
      <rect x="-40" y="-30" width="80" height="60" fill="transparent" stroke="none" />
      <polygon points="-30,-25 -30,25 10,0" fill="#0f172a" stroke="currentColor" strokeWidth="1.5" />
      <text x="-25" y="-10" fontSize="10" fill="currentColor" fontWeight="bold">-</text>
      <text x="-25" y="14" fontSize="10" fill="currentColor" fontWeight="bold">+</text>
      <line x1="-40" y1="-10" x2="-30" y2="-10" stroke="currentColor" strokeWidth="1.5" />
      <line x1="-40" y1="10" x2="-30" y2="10" stroke="currentColor" strokeWidth="1.5" />
      <line x1="10" y1="0" x2="40" y2="0" stroke="currentColor" strokeWidth="1.5" />
      <SchematicLabel label={label} subLabel={subLabel} rotation={rotation} />
      {highlighted && (
        <rect x="-42" y="-32" width="84" height="64" fill="none" stroke="var(--primary-active, #3b82f6)" strokeWidth="1.5" strokeDasharray="4 3" className="animate-pulse" />
      )}
    </g>
  );
};

export const SchematicTL431: React.FC<SchematicComponentProps> = (props) => {
  const { x, y, rotation = 0, label, subLabel, highlighted } = props;
  const interactive = getInteractiveProps(props);
  return (
    <g transform={`translate(${x}, ${y}) rotate(${rotation})`} {...interactive}>
      <rect x="-30" y="-30" width="60" height="60" fill="transparent" stroke="none" />
      <line x1="0" y1="-30" x2="0" y2="-10" stroke="currentColor" strokeWidth="1.5" />
      <polygon points="-10,-10 10,-10 0,10" fill="#0f172a" stroke="currentColor" strokeWidth="1.5" />
      <line x1="-12" y1="10" x2="12" y2="10" stroke="currentColor" strokeWidth="2" />
      <line x1="12" y1="10" x2="12" y2="6" stroke="currentColor" strokeWidth="2" />
      <line x1="-12" y1="10" x2="-12" y2="14" stroke="currentColor" strokeWidth="2" />
      <line x1="0" y1="10" x2="0" y2="30" stroke="currentColor" strokeWidth="1.5" />
      <line x1="-30" y1="-2" x2="-5" y2="-2" stroke="currentColor" strokeWidth="1.5" />
      <line x1="-5" y1="-2" x2="-5" y2="0" stroke="currentColor" strokeWidth="1.5" />
      <SchematicLabel label={label} subLabel={subLabel} rotation={rotation} />
      {highlighted && (
        <rect x="-32" y="-32" width="64" height="64" fill="none" stroke="var(--primary-active, #3b82f6)" strokeWidth="1.5" strokeDasharray="4 3" className="animate-pulse" />
      )}
    </g>
  );
};

export const SchematicOptocoupler: React.FC<SchematicComponentProps> = (props) => {
  const { x, y, rotation = 0, label, subLabel, highlighted } = props;
  const interactive = getInteractiveProps(props);
  return (
    <g transform={`translate(${x}, ${y}) rotate(${rotation})`} {...interactive}>
      <rect x="-40" y="-30" width="80" height="60" fill="transparent" stroke="none" />
      <rect x="-35" y="-25" width="70" height="50" fill="none" stroke="currentColor" strokeWidth="1.5" rx="5" strokeDasharray="4 2" />
      <line x1="-40" y1="-10" x2="-20" y2="-10" stroke="currentColor" strokeWidth="1.5" />
      <line x1="-40" y1="10" x2="-20" y2="10" stroke="currentColor" strokeWidth="1.5" />
      <polygon points="-20,-10 -20,10 -10,0" fill="#0f172a" stroke="currentColor" strokeWidth="1.5" />
      <line x1="-10" y1="-10" x2="-10" y2="10" stroke="currentColor" strokeWidth="2" />
      <line x1="-10" y1="0" x2="-5" y2="0" stroke="currentColor" strokeWidth="1.5" />
      
      <line x1="40" y1="-15" x2="20" y2="-15" stroke="currentColor" strokeWidth="1.5" />
      <line x1="40" y1="15" x2="20" y2="15" stroke="currentColor" strokeWidth="1.5" />
      <line x1="20" y1="-15" x2="20" y2="15" stroke="currentColor" strokeWidth="2" />
      <line x1="20" y1="0" x2="10" y2="0" stroke="currentColor" strokeWidth="1.5" />
      <polygon points="12,-5 18,0 12,5" fill="currentColor" />
      
      <path d="M -2,-8 L 8,-3" stroke="currentColor" strokeWidth="1" />
      <path d="M -2,-2 L 8,3" stroke="currentColor" strokeWidth="1" />
      
      <SchematicLabel label={label} subLabel={subLabel} rotation={rotation} />
      {highlighted && (
        <rect x="-42" y="-32" width="84" height="64" fill="none" stroke="var(--primary-active, #3b82f6)" strokeWidth="1.5" strokeDasharray="4 3" className="animate-pulse" />
      )}
    </g>
  );
};

export const SchematicNode: React.FC<SchematicComponentProps> = (props) => {
  const { x, y, rotation = 0, label, subLabel, highlighted } = props;
  const interactive = getInteractiveProps(props);
  return (
    <g transform={`translate(${x}, ${y}) rotate(${rotation})`} {...interactive}>
      <circle cx="0" cy="0" r="4" fill="#10b981" />
      <circle cx="0" cy="0" r="10" fill="transparent" stroke="none" />
      <SchematicLabel label={label} subLabel={subLabel} rotation={rotation} />
      {highlighted && (
        <circle cx="0" cy="0" r="8" fill="none" stroke="var(--primary-active, #3b82f6)" strokeWidth="1.5" strokeDasharray="3 2" className="animate-pulse" />
      )}
    </g>
  );
};

interface Flyline {
  from: string;
  to: string;
  fromCoords: { x: number; y: number };
  toCoords: { x: number; y: number };
}

interface LoopCompensationSchematicSandboxProps {
  activeTab: string;
  t2R1: number;
  t2Result: any;
  t3R1: number;
  t3Result: any;
  tlResult: any;
  tlVout: number;
  dcRled: number;
  tlDcResult: any;
  hvResult: any;
  digResult: any;
  digControllerType: string;
}

function fmtRes(val: number): string {
  if (val >= 1e6) return `${(val / 1e6).toFixed(2)} MΩ`;
  if (val >= 1e3) return `${(val / 1e3).toFixed(2)} kΩ`;
  return `${val.toFixed(1)} Ω`;
}

function fmtCap(val: number): string {
  if (val >= 1e-6) return `${(val * 1e6).toFixed(2)} μF`;
  if (val >= 1e-9) return `${(val * 1e9).toFixed(2)} nF`;
  return `${(val * 1e12).toFixed(1)} pF`;
}

function getGlobalPinCoords(
  compX: number,
  compY: number,
  rotation: number,
  localX: number,
  localY: number
) {
  const rad = (rotation * Math.PI) / 180;
  const cos = Math.cos(rad);
  const sin = Math.sin(rad);
  const gx = Math.round(compX + localX * cos - localY * sin);
  const gy = Math.round(compY + localX * sin + localY * cos);
  return { x: gx, y: gy };
}

function getPinDirection(pinId: string, rotation: number): 'V' | 'H' {
  const compId = pinId.split('.')[0];
  if (compId.endsWith('GND') || compId === 'GND') return 'V';
  if (compId === 'Vin' || compId === 'Vcomp' || compId === 'Vcc') return 'H';
  return (rotation % 180 === 0) ? 'H' : 'V';
}

export default function LoopCompensationSchematicSandbox({
  activeTab,
  t2R1,
  t2Result,
  t3R1,
  t3Result,
  tlResult,
  tlVout,
  dcRled,
  tlDcResult,
  hvResult,
  digResult,
  digControllerType
}: LoopCompensationSchematicSandboxProps) {
  const templatesByTab: { [tab: string]: { [comp: string]: { [pin: string]: { x: number; y: number } } } } = {
    type2: {
      Vin: { P: { x: -40, y: 0 }, N: { x: 40, y: 0 } },
      R1: { Pin1: { x: -40, y: 0 }, Pin2: { x: 40, y: 0 } },
      OpAmp: { InMinus: { x: -40, y: -10 }, InPlus: { x: -40, y: 10 }, Out: { x: 40, y: 0 } },
      Vref: { P: { x: -40, y: 0 }, N: { x: 40, y: 0 } },
      R3: { Pin1: { x: -40, y: 0 }, Pin2: { x: 40, y: 0 } },
      C1: { P: { x: -40, y: 0 }, N: { x: 40, y: 0 } },
      C2: { P: { x: -40, y: 0 }, N: { x: 40, y: 0 } },
      Vcomp: { Pin: { x: 0, y: 0 } },
      GND: { Pin: { x: 0, y: 0 } }
    },
    type3: {
      Vin: { P: { x: -40, y: 0 }, N: { x: 40, y: 0 } },
      R1: { Pin1: { x: -40, y: 0 }, Pin2: { x: 40, y: 0 } },
      R2: { Pin1: { x: -40, y: 0 }, Pin2: { x: 40, y: 0 } },
      C3: { P: { x: -40, y: 0 }, N: { x: 40, y: 0 } },
      OpAmp: { InMinus: { x: -40, y: -10 }, InPlus: { x: -40, y: 10 }, Out: { x: 40, y: 0 } },
      Vref: { P: { x: -40, y: 0 }, N: { x: 40, y: 0 } },
      R3: { Pin1: { x: -40, y: 0 }, Pin2: { x: 40, y: 0 } },
      C1: { P: { x: -40, y: 0 }, N: { x: 40, y: 0 } },
      C2: { P: { x: -40, y: 0 }, N: { x: 40, y: 0 } },
      Vcomp: { Pin: { x: 0, y: 0 } },
      GND: { Pin: { x: 0, y: 0 } }
    },
    tl431: {
      Vin: { P: { x: -40, y: 0 }, N: { x: 40, y: 0 } },
      R_up: { Pin1: { x: -40, y: 0 }, Pin2: { x: 40, y: 0 } },
      R_led: { Pin1: { x: -40, y: 0 }, Pin2: { x: 40, y: 0 } },
      Opto: { A: { x: -40, y: -10 }, K: { x: -40, y: 10 }, C: { x: 40, y: -15 }, E: { x: 40, y: 15 } },
      TL431: { Ref: { x: -30, y: -2 }, Cathode: { x: 0, y: -20 }, Anode: { x: 0, y: 20 } },
      R_comp: { Pin1: { x: -40, y: 0 }, Pin2: { x: 40, y: 0 } },
      C_comp: { P: { x: -40, y: 0 }, N: { x: 40, y: 0 } },
      C_hf: { P: { x: -40, y: 0 }, N: { x: 40, y: 0 } },
      R_pull: { Pin1: { x: -40, y: 0 }, Pin2: { x: 40, y: 0 } },
      Vcc: { P: { x: -40, y: 0 }, N: { x: 40, y: 0 } },
      Vcomp: { Pin: { x: 0, y: 0 } },
      GND: { Pin: { x: 0, y: 0 } }
    },
    hv: {
      Vin: { P: { x: -40, y: 0 }, N: { x: 40, y: 0 } },
      R1: { Pin1: { x: -40, y: 0 }, Pin2: { x: 40, y: 0 } },
      C1: { P: { x: -40, y: 0 }, N: { x: 40, y: 0 } },
      R2: { Pin1: { x: -40, y: 0 }, Pin2: { x: 40, y: 0 } },
      C2: { P: { x: -40, y: 0 }, N: { x: 40, y: 0 } },
      Vout: { Pin: { x: 0, y: 0 } },
      GND: { Pin: { x: 0, y: 0 } }
    }
  };

  const currentTemplates = templatesByTab[activeTab] || {};
  const allPins = Object.entries(currentTemplates).flatMap(([compId, template]) =>
    Object.keys(template).map(pinName => `${compId}.${pinName}`)
  );

  const netGroupsByTab: { [tab: string]: { [net: string]: string[] } } = {
    type2: {
      Net_Vout: ['Vin.P', 'R1.Pin1'],
      Net_InMinus: ['R1.Pin2', 'OpAmp.InMinus', 'R3.Pin1', 'C2.P'],
      Net_Series_Mid: ['R3.Pin2', 'C1.P'],
      Net_Vcomp: ['C1.N', 'C2.N', 'OpAmp.Out', 'Vcomp.Pin'],
      Net_Vref: ['Vref.P', 'OpAmp.InPlus'],
      Net_GND: ['Vin.N', 'Vref.N', 'GND.Pin']
    },
    type3: {
      Net_Vout: ['Vin.P', 'R1.Pin1', 'C3.P'],
      Net_Feedforward_Mid: ['C3.N', 'R2.Pin1'],
      Net_InMinus: ['R1.Pin2', 'R2.Pin2', 'OpAmp.InMinus', 'R3.Pin1', 'C2.P'],
      Net_Series_Mid: ['R3.Pin2', 'C1.P'],
      Net_Vcomp: ['C1.N', 'C2.N', 'OpAmp.Out', 'Vcomp.Pin'],
      Net_Vref: ['Vref.P', 'OpAmp.InPlus'],
      Net_GND: ['Vin.N', 'Vref.N', 'GND.Pin']
    },
    tl431: {
      Net_Vout: ['Vin.P', 'R_up.Pin1', 'R_led.Pin1'],
      Net_Ref: ['R_up.Pin2', 'TL431.Ref', 'R_comp.Pin1', 'C_hf.P'],
      Net_Cathode: ['TL431.Cathode', 'Opto.K', 'C_comp.N', 'C_hf.N'],
      Net_Series_Mid: ['R_comp.Pin2', 'C_comp.P'],
      Net_LED_Anode: ['R_led.Pin2', 'Opto.A'],
      Net_Vcomp: ['Opto.C', 'R_pull.Pin2', 'Vcomp.Pin'],
      Net_Vcc: ['Vcc.P', 'R_pull.Pin1'],
      Net_GND: ['Vin.N', 'TL431.Anode', 'Opto.E', 'Vcc.N', 'GND.Pin']
    },
    hv: {
      Net_Vin: ['Vin.P', 'R1.Pin1', 'C1.P'],
      Net_Vout: ['R1.Pin2', 'C1.N', 'R2.Pin1', 'C2.P', 'Vout.Pin'],
      Net_GND: ['Vin.N', 'R2.Pin2', 'C2.N', 'GND.Pin']
    }
  };

  const currentNetGroups = netGroupsByTab[activeTab] || {};
  const pinToNetGroup: { [pin: string]: string } = {};
  Object.entries(currentNetGroups).forEach(([net, pins]) => {
    pins.forEach(pin => {
      pinToNetGroup[pin] = net;
    });
  });

  const defaultPositions: { [tab: string]: { [key: string]: { x: number; y: number; rotation: number } } } = {
    type2: {
      Vin: { x: 60, y: 150, rotation: 270 },
      R1: { x: 180, y: 150, rotation: 0 },
      OpAmp: { x: 300, y: 200, rotation: 0 },
      Vref: { x: 200, y: 260, rotation: 270 },
      R3: { x: 230, y: 70, rotation: 0 },
      C1: { x: 340, y: 70, rotation: 0 },
      C2: { x: 285, y: 20, rotation: 0 },
      Vcomp: { x: 440, y: 200, rotation: 90 },
      GND: { x: 60, y: 310, rotation: 0 }
    },
    type3: {
      Vin: { x: 60, y: 150, rotation: 270 },
      R1: { x: 170, y: 110, rotation: 0 },
      R2: { x: 280, y: 160, rotation: 0 },
      C3: { x: 170, y: 160, rotation: 0 },
      OpAmp: { x: 390, y: 210, rotation: 0 },
      Vref: { x: 290, y: 270, rotation: 270 },
      R3: { x: 300, y: 70, rotation: 0 },
      C1: { x: 400, y: 70, rotation: 0 },
      C2: { x: 350, y: 20, rotation: 0 },
      Vcomp: { x: 500, y: 210, rotation: 90 },
      GND: { x: 60, y: 310, rotation: 0 }
    },
    tl431: {
      Vin: { x: 60, y: 130, rotation: 270 },
      R_up: { x: 180, y: 110, rotation: 90 },
      R_led: { x: 270, y: 80, rotation: 0 },
      Opto: { x: 390, y: 120, rotation: 0 },
      TL431: { x: 290, y: 230, rotation: 0 },
      R_comp: { x: 200, y: 230, rotation: 0 },
      C_comp: { x: 200, y: 290, rotation: 0 },
      C_hf: { x: 130, y: 250, rotation: 90 },
      R_pull: { x: 470, y: 120, rotation: 90 },
      Vcc: { x: 470, y: 40, rotation: 270 },
      Vcomp: { x: 540, y: 150, rotation: 90 },
      GND: { x: 390, y: 330, rotation: 0 }
    },
    hv: {
      Vin: { x: 80, y: 160, rotation: 270 },
      R1: { x: 200, y: 110, rotation: 0 },
      C1: { x: 200, y: 50, rotation: 0 },
      R2: { x: 300, y: 160, rotation: 90 },
      C2: { x: 360, y: 160, rotation: 90 },
      Vout: { x: 440, y: 110, rotation: 90 },
      GND: { x: 300, y: 280, rotation: 0 }
    }
  };

  const defaultWires: { [tab: string]: { from: string; to: string }[] } = {
    type2: [
      { from: 'Vin.P', to: 'R1.Pin1' },
      { from: 'R1.Pin2', to: 'OpAmp.InMinus' },
      { from: 'OpAmp.InMinus', to: 'R3.Pin1' },
      { from: 'OpAmp.InMinus', to: 'C2.P' },
      { from: 'R3.Pin2', to: 'C1.P' },
      { from: 'C1.N', to: 'OpAmp.Out' },
      { from: 'C2.N', to: 'OpAmp.Out' },
      { from: 'OpAmp.Out', to: 'Vcomp.Pin' },
      { from: 'Vref.P', to: 'OpAmp.InPlus' },
      { from: 'Vin.N', to: 'GND.Pin' },
      { from: 'Vref.N', to: 'GND.Pin' }
    ],
    type3: [
      { from: 'Vin.P', to: 'R1.Pin1' },
      { from: 'Vin.P', to: 'C3.P' },
      { from: 'C3.N', to: 'R2.Pin1' },
      { from: 'R1.Pin2', to: 'OpAmp.InMinus' },
      { from: 'R2.Pin2', to: 'OpAmp.InMinus' },
      { from: 'OpAmp.InMinus', to: 'R3.Pin1' },
      { from: 'OpAmp.InMinus', to: 'C2.P' },
      { from: 'R3.Pin2', to: 'C1.P' },
      { from: 'C1.N', to: 'OpAmp.Out' },
      { from: 'C2.N', to: 'OpAmp.Out' },
      { from: 'OpAmp.Out', to: 'Vcomp.Pin' },
      { from: 'Vref.P', to: 'OpAmp.InPlus' },
      { from: 'Vin.N', to: 'GND.Pin' },
      { from: 'Vref.N', to: 'GND.Pin' }
    ],
    tl431: [
      { from: 'Vin.P', to: 'R_up.Pin1' },
      { from: 'Vin.P', to: 'R_led.Pin1' },
      { from: 'R_up.Pin2', to: 'TL431.Ref' },
      { from: 'TL431.Ref', to: 'R_comp.Pin1' },
      { from: 'TL431.Ref', to: 'C_hf.P' },
      { from: 'R_comp.Pin2', to: 'C_comp.P' },
      { from: 'C_comp.N', to: 'TL431.Cathode' },
      { from: 'C_hf.N', to: 'TL431.Cathode' },
      { from: 'TL431.Cathode', to: 'Opto.K' },
      { from: 'R_led.Pin2', to: 'Opto.A' },
      { from: 'Vcc.P', to: 'R_pull.Pin1' },
      { from: 'Opto.C', to: 'R_pull.Pin2' },
      { from: 'Opto.C', to: 'Vcomp.Pin' },
      { from: 'Vin.N', to: 'GND.Pin' },
      { from: 'TL431.Anode', to: 'GND.Pin' },
      { from: 'Opto.E', to: 'GND.Pin' },
      { from: 'Vcc.N', to: 'GND.Pin' }
    ],
    hv: [
      { from: 'Vin.P', to: 'R1.Pin1' },
      { from: 'Vin.P', to: 'C1.P' },
      { from: 'R1.Pin2', to: 'R2.Pin1' },
      { from: 'C1.N', to: 'R2.Pin1' },
      { from: 'R2.Pin1', to: 'C2.P' },
      { from: 'R2.Pin1', to: 'Vout.Pin' },
      { from: 'Vin.N', to: 'GND.Pin' },
      { from: 'R2.Pin2', to: 'GND.Pin' },
      { from: 'C2.N', to: 'GND.Pin' }
    ]
  };

  const [componentsPos, setComponentsPos] = useState<{ [key: string]: { x: number; y: number; rotation: number } }>(() => {
    const saved = localStorage.getItem(`toolbox_loop_layout_pos_${activeTab}`);
    if (saved) {
      try { return JSON.parse(saved); } catch (e) { console.error("Error loading layout pos", e); }
    }
    return defaultPositions[activeTab] || {};
  });

  const [wires, setWires] = useState<{ from: string; to: string }[]>(() => {
    const saved = localStorage.getItem(`toolbox_loop_layout_wires_${activeTab}`);
    if (saved) {
      try { return JSON.parse(saved); } catch (e) { console.error("Error loading layout wires", e); }
    }
    return defaultWires[activeTab] || [];
  });

  const [activeDragComponent, setActiveDragComponent] = useState<string | null>(null);
  const [dragStartPin, setDragStartPin] = useState<string | null>(null);
  const [tempWireEnd, setTempWireEnd] = useState<{ x: number; y: number } | null>(null);
  const [snapTargetPin, setSnapTargetPin] = useState<string | null>(null);
  const [hoveredComponent, setHoveredComponent] = useState<string | null>(null);
  const [hoveredWire, setHoveredWire] = useState<number | null>(null);

  const dragStartOffset = useRef({ x: 0, y: 0 });
  const svgRef = useRef<SVGSVGElement | null>(null);
  const [saveTip, setSaveTip] = useState<string | null>(null);

  useEffect(() => {
    const savedPos = localStorage.getItem(`toolbox_loop_layout_pos_${activeTab}`);
    const savedWires = localStorage.getItem(`toolbox_loop_layout_wires_${activeTab}`);
    if (savedPos) {
      try { setComponentsPos(JSON.parse(savedPos)); } catch (e) { setComponentsPos(defaultPositions[activeTab] || {}); }
    } else {
      setComponentsPos(defaultPositions[activeTab] || {});
    }
    if (savedWires) {
      try { setWires(JSON.parse(savedWires)); } catch (e) { setWires(defaultWires[activeTab] || []); }
    } else {
      setWires(defaultWires[activeTab] || []);
    }
  }, [activeTab]);

  useEffect(() => {
    if (Object.keys(componentsPos).length > 0) {
      localStorage.setItem(`toolbox_loop_layout_pos_${activeTab}`, JSON.stringify(componentsPos));
    }
  }, [componentsPos, activeTab]);

  useEffect(() => {
    localStorage.setItem(`toolbox_loop_layout_wires_${activeTab}`, JSON.stringify(wires));
  }, [wires, activeTab]);

  const getPinCoordsMap = (posMap: typeof componentsPos) => {
    const coords = new Map<string, { x: number; y: number }>();
    for (const [compId, template] of Object.entries(currentTemplates)) {
      const pos = posMap[compId];
      if (!pos) continue;
      for (const [pinName, local] of Object.entries(template)) {
        const global = getGlobalPinCoords(pos.x, pos.y, pos.rotation, local.x, local.y);
        coords.set(`${compId}.${pinName}`, global);
      }
    }
    return coords;
  };

  const allPinCoords = getPinCoordsMap(componentsPos);

  const getRatsnestLines = (): Flyline[] => {
    const parent = new Map<string, string>();
    for (const pin of allPins) {
      parent.set(pin, pin);
    }

    const find = (i: string): string => {
      const p = parent.get(i);
      if (!p || p === i) return i;
      const root = find(p);
      parent.set(i, root);
      return root;
    };

    const union = (i: string, j: string) => {
      const rootI = find(i);
      const rootJ = find(j);
      if (rootI !== rootJ) {
        parent.set(rootI, rootJ);
      }
    };

    wires.forEach(wire => {
      if (parent.has(wire.from) && parent.has(wire.to)) {
        union(wire.from, wire.to);
      }
    });

    const lines: Flyline[] = [];
    Object.values(currentNetGroups).forEach(groupPins => {
      const components = new Map<string, string[]>();
      groupPins.forEach(pin => {
        const root = find(pin);
        if (!components.has(root)) components.set(root, []);
        components.get(root)!.push(pin);
      });

      const compList = Array.from(components.values());
      if (compList.length > 1) {
        for (let i = 0; i < compList.length - 1; i++) {
          const p1 = compList[i][0];
          const p2 = compList[i + 1][0];
          const c1 = allPinCoords.get(p1);
          const c2 = allPinCoords.get(p2);
          if (c1 && c2) {
            lines.push({
              from: p1,
              to: p2,
              fromCoords: c1,
              toCoords: c2
            });
          }
        }
      }
    });

    return lines;
  };

  const ratsnestLines = getRatsnestLines();

  const getSvgCoordinates = (e: React.MouseEvent) => {
    if (!svgRef.current) return { x: 0, y: 0 };
    const pt = svgRef.current.createSVGPoint();
    pt.x = e.clientX;
    pt.y = e.clientY;
    const transformed = pt.matrixTransform(svgRef.current.getScreenCTM()?.inverse());
    return { x: Math.round(transformed.x), y: Math.round(transformed.y) };
  };

  const handleComponentMouseDown = (compId: string, e: React.MouseEvent) => {
    const coords = getSvgCoordinates(e);
    const pos = componentsPos[compId];
    if (pos) {
      dragStartOffset.current = { x: coords.x - pos.x, y: coords.y - pos.y };
      setActiveDragComponent(compId);
    }
  };

  const handlePinMouseDown = (pinId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setDragStartPin(pinId);
    const coords = getSvgCoordinates(e);
    setTempWireEnd(coords);
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    const coords = getSvgCoordinates(e);
    if (activeDragComponent) {
      setComponentsPos(prev => ({
        ...prev,
        [activeDragComponent]: {
          ...prev[activeDragComponent],
          x: Math.max(20, Math.min(580, coords.x - dragStartOffset.current.x)),
          y: Math.max(20, Math.min(380, coords.y - dragStartOffset.current.y))
        }
      }));
    } else if (dragStartPin) {
      setTempWireEnd(coords);
      let foundSnap: string | null = null;
      for (const [pinId, pinCoord] of allPinCoords.entries()) {
        if (pinId === dragStartPin) continue;
        if (pinId.split('.')[0] === dragStartPin.split('.')[0]) continue;
        const dist = Math.hypot(coords.x - pinCoord.x, coords.y - pinCoord.y);
        if (dist < 15) {
          foundSnap = pinId;
          break;
        }
      }
      setSnapTargetPin(foundSnap);
    }
  };

  const handleMouseUp = () => {
    if (dragStartPin && snapTargetPin) {
      const newWire = { from: dragStartPin, to: snapTargetPin };
      const exists = wires.some(
        w => (w.from === newWire.from && w.to === newWire.to) ||
             (w.from === newWire.to && w.to === newWire.from)
      );
      if (!exists) {
        setWires(prev => [...prev, newWire]);
      }
    }
    setActiveDragComponent(null);
    setDragStartPin(null);
    setTempWireEnd(null);
    setSnapTargetPin(null);
  };

  const handleComponentRotate = (compId: string) => {
    setComponentsPos(prev => ({
      ...prev,
      [compId]: {
        ...prev[compId],
        rotation: (prev[compId].rotation + 90) % 360
      }
    }));
  };

  const handleWireClick = (idx: number, e: React.MouseEvent) => {
    e.stopPropagation();
    setWires(prev => prev.filter((_, i) => i !== idx));
  };

  const handleResetLayout = () => {
    setComponentsPos(defaultPositions[activeTab] || {});
    setWires(defaultWires[activeTab] || []);
    localStorage.removeItem(`toolbox_loop_layout_pos_${activeTab}`);
    localStorage.removeItem(`toolbox_loop_layout_wires_${activeTab}`);
  };

  const handleSaveLayout = () => {
    localStorage.setItem(`toolbox_loop_layout_pos_${activeTab}`, JSON.stringify(componentsPos));
    localStorage.setItem(`toolbox_loop_layout_wires_${activeTab}`, JSON.stringify(wires));
    setSaveTip("💾 Schematic layout and wiring saved!");
    setTimeout(() => setSaveTip(null), 2500);
  };

  const getOrthogonalPoints = (fromId: string, toId: string): [number, number][] => {
    const start = allPinCoords.get(fromId);
    const end = allPinCoords.get(toId);
    if (!start || !end) return [];

    const rotFrom = componentsPos[fromId.split('.')[0]]?.rotation ?? 0;
    const rotTo = componentsPos[toId.split('.')[0]]?.rotation ?? 0;

    const dirFrom = getPinDirection(fromId, rotFrom);
    if (dirFrom === 'H') {
      return [
        [start.x, start.y],
        [(start.x + end.x) / 2, start.y],
        [(start.x + end.x) / 2, end.y],
        [end.x, end.y]
      ];
    } else {
      return [
        [start.x, start.y],
        [start.x, (start.y + end.y) / 2],
        [end.x, (start.y + end.y) / 2],
        [end.x, end.y]
      ];
    }
  };

  const getSubLabel = (compId: string): string => {
    if (activeTab === 'type2') {
      if (compId === 'Vin') return 'Vout';
      if (compId === 'R1') return `${t2R1.toFixed(1)} kΩ`;
      if (compId === 'R3') return t2Result?.design ? fmtRes(t2Result.design.r3_ohm) : '--';
      if (compId === 'C1') return t2Result?.design ? fmtCap(t2Result.design.c1_f) : '--';
      if (compId === 'C2') return t2Result?.design ? fmtCap(t2Result.design.c2_f) : '--';
    }
    if (activeTab === 'type3') {
      if (compId === 'Vin') return 'Vout';
      if (compId === 'R1') return `${t3R1.toFixed(1)} kΩ`;
      if (compId === 'R2') return t3Result?.design ? fmtRes(t3Result.design.r2_ohm) : '--';
      if (compId === 'C3') return t3Result?.design ? fmtCap(t3Result.design.c3_f) : '--';
      if (compId === 'R3') return t3Result?.design ? fmtRes(t3Result.design.r3_ohm) : '--';
      if (compId === 'C1') return t3Result?.design ? fmtCap(t3Result.design.c1_f) : '--';
      if (compId === 'C2') return t3Result?.design ? fmtCap(t3Result.design.c2_f) : '--';
    }
    if (activeTab === 'tl431') {
      if (compId === 'Vin') return `${tlVout.toFixed(1)} V`;
      if (compId === 'R_up') return tlResult?.design ? fmtRes(tlResult.design.r_upper_ohm ?? 10000) : '--';
      if (compId === 'R_led') return `${dcRled.toFixed(2)} kΩ`;
      if (compId === 'R_comp') return tlResult?.design ? fmtRes(tlResult.design.r_comp_ohm) : '--';
      if (compId === 'C_comp') return tlResult?.design ? fmtCap(tlResult.design.c_comp_f) : '--';
      if (compId === 'C_hf') return tlResult?.design ? fmtCap(tlResult.design.c_hf_f) : '--';
      if (compId === 'R_pull') return tlDcResult ? `${tlDcResult.rec_r_par_k > 0 ? tlDcResult.rec_r_par_k.toFixed(2) : '4.70'} kΩ` : '--';
    }
    if (activeTab === 'hv') {
      if (compId === 'R1') return '1.0 MΩ';
      if (compId === 'C1') return '10.0 pF';
      if (compId === 'R2') return '10.0 kΩ';
      if (compId === 'C2') return hvResult ? `${hvResult.c2_pf.toFixed(1)} pF` : '--';
    }
    return '';
  };

  if (activeTab === 'digital') {
    return (
      <div className="h-[280px] w-full flex flex-col items-center justify-center bg-slate-950/40 border border-slate-800 rounded-xl p-6 text-center">
        <Cpu className="w-10 h-10 text-cyan-400 mb-2 animate-bounce" />
        <span className="text-xs font-bold text-white mb-1">DSP / MCU Digital Control Loop Block Diagram</span>
        <p className="text-[10px] text-slate-400 max-w-[360px] leading-relaxed">
          The digital control loop is implemented via closed-loop difference recurrence algorithms (2P2Z/3P3Z) in software, without discrete op-amps and RC networks. Physical hardware utilizes high-precision ADC sampling, DSP math cores, and MCU PWM generators. Refer to the difference equation and C code panel for implementation templates.
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-2 h-full overflow-hidden">
      {/* Status indicator and action bar */}
      <div className="flex flex-row justify-between items-center gap-2 bg-slate-900/60 p-2.5 rounded-lg border border-slate-800 flex-shrink-0">
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-yellow-400 animate-pulse"></span>
          <span className="text-xs font-semibold text-slate-200">Interactive Schematic Sandbox Wiring DRC</span>
          {ratsnestLines.length === 0 ? (
            <span className="text-[9px] text-emerald-400 bg-emerald-950/40 border border-emerald-500/20 px-2 py-0.5 rounded ml-2">
              ✓ All connections valid
            </span>
          ) : (
            <span className="text-[9px] text-pink-400 bg-pink-950/40 border border-pink-500/20 px-2 py-0.5 rounded ml-2">
              ⚠ {ratsnestLines.length} open/unconnected pin(s) remaining
            </span>
          )}
        </div>
        <div className="flex items-center gap-1">
          {saveTip && <span className="text-[9px] text-emerald-400 mr-2 animate-fade-in">{saveTip}</span>}
          <Button onClick={handleSaveLayout} size="sm" variant="ghost" className="h-6 text-[9.5px] px-2 bg-slate-900 text-teal-400 hover:bg-slate-800">
            💾 Save Layout
          </Button>
          <Button onClick={handleResetLayout} size="sm" variant="ghost" className="h-6 text-[9.5px] px-2 bg-slate-900 text-slate-400 hover:bg-slate-800">
            <RefreshCw className="w-3 h-3 mr-1" />
            Reset
          </Button>
        </div>
      </div>

      {/* SVG Canvas */}
      <div className="flex-1 min-h-[220px] bg-slate-950 border border-slate-850 rounded-xl relative overflow-hidden">
        <svg
          ref={svgRef}
          width="100%"
          height="100%"
          viewBox="0 0 600 400"
          className="absolute inset-0 select-none text-slate-300"
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
        >
          <defs>
            <pattern id="grid-dots" width="20" height="20" patternUnits="userSpaceOnUse">
              <circle cx="2" cy="2" r="0.75" fill="rgba(255,255,255,0.06)" />
            </pattern>
            <marker id="arrow" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
              <path d="M 0 1 L 10 5 L 0 9 z" fill="currentColor" />
            </marker>
          </defs>
          <rect width="100%" height="100%" fill="url(#grid-dots)" />

          {wires.map((wire, idx) => {
            const points = getOrthogonalPoints(wire.from, wire.to);
            return (
              <g key={idx}>
                <OrthogonalWire
                  points={points}
                  highlighted={hoveredWire === idx}
                  color={hoveredWire === idx ? '#f43f5e' : '#475569'}
                  label={hoveredWire === idx ? 'Click to cut' : undefined}
                />
                <path
                  d={`M ${points.map(p => `${p[0]} ${p[1]}`).join(' L ')}`}
                  fill="none"
                  stroke="transparent"
                  strokeWidth="8"
                  className="cursor-pointer"
                  onMouseEnter={() => setHoveredWire(idx)}
                  onMouseLeave={() => setHoveredWire(null)}
                  onClick={(e) => handleWireClick(idx, e)}
                />
              </g>
            );
          })}

          {ratsnestLines.map((line, idx) => (
            <line
              key={`rats-${idx}`}
              x1={line.fromCoords.x}
              y1={line.fromCoords.y}
              x2={line.toCoords.x}
              y2={line.toCoords.y}
              stroke="#f43f5e"
              strokeWidth="1.2"
              strokeDasharray="4 3"
              opacity="0.7"
              className="pointer-events-none"
            />
          ))}

          {dragStartPin && tempWireEnd && (
            <line
              x1={allPinCoords.get(dragStartPin)!.x}
              y1={allPinCoords.get(dragStartPin)!.y}
              x2={tempWireEnd.x}
              y2={tempWireEnd.y}
              stroke={snapTargetPin ? '#10b981' : '#38bdf8'}
              strokeWidth="2"
              strokeDasharray="3 3"
              className="pointer-events-none"
            />
          )}

          {Array.from(allPinCoords.entries()).map(([pinId, coords]) => (
            <circle
              key={pinId}
              cx={coords.x}
              cy={coords.y}
              r={snapTargetPin === pinId ? 7 : 4}
              fill={snapTargetPin === pinId ? '#10b981' : dragStartPin === pinId ? '#38bdf8' : '#475569'}
              stroke="#0f172a"
              strokeWidth="1.5"
              className="cursor-crosshair hover:scale-125 transition-transform"
              onMouseDown={(e) => handlePinMouseDown(pinId, e)}
            />
          ))}

          {Object.entries(componentsPos).map(([compId, pos]) => {
            const labelStr = compId;
            const subLabelStr = getSubLabel(compId);
            const isHovered = hoveredComponent === compId;

            if (compId === 'Vin' || compId === 'Vcc') {
              return (
                <SchematicDCSource
                  key={compId}
                  x={pos.x}
                  y={pos.y}
                  rotation={pos.rotation}
                  label={labelStr}
                  subLabel={subLabelStr}
                  highlighted={isHovered}
                  onMouseDown={(e) => handleComponentMouseDown(compId, e)}
                  onDoubleClick={() => handleComponentRotate(compId)}
                />
              );
            }
            if (compId === 'GND') {
              return (
                <SchematicGround
                  key={compId}
                  x={pos.x}
                  y={pos.y}
                  label={labelStr}
                  highlighted={isHovered}
                  onMouseDown={(e) => handleComponentMouseDown(compId, e)}
                />
              );
            }
            if (compId.startsWith('R')) {
              return (
                <SchematicResistor
                  key={compId}
                  x={pos.x}
                  y={pos.y}
                  rotation={pos.rotation}
                  label={labelStr}
                  subLabel={subLabelStr}
                  highlighted={isHovered}
                  onMouseDown={(e) => handleComponentMouseDown(compId, e)}
                  onDoubleClick={() => handleComponentRotate(compId)}
                />
              );
            }
            if (compId.startsWith('C')) {
              return (
                <SchematicCapacitor
                  key={compId}
                  x={pos.x}
                  y={pos.y}
                  rotation={pos.rotation}
                  label={labelStr}
                  subLabel={subLabelStr}
                  highlighted={isHovered}
                  onMouseDown={(e) => handleComponentMouseDown(compId, e)}
                  onDoubleClick={() => handleComponentRotate(compId)}
                />
              );
            }
            if (compId === 'OpAmp') {
              return (
                <SchematicOpAmp
                  key={compId}
                  x={pos.x}
                  y={pos.y}
                  rotation={pos.rotation}
                  label={labelStr}
                  subLabel="Op-Amp"
                  highlighted={isHovered}
                  onMouseDown={(e) => handleComponentMouseDown(compId, e)}
                  onDoubleClick={() => handleComponentRotate(compId)}
                />
              );
            }
            if (compId === 'TL431') {
              return (
                <SchematicTL431
                  key={compId}
                  x={pos.x}
                  y={pos.y}
                  rotation={pos.rotation}
                  label={labelStr}
                  subLabel="TL431 Ref"
                  highlighted={isHovered}
                  onMouseDown={(e) => handleComponentMouseDown(compId, e)}
                  onDoubleClick={() => handleComponentRotate(compId)}
                />
              );
            }
            if (compId === 'Opto') {
              return (
                <SchematicOptocoupler
                  key={compId}
                  x={pos.x}
                  y={pos.y}
                  rotation={pos.rotation}
                  label={labelStr}
                  subLabel="Optocoupler"
                  highlighted={isHovered}
                  onMouseDown={(e) => handleComponentMouseDown(compId, e)}
                  onDoubleClick={() => handleComponentRotate(compId)}
                />
              );
            }
            if (compId === 'Vcomp' || compId === 'Vout') {
              return (
                <SchematicNode
                  key={compId}
                  x={pos.x}
                  y={pos.y}
                  rotation={pos.rotation}
                  label={labelStr}
                  highlighted={isHovered}
                  onMouseDown={(e) => handleComponentMouseDown(compId, e)}
                />
              );
            }
            return null;
          })}
        </svg>
      </div>

      {/* DRC Rule Validation Panel */}
      <div className="bg-slate-900/40 p-2.5 rounded-lg border border-slate-800 text-[10px] space-y-1 text-slate-400 flex-shrink-0">
        <span className="font-bold text-slate-300 block">Sandbox Wiring Physical DRC Validation:</span>
        {ratsnestLines.length === 0 ? (
          <p className="text-emerald-400 font-medium">✓ Loop continuity DRC check passed. All feedback RC components correctly routed with complete zero-pole paths.</p>
        ) : (
          <div className="space-y-1">
            <p className="text-yellow-400">⚠ Incomplete or open connections detected. Open loops will cause feedback failure:</p>
            <div className="grid grid-cols-2 gap-x-4 text-[9.5px] font-mono text-slate-300">
              {ratsnestLines.slice(0, 4).map((line, idx) => (
                <div key={idx} className="flex items-center gap-1.5 py-0.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-pink-500"></span>
                  <span>Connect: <span className="text-teal-400">{line.from}</span> ↔ <span className="text-teal-400">{line.to}</span></span>
                </div>
              ))}
              {ratsnestLines.length > 4 && <div>... and {ratsnestLines.length - 4} remaining pins</div>}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
