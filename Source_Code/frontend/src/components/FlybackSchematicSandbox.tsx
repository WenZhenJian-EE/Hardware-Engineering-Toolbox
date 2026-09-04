import React, { useState, useEffect, useRef } from 'react';
import katex from 'katex';
import 'katex/dist/katex.min.css';
import { Button } from './ui/Button';
import {
  SchematicCapacitorPolar,
  SchematicDCSource,
  SchematicDiode,
  SchematicGround,
  SchematicMosfetN,
  SchematicResistor,
  SchematicTransformer
} from './ui/SchematicSymbols';

interface Flyline {
  from: string;
  to: string;
  fromCoords: { x: number; y: number };
  toCoords: { x: number; y: number };
}

const Latex: React.FC<{ math: string; block?: boolean }> = ({ math, block = false }) => {
  const containerRef = useRef<HTMLSpanElement>(null);
  useEffect(() => {
    if (containerRef.current) {
      try {
        katex.render(math, containerRef.current, {
          displayMode: block,
          throwOnError: false,
        });
      } catch (err) {
        console.error(err);
      }
    }
  }, [math, block]);
  return <span ref={containerRef} className={block ? "block my-2 overflow-x-auto text-center" : "inline-block"} />;
};

interface FlybackSchematicSandboxProps {
  vin: number;
  setVin: (v: number) => void;
  vor: number;
  setVor: (v: number) => void;
  vout: number;
  setVout: (v: number) => void;
  iout: number;
  setIout: (v: number) => void;
  fsw: number;
  setFsw: (v: number) => void;
  krf: number;
  setKrf: (v: number) => void;
  bmax: number;
  setBmax: (v: number) => void;
  ae: number;
  setAe: (v: number) => void;
  lpUh: string;
  setLpUh: (v: string) => void;
  cUf: string;
  setCUf: (v: string) => void;
  rcEsr: number;
  setRcEsr: (v: number) => void;
  rcdLlk: number;
  setRcdLlk: (v: number) => void;
  rcdVspike: number;
  setRcdVspike: (v: number) => void;
  calcData: any;
}

const componentTemplates: { [key: string]: { [pin: string]: { x: number; y: number } } } = {
  Vin: { P: { x: -40, y: 0 }, N: { x: 40, y: 0 } },
  Cin: { P: { x: -40, y: 0 }, N: { x: 40, y: 0 } },
  R_clamp: { Pin1: { x: -40, y: 0 }, Pin2: { x: 40, y: 0 } },
  C_clamp: { P: { x: -40, y: 0 }, N: { x: 40, y: 0 } },
  D_clamp: { A: { x: -40, y: 0 }, K: { x: 40, y: 0 } },
  Q1: { D: { x: 0, y: -40 }, S: { x: 0, y: 40 } },
  T1: { Pri1: { x: -40, y: -25 }, Pri2: { x: -40, y: 25 }, Sec2: { x: 40, y: -25 }, Sec1: { x: 40, y: 25 } },
  D1: { A: { x: -40, y: 0 }, K: { x: 40, y: 0 } },
  Cout: { P: { x: -40, y: 0 }, N: { x: 40, y: 0 } },
  RL: { Pin1: { x: -40, y: 0 }, Pin2: { x: 40, y: 0 } },
  GND: { Pin: { x: 0, y: 0 } },
  GND_sec: { Pin: { x: 0, y: 0 } }
};

const allPins = [
  "Vin.P", "Vin.N",
  "Cin.P", "Cin.N",
  "R_clamp.Pin1", "R_clamp.Pin2",
  "C_clamp.P", "C_clamp.N",
  "D_clamp.A", "D_clamp.K",
  "Q1.D", "Q1.S",
  "T1.Pri1", "T1.Pri2", "T1.Sec2", "T1.Sec1",
  "D1.A", "D1.K",
  "Cout.P", "Cout.N",
  "RL.Pin1", "RL.Pin2",
  "GND.Pin", "GND_sec.Pin"
];

const pinToNetGroup: { [pin: string]: string } = {
  "Vin.P": "Net_Vin", "Cin.P": "Net_Vin", "R_clamp.Pin1": "Net_Vin", "C_clamp.P": "Net_Vin", "T1.Pri1": "Net_Vin",
  "T1.Pri2": "Net_SW_Pri", "Q1.D": "Net_SW_Pri", "D_clamp.A": "Net_SW_Pri",
  "D_clamp.K": "Net_Clamp", "R_clamp.Pin2": "Net_Clamp", "C_clamp.N": "Net_Clamp",
  "Vin.N": "Net_PGND", "Cin.N": "Net_PGND", "Q1.S": "Net_PGND", "GND.Pin": "Net_PGND",
  "T1.Sec2": "Net_SW_Sec", "D1.A": "Net_SW_Sec",
  "D1.K": "Net_Vout", "Cout.P": "Net_Vout", "RL.Pin1": "Net_Vout",
  "T1.Sec1": "Net_SGND", "Cout.N": "Net_SGND", "RL.Pin2": "Net_SGND", "GND_sec.Pin": "Net_SGND"
};

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
  if (compId === 'GND' || compId === 'GND_sec') return 'V';
  if (compId === 'Vin' || compId === 'Cin' || compId === 'Cout' || compId === 'RL') {
    return rotation % 180 === 90 ? 'V' : 'H';
  }
  if (compId === 'R_clamp' || compId === 'C_clamp') {
    return rotation % 180 === 90 ? 'V' : 'H';
  }
  if (compId === 'D_clamp') {
    return rotation % 180 === 90 ? 'H' : 'V';
  }
  if (compId === 'Q1') {
    return rotation % 180 === 90 ? 'H' : 'V';
  }
  if (compId === 'D1') {
    return rotation % 180 === 90 ? 'V' : 'H';
  }
  if (compId === 'T1') {
    return 'H';
  }
  return 'H';
}

function routeOrthogonal(
  pinA: string,
  pinB: string,
  cA: { x: number; y: number },
  cB: { x: number; y: number },
  rotA: number,
  rotB: number,
  offset: number = 0
): [number, number][] {
  const dirA = getPinDirection(pinA, rotA);
  const dirB = getPinDirection(pinB, rotB);
  
  if (cA.x === cB.x || cA.y === cB.y) {
    if (offset !== 0) {
      if (cA.x === cB.x) {
        return [[cA.x, cA.y], [cA.x + offset, cA.y], [cA.x + offset, cB.y], [cB.x, cB.y]];
      } else {
        return [[cA.x, cA.y], [cA.x, cA.y + offset], [cB.x, cA.y + offset], [cB.x, cB.y]];
      }
    }
    return [[cA.x, cA.y], [cB.x, cB.y]];
  }
  
  if (dirA === 'V' && dirB === 'H') {
    const turnY = cB.y + offset;
    return [[cA.x, cA.y], [cA.x, turnY], [cB.x, turnY], [cB.x, cB.y]];
  } else if (dirA === 'H' && dirB === 'V') {
    const turnX = cB.x + offset;
    return [[cA.x, cA.y], [turnX, cA.y], [turnX, cB.y], [cB.x, cB.y]];
  } else {
    if (dirA === 'V') {
      const midY = (cA.y + cB.y) / 2 + offset;
      return [[cA.x, cA.y], [cA.x, midY], [cB.x, midY], [cB.x, cB.y]];
    } else {
      const midX = (cA.x + cB.x) / 2 + offset;
      return [[cA.x, cA.y], [midX, cA.y], [midX, cB.y], [cB.x, cB.y]];
    }
  }
}

export default function FlybackSchematicSandbox({
  vin, setVin,
  vor, setVor,
  vout, setVout,
  iout, setIout,
  fsw, setFsw,
  krf, setKrf,
  bmax, setBmax,
  ae, setAe,
  lpUh, setLpUh,
  cUf, setCUf,
  rcEsr, setRcEsr,
  rcdLlk, setRcdLlk,
  rcdVspike, setRcdVspike,
  calcData
}: FlybackSchematicSandboxProps) {
  const [componentsPos, setComponentsPos] = useState<{ [key: string]: { x: number; y: number; rotation: number } }>(() => {
    const saved = localStorage.getItem('toolbox_flyback_layout_pos');
    if (saved) {
      try { return JSON.parse(saved); } catch (e) { console.error("Error loading layout pos", e); }
    }
    return {
      Vin: { x: 80, y: 200, rotation: 90 },
      Cin: { x: 160, y: 200, rotation: 90 },
      R_clamp: { x: 240, y: 80, rotation: 90 },
      C_clamp: { x: 300, y: 80, rotation: 90 },
      D_clamp: { x: 260, y: 160, rotation: 270 },
      Q1: { x: 340, y: 200, rotation: 0 },
      T1: { x: 380, y: 100, rotation: 0 },
      D1: { x: 480, y: 75, rotation: 0 },
      Cout: { x: 580, y: 200, rotation: 90 },
      RL: { x: 680, y: 200, rotation: 90 },
      GND: { x: 340, y: 260, rotation: 0 },
      GND_sec: { x: 580, y: 260, rotation: 0 }
    };
  });

  const [wires, setWires] = useState<{ from: string; to: string }[]>(() => {
    const saved = localStorage.getItem('toolbox_flyback_layout_wires');
    if (saved) {
      try { return JSON.parse(saved); } catch (e) { console.error("Error loading layout wires", e); }
    }
    return [
      { from: 'Vin.P', to: 'Cin.P' },
      { from: 'Cin.P', to: 'R_clamp.Pin1' },
      { from: 'R_clamp.Pin1', to: 'C_clamp.P' },
      { from: 'C_clamp.P', to: 'T1.Pri1' },
      { from: 'T1.Pri2', to: 'Q1.D' },
      { from: 'Q1.D', to: 'D_clamp.A' },
      { from: 'D_clamp.K', to: 'R_clamp.Pin2' },
      { from: 'R_clamp.Pin2', to: 'C_clamp.N' },
      { from: 'Vin.N', to: 'Cin.N' },
      { from: 'Cin.N', to: 'Q1.S' },
      { from: 'Q1.S', to: 'GND.Pin' },
      { from: 'T1.Sec2', to: 'D1.A' },
      { from: 'D1.K', to: 'Cout.P' },
      { from: 'Cout.P', to: 'RL.Pin1' },
      { from: 'T1.Sec1', to: 'Cout.N' },
      { from: 'Cout.N', to: 'RL.Pin2' },
      { from: 'Cout.N', to: 'GND_sec.Pin' }
    ];
  });

  const [activeDragComponent, setActiveDragComponent] = useState<string | null>(null);
  const [dragStartPin, setDragStartPin] = useState<string | null>(null);
  const [tempWireEnd, setTempWireEnd] = useState<{ x: number; y: number } | null>(null);
  const [snapTargetPin, setSnapTargetPin] = useState<string | null>(null);
  const [drcViolation, setDrcViolation] = useState<{ message: string; x: number; y: number } | null>(null);
  const [activeModalComponent, setActiveModalComponent] = useState<string | null>(null);
  const [modalSize, setModalSize] = useState<{ width: number; height: number }>(() => {
    const saved = localStorage.getItem('toolbox_modal_size');
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        if (typeof parsed.width === 'number' && typeof parsed.height === 'number') {
          return parsed;
        }
      } catch (e) {}
    }
    return { width: 550, height: 650 };
  });

  useEffect(() => {
    localStorage.setItem('toolbox_modal_size', JSON.stringify(modalSize));
  }, [modalSize]);

  const [hoveredComponent, setHoveredComponent] = useState<string | null>(null);
  const [hoveredWire, setHoveredWire] = useState<number | null>(null);
  
  const [wireOffsets, setWireOffsets] = useState<{ [key: string]: number }>(() => {
    const saved = localStorage.getItem('toolbox_flyback_layout_offsets');
    if (saved) {
      try { return JSON.parse(saved); } catch (e) { console.error("Error loading layout offsets", e); }
    }
    return {};
  });
  
  const [activeDragWire, setActiveDragWire] = useState<{
    wireKey: string;
    isHorizontal: boolean;
    startMouseCoord: number;
    startOffset: number;
    hasDragged: boolean;
  } | null>(null);

  const dragStartOffset = useRef({ x: 0, y: 0 });
  const dragStartCoords = useRef({ x: 0, y: 0 });
  const hasDragged = useRef(false);
  const svgRef = useRef<SVGSVGElement | null>(null);

  const getPinCoordsMap = (posMap: typeof componentsPos) => {
    const coords = new Map<string, { x: number; y: number }>();
    for (const [compId, template] of Object.entries(componentTemplates)) {
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

    function find(x: string): string {
      let r = x;
      if (!parent.has(r)) parent.set(r, r);
      while (parent.get(r) !== r) {
        r = parent.get(r)!;
      }
      let curr = x;
      while (parent.has(curr) && curr !== r) {
        const nxt = parent.get(curr)!;
        parent.set(curr, r);
        curr = nxt;
      }
      return r;
    }

    function union(x: string, y: string) {
      const rx = find(x);
      const ry = find(y);
      if (rx !== ry) {
        parent.set(rx, ry);
      }
    }

    for (const w of wires) {
      union(w.from, w.to);
    }

    const flylines: Flyline[] = [];
    const netGroups = {
      Net_Vin: ["Vin.P", "Cin.P", "R_clamp.Pin1", "C_clamp.P", "T1.Pri1"],
      Net_SW_Pri: ["T1.Pri2", "Q1.D", "D_clamp.A"],
      Net_Clamp: ["D_clamp.K", "R_clamp.Pin2", "C_clamp.N"],
      Net_PGND: ["Vin.N", "Cin.N", "Q1.S", "GND.Pin"],
      Net_SW_Sec: ["T1.Sec2", "D1.A"],
      Net_Vout: ["D1.K", "Cout.P", "RL.Pin1"],
      Net_SGND: ["T1.Sec1", "Cout.N", "RL.Pin2", "GND_sec.Pin"]
    };

    for (const [_, netPins] of Object.entries(netGroups)) {
      let uniqueRoots = Array.from(new Set(netPins.map(p => find(p))));
      
      while (uniqueRoots.length > 1) {
        let minDist = Infinity;
        let bestPair: [string, string] | null = null;

        for (let i = 0; i < netPins.length; i++) {
          for (let j = i + 1; j < netPins.length; j++) {
            const pA = netPins[i];
            const pB = netPins[j];
            const rA = find(pA);
            const rB = find(pB);
            if (rA !== rB) {
              const cA = allPinCoords.get(pA);
              const cB = allPinCoords.get(pB);
              if (cA && cB) {
                const dist = Math.hypot(cA.x - cB.x, cA.y - cB.y);
                if (dist < minDist) {
                  minDist = dist;
                  bestPair = [pA, pB];
                }
              }
            }
          }
        }

        if (bestPair) {
          const [pA, pB] = bestPair;
          const cA = allPinCoords.get(pA)!;
          const cB = allPinCoords.get(pB)!;
          flylines.push({
            from: pA,
            to: pB,
            fromCoords: cA,
            toCoords: cB
          });
          union(pA, pB);
          uniqueRoots = Array.from(new Set(netPins.map(p => find(p))));
        } else {
          break;
        }
      }
    }

    return flylines;
  };

  const ratsnestLines = getRatsnestLines();

  useEffect(() => {
    if (Object.keys(componentsPos).length > 0) {
      localStorage.setItem('toolbox_flyback_layout_pos', JSON.stringify(componentsPos));
    }
  }, [componentsPos]);

  useEffect(() => {
    localStorage.setItem('toolbox_flyback_layout_wires', JSON.stringify(wires));
  }, [wires]);

  useEffect(() => {
    localStorage.setItem('toolbox_flyback_layout_offsets', JSON.stringify(wireOffsets));
  }, [wireOffsets]);

  const [saveTip, setSaveTip] = useState<string | null>(null);

  const handleSaveLayout = () => {
    localStorage.setItem('toolbox_flyback_layout_pos', JSON.stringify(componentsPos));
    localStorage.setItem('toolbox_flyback_layout_wires', JSON.stringify(wires));
    localStorage.setItem('toolbox_flyback_layout_offsets', JSON.stringify(wireOffsets));
    setSaveTip("Saved layout & wiring!");
    setTimeout(() => setSaveTip(null), 2500);
  };

  const getSvgCoords = (e: React.MouseEvent) => {
    if (!svgRef.current) return { x: 0, y: 0 };
    const rect = svgRef.current.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * 850;
    const y = ((e.clientY - rect.top) / rect.height) * 300;
    return { x, y };
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    const coords = getSvgCoords(e);

    if (activeDragWire) {
      const { wireKey, isHorizontal, startMouseCoord, startOffset } = activeDragWire;
      const currentCoord = isHorizontal ? coords.y : coords.x;
      const delta = currentCoord - startMouseCoord;
      
      if (Math.abs(delta) > 5) {
        setActiveDragWire(prev => prev ? { ...prev, hasDragged: true } : null);
      }

      const gridDelta = Math.round(delta / 20) * 20;
      setWireOffsets(prev => ({
        ...prev,
        [wireKey]: startOffset + gridDelta
      }));
      return;
    }

    if (activeDragComponent) {
      let newX = coords.x - dragStartOffset.current.x;
      let newY = coords.y - dragStartOffset.current.y;
      
      newX = Math.round(newX / 20) * 20;
      newY = Math.round(newY / 20) * 20;

      newX = Math.max(40, Math.min(810, newX));
      newY = Math.max(40, Math.min(260, newY));

      const deltaX = Math.abs(coords.x - dragStartCoords.current.x);
      const deltaY = Math.abs(coords.y - dragStartCoords.current.y);
      if (deltaX > 5 || deltaY > 5) {
        hasDragged.current = true;
      }

      setComponentsPos(prev => ({
        ...prev,
        [activeDragComponent]: {
          ...prev[activeDragComponent],
          x: newX,
          y: newY
        }
      }));
      return;
    }

    if (dragStartPin) {
      setTempWireEnd(coords);
      let foundSnap: string | null = null;
      for (const pinId of allPins) {
        if (pinId === dragStartPin) continue;
        const pinC = allPinCoords.get(pinId);
        if (pinC) {
          const dist = Math.hypot(coords.x - pinC.x, coords.y - pinC.y);
          if (dist <= 20) {
            foundSnap = pinId;
            break;
          }
        }
      }
      setSnapTargetPin(foundSnap);
    }
  };

  const handleMouseDownComponent = (e: React.MouseEvent, compId: string) => {
    e.stopPropagation();
    const coords = getSvgCoords(e);
    const pos = componentsPos[compId];
    if (!pos) return;
    
    dragStartOffset.current = {
      x: coords.x - pos.x,
      y: coords.y - pos.y
    };
    dragStartCoords.current = { x: coords.x, y: coords.y };
    hasDragged.current = false;
    setActiveDragComponent(compId);
  };

  const handleMouseUpComponent = (e: React.MouseEvent, compId: string) => {
    e.stopPropagation();
    setActiveDragComponent(null);
    if (!hasDragged.current) {
      setActiveModalComponent(compId);
    }
  };

  const handleMouseDownPin = (e: React.MouseEvent, pinId: string) => {
    e.stopPropagation();
    const coords = getSvgCoords(e);
    setDragStartPin(pinId);
    setTempWireEnd(coords);
  };

  const handleMouseUp = (e: React.MouseEvent) => {
    if (activeDragWire) {
      setActiveDragWire(null);
      return;
    }
    
    setActiveDragComponent(null);

    if (dragStartPin) {
      if (snapTargetPin) {
        const netA = pinToNetGroup[dragStartPin];
        const netB = pinToNetGroup[snapTargetPin];
        
        if (netA && netB && netA === netB) {
          const exists = wires.some(
            w => (w.from === dragStartPin && w.to === snapTargetPin) || 
                 (w.from === snapTargetPin && w.to === dragStartPin)
          );
          if (!exists) {
            setWires(prev => [...prev, { from: dragStartPin, to: snapTargetPin }]);
          }
        } else {
          const coords = getSvgCoords(e);
          let errMsg = `DRC Check: [${dragStartPin}] and [${snapTargetPin}] belong to different electrical nets!`;
          if ((netA === 'Net_Vin' && netB === 'Net_PGND') || (netA === 'Net_PGND' && netB === 'Net_Vin')) {
            errMsg = "Fatal DRC Error: Shorting Vin directly to PGND causes a dead short across the DC input power source!";
          } else if ((netA === 'Net_Vout' && netB === 'Net_SGND') || (netA === 'Net_SGND' && netB === 'Net_Vout')) {
            errMsg = "Fatal DRC Error: Shorting Vout directly to SGND shorts output capacitors and load!";
          } else if ((netA === 'Net_SW_Pri' && netB === 'Net_PGND') || (netA === 'Net_PGND' && netB === 'Net_SW_Pri')) {
            errMsg = "Fatal DRC Error: Shorting SW to PGND shorts the MOSFET switch!";
          } else if (netA && netB && ((netA.includes('PGND') && netB.includes('SGND')) || (netA.includes('SGND') && netB.includes('PGND')))) {
            errMsg = "Safety Isolation DRC: Primary and secondary grounds must maintain galvanic isolation!";
          }
          
          setDrcViolation({
            message: errMsg,
            x: coords.x,
            y: coords.y
          });
        }
      }
      setDragStartPin(null);
      setTempWireEnd(null);
      setSnapTargetPin(null);
    }
  };

  const handleDisconnectWire = (index: number) => {
    setWires(prev => prev.filter((_, i) => i !== index));
  };

  const handleResetLayout = () => {
    const defaultPos = {
      Vin: { x: 80, y: 200, rotation: 90 },
      Cin: { x: 160, y: 200, rotation: 90 },
      R_clamp: { x: 240, y: 80, rotation: 90 },
      C_clamp: { x: 300, y: 80, rotation: 90 },
      D_clamp: { x: 260, y: 160, rotation: 270 },
      Q1: { x: 340, y: 200, rotation: 0 },
      T1: { x: 380, y: 100, rotation: 0 },
      D1: { x: 480, y: 75, rotation: 0 },
      Cout: { x: 580, y: 200, rotation: 90 },
      RL: { x: 680, y: 200, rotation: 90 },
      GND: { x: 340, y: 260, rotation: 0 },
      GND_sec: { x: 580, y: 260, rotation: 0 }
    };
    const defaultWires = [
      { from: 'Vin.P', to: 'Cin.P' },
      { from: 'Cin.P', to: 'R_clamp.Pin1' },
      { from: 'R_clamp.Pin1', to: 'C_clamp.P' },
      { from: 'C_clamp.P', to: 'T1.Pri1' },
      { from: 'T1.Pri2', to: 'Q1.D' },
      { from: 'Q1.D', to: 'D_clamp.A' },
      { from: 'D_clamp.K', to: 'R_clamp.Pin2' },
      { from: 'R_clamp.Pin2', to: 'C_clamp.N' },
      { from: 'Vin.N', to: 'Cin.N' },
      { from: 'Cin.N', to: 'Q1.S' },
      { from: 'Q1.S', to: 'GND.Pin' },
      { from: 'T1.Sec2', to: 'D1.A' },
      { from: 'D1.K', to: 'Cout.P' },
      { from: 'Cout.P', to: 'RL.Pin1' },
      { from: 'T1.Sec1', to: 'Cout.N' },
      { from: 'Cout.N', to: 'RL.Pin2' },
      { from: 'Cout.N', to: 'GND_sec.Pin' }
    ];
    setComponentsPos(defaultPos);
    setWires(defaultWires);
    setWireOffsets({});
    localStorage.removeItem('toolbox_flyback_layout_pos');
    localStorage.removeItem('toolbox_flyback_layout_wires');
    localStorage.removeItem('toolbox_flyback_layout_offsets');
  };

  const handleRotateComponent = (compId: string) => {
    setComponentsPos(prev => {
      const pos = prev[compId];
      if (!pos) return prev;
      return {
        ...prev,
        [compId]: {
          ...pos,
          rotation: (pos.rotation + 90) % 360
        }
      };
    });
  };

  const [resizing, setResizing] = useState(false);
  const resizeStartMouse = useRef({ x: 0, y: 0 });
  const resizeStartSize = useRef({ width: 0, height: 0 });

  const handleResizeStart = (e: React.MouseEvent) => {
    e.stopPropagation();
    e.preventDefault();
    setResizing(true);
    resizeStartMouse.current = { x: e.clientX, y: e.clientY };
    resizeStartSize.current = { width: modalSize.width, height: modalSize.height };
  };

  useEffect(() => {
    const handleResizeMove = (e: MouseEvent) => {
      if (!resizing) return;
      const deltaX = e.clientX - resizeStartMouse.current.x;
      const deltaY = e.clientY - resizeStartMouse.current.y;
      
      const newWidth = Math.max(380, Math.min(800, resizeStartSize.current.width + deltaX));
      const newHeight = Math.max(300, Math.min(750, resizeStartSize.current.height + deltaY));
      
      setModalSize({ width: newWidth, height: newHeight });
    };

    const handleResizeMouseUp = () => {
      if (resizing) {
        setResizing(false);
      }
    };

    if (resizing) {
      document.addEventListener('mousemove', handleResizeMove);
      document.addEventListener('mouseup', handleResizeMouseUp);
    }
    return () => {
      document.removeEventListener('mousemove', handleResizeMove);
      document.removeEventListener('mouseup', handleResizeMouseUp);
    };
  }, [resizing]);

  useEffect(() => {
    if (drcViolation) {
      const timer = setTimeout(() => setDrcViolation(null), 4000);
      return () => clearTimeout(timer);
    }
  }, [drcViolation]);

  return (
    <div className="relative w-full flex flex-col gap-2">
      <div className="flex justify-between items-center bg-[#090d16]/80 p-2.5 rounded-lg border border-slate-800/80 mb-2">
        <div className="flex items-center gap-2">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">EDA Interactive Schematic Canvas (20px Grid)</span>
          {saveTip && (
            <span className="text-[10px] text-emerald-400 font-bold animate-pulse font-mono">{saveTip}</span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <Button 
            variant="outline" 
            size="sm" 
            onClick={handleSaveLayout}
            className="h-7 text-[10px] border-slate-800 bg-slate-900 text-slate-200 hover:text-white"
          >
            Save Layout & Wires
          </Button>
          <Button 
            variant="outline" 
            size="sm" 
            onClick={handleResetLayout}
            className="h-7 text-[10px] border-slate-800 bg-slate-900 text-rose-400 hover:text-red-300"
          >
            Reset Default Layout
          </Button>
        </div>
      </div>

      <div className="relative border border-slate-850 bg-slate-950/40 rounded-xl overflow-hidden shadow-inner">
        <svg
          ref={svgRef}
          viewBox="0 0 850 300"
          className="w-full h-auto"
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
          style={{ cursor: activeDragComponent ? 'grabbing' : 'default' }}
        >
          <defs>
            <pattern id="grid-dots" width="20" height="20" patternUnits="userSpaceOnUse">
              <circle cx="2" cy="2" r="1" fill="rgba(255, 255, 255, 0.05)" />
            </pattern>
            <filter id="wire-glow" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="2.5" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
            <filter id="select-glow" x="-30%" y="-30%" width="160%" height="160%">
              <feDropShadow dx="0" dy="0" stdDeviation="4" floodColor="#00f2fe" floodOpacity="0.6" />
            </filter>
          </defs>

          <rect width="850" height="300" fill="url(#grid-dots)" />

          {ratsnestLines.map((fly, idx) => (
            <line
              key={`ratsnest-${idx}`}
              x1={fly.fromCoords.x}
              y1={fly.fromCoords.y}
              x2={fly.toCoords.x}
              y2={fly.toCoords.y}
              stroke="#00f2fe"
              strokeWidth="1.0"
              strokeDasharray="3 3"
              strokeOpacity="0.4"
            />
          ))}

          {dragStartPin && tempWireEnd && (
            <line
              x1={allPinCoords.get(dragStartPin)!.x}
              y1={allPinCoords.get(dragStartPin)!.y}
              x2={tempWireEnd.x}
              y2={tempWireEnd.y}
              stroke="#00f2fe"
              strokeWidth="2"
              strokeDasharray="4 4"
            />
          )}

          {wires.map((w, index) => {
            const cA = allPinCoords.get(w.from);
            const cB = allPinCoords.get(w.to);
            if (!cA || !cB) return null;
            
            const compA = w.from.split('.')[0];
            const compB = w.to.split('.')[0];
            const rotA = componentsPos[compA]?.rotation ?? 0;
            const rotB = componentsPos[compB]?.rotation ?? 0;

            const wireKey = `${w.from}-${w.to}`;
            const offset = wireOffsets[wireKey] ?? 0;

            const pts = routeOrthogonal(w.from, w.to, cA, cB, rotA, rotB, offset);
            const pathD = `M ${pts.map(p => `${p[0]} ${p[1]}`).join(' L ')}`;
            
            const isHovered = hoveredWire === index;

            return (
              <g key={`wire-${index}`} onMouseEnter={() => setHoveredWire(index)} onMouseLeave={() => setHoveredWire(null)}>
                <path
                  d={pathD}
                  fill="none"
                  stroke="transparent"
                  strokeWidth="8"
                  className="cursor-pointer"
                  onClick={() => handleDisconnectWire(index)}
                >
                  <title>Click to disconnect wire</title>
                </path>
                
                <path
                  d={pathD}
                  fill="none"
                  stroke={isHovered ? '#ff0055' : '#00f2fe'}
                  strokeWidth={isHovered ? '2.5' : '1.8'}
                  strokeOpacity={isHovered ? '1.0' : '0.8'}
                  filter={isHovered ? 'url(#wire-glow)' : ''}
                  className="transition-all duration-150"
                />
              </g>
            );
          })}

          <g
            className="schematic-interactive-group"
            onMouseEnter={() => setHoveredComponent('GND')}
            onMouseLeave={() => setHoveredComponent(null)}
            onMouseDown={(e) => handleMouseDownComponent(e, 'GND')}
            onMouseUp={(e) => handleMouseUpComponent(e, 'GND')}
          >
            <SchematicGround
              x={componentsPos.GND.x}
              y={componentsPos.GND.y}
              label="PGND"
              highlighted={hoveredComponent === 'GND'}
            />
          </g>
          <circle cx={allPinCoords.get("GND.Pin")!.x} cy={allPinCoords.get("GND.Pin")!.y} r="4" fill="#00f2fe" className="cursor-crosshair" onMouseDown={(e) => handleMouseDownPin(e, "GND.Pin")} />

          <g
            className="schematic-interactive-group"
            onMouseEnter={() => setHoveredComponent('GND_sec')}
            onMouseLeave={() => setHoveredComponent(null)}
            onMouseDown={(e) => handleMouseDownComponent(e, 'GND_sec')}
            onMouseUp={(e) => handleMouseUpComponent(e, 'GND_sec')}
          >
            <SchematicGround
              x={componentsPos.GND_sec.x}
              y={componentsPos.GND_sec.y}
              label="SGND"
              highlighted={hoveredComponent === 'GND_sec'}
            />
          </g>
          <circle cx={allPinCoords.get("GND_sec.Pin")!.x} cy={allPinCoords.get("GND_sec.Pin")!.y} r="4" fill="#00f2fe" className="cursor-crosshair" onMouseDown={(e) => handleMouseDownPin(e, "GND_sec.Pin")} />

          <g
            className="schematic-interactive-group"
            onMouseEnter={() => setHoveredComponent('Vin')}
            onMouseLeave={() => setHoveredComponent(null)}
            onMouseDown={(e) => handleMouseDownComponent(e, 'Vin')}
            onMouseUp={(e) => handleMouseUpComponent(e, 'Vin')}
          >
            <SchematicDCSource
              x={componentsPos.Vin.x}
              y={componentsPos.Vin.y}
              rotation={componentsPos.Vin.rotation}
              pinLength={40}
              label="Vin"
              subLabel={`${vin.toFixed(1)} V`}
              highlighted={hoveredComponent === 'Vin'}
            />
            <circle cx={allPinCoords.get("Vin.P")!.x} cy={allPinCoords.get("Vin.P")!.y} r="4" fill="#00f2fe" className="cursor-crosshair" onMouseDown={(e) => handleMouseDownPin(e, "Vin.P")} />
            <circle cx={allPinCoords.get("Vin.N")!.x} cy={allPinCoords.get("Vin.N")!.y} r="4" fill="#00f2fe" className="cursor-crosshair" onMouseDown={(e) => handleMouseDownPin(e, "Vin.N")} />
          </g>

          <g
            className="schematic-interactive-group"
            onMouseEnter={() => setHoveredComponent('Cin')}
            onMouseLeave={() => setHoveredComponent(null)}
            onMouseDown={(e) => handleMouseDownComponent(e, 'Cin')}
            onMouseUp={(e) => handleMouseUpComponent(e, 'Cin')}
          >
            <SchematicCapacitorPolar
              x={componentsPos.Cin.x}
              y={componentsPos.Cin.y}
              rotation={componentsPos.Cin.rotation}
              label="Cin"
              subLabel="47 μF"
              highlighted={hoveredComponent === 'Cin'}
            />
            <circle cx={allPinCoords.get("Cin.P")!.x} cy={allPinCoords.get("Cin.P")!.y} r="4" fill="#00f2fe" className="cursor-crosshair" onMouseDown={(e) => handleMouseDownPin(e, "Cin.P")} />
            <circle cx={allPinCoords.get("Cin.N")!.x} cy={allPinCoords.get("Cin.N")!.y} r="4" fill="#00f2fe" className="cursor-crosshair" onMouseDown={(e) => handleMouseDownPin(e, "Cin.N")} />
          </g>

          <g
            className="schematic-interactive-group"
            onMouseEnter={() => setHoveredComponent('R_clamp')}
            onMouseLeave={() => setHoveredComponent(null)}
            onMouseDown={(e) => handleMouseDownComponent(e, 'R_clamp')}
            onMouseUp={(e) => handleMouseUpComponent(e, 'R_clamp')}
          >
            <SchematicResistor
              x={componentsPos.R_clamp.x}
              y={componentsPos.R_clamp.y}
              rotation={componentsPos.R_clamp.rotation}
              label="R_clamp"
              subLabel={`${calcData?.design ? (calcData?.design?.r_clamp_recommend_kohm)?.toFixed(1) ?? '-' : '-'} kΩ`}
              highlighted={hoveredComponent === 'R_clamp'}
            />
            <circle cx={allPinCoords.get("R_clamp.Pin1")!.x} cy={allPinCoords.get("R_clamp.Pin1")!.y} r="4" fill="#00f2fe" className="cursor-crosshair" onMouseDown={(e) => handleMouseDownPin(e, "R_clamp.Pin1")} />
            <circle cx={allPinCoords.get("R_clamp.Pin2")!.x} cy={allPinCoords.get("R_clamp.Pin2")!.y} r="4" fill="#00f2fe" className="cursor-crosshair" onMouseDown={(e) => handleMouseDownPin(e, "R_clamp.Pin2")} />
          </g>

          <g
            className="schematic-interactive-group"
            onMouseEnter={() => setHoveredComponent('C_clamp')}
            onMouseLeave={() => setHoveredComponent(null)}
            onMouseDown={(e) => handleMouseDownComponent(e, 'C_clamp')}
            onMouseUp={(e) => handleMouseUpComponent(e, 'C_clamp')}
          >
            <SchematicCapacitorPolar
              x={componentsPos.C_clamp.x}
              y={componentsPos.C_clamp.y}
              rotation={componentsPos.C_clamp.rotation}
              label="C_clamp"
              subLabel={`${calcData?.design ? (calcData?.design?.c_clamp_recommend_nf)?.toFixed(1) ?? '-' : '-'} nF`}
              highlighted={hoveredComponent === 'C_clamp'}
            />
            <circle cx={allPinCoords.get("C_clamp.P")!.x} cy={allPinCoords.get("C_clamp.P")!.y} r="4" fill="#00f2fe" className="cursor-crosshair" onMouseDown={(e) => handleMouseDownPin(e, "C_clamp.P")} />
            <circle cx={allPinCoords.get("C_clamp.N")!.x} cy={allPinCoords.get("C_clamp.N")!.y} r="4" fill="#00f2fe" className="cursor-crosshair" onMouseDown={(e) => handleMouseDownPin(e, "C_clamp.N")} />
          </g>

          <g
            className="schematic-interactive-group"
            onMouseEnter={() => setHoveredComponent('D_clamp')}
            onMouseLeave={() => setHoveredComponent(null)}
            onMouseDown={(e) => handleMouseDownComponent(e, 'D_clamp')}
            onMouseUp={(e) => handleMouseUpComponent(e, 'D_clamp')}
          >
            <SchematicDiode
              x={componentsPos.D_clamp.x}
              y={componentsPos.D_clamp.y}
              rotation={componentsPos.D_clamp.rotation}
              label="D_clamp"
              subLabel="Fast Recovery"
              highlighted={hoveredComponent === 'D_clamp'}
            />
            <circle cx={allPinCoords.get("D_clamp.A")!.x} cy={allPinCoords.get("D_clamp.A")!.y} r="4" fill="#00f2fe" className="cursor-crosshair" onMouseDown={(e) => handleMouseDownPin(e, "D_clamp.A")} />
            <circle cx={allPinCoords.get("D_clamp.K")!.x} cy={allPinCoords.get("D_clamp.K")!.y} r="4" fill="#00f2fe" className="cursor-crosshair" onMouseDown={(e) => handleMouseDownPin(e, "D_clamp.K")} />
          </g>

          <g
            className="schematic-interactive-group"
            onMouseEnter={() => setHoveredComponent('Q1')}
            onMouseLeave={() => setHoveredComponent(null)}
            onMouseDown={(e) => handleMouseDownComponent(e, 'Q1')}
            onMouseUp={(e) => handleMouseUpComponent(e, 'Q1')}
          >
            <SchematicMosfetN
              x={componentsPos.Q1.x}
              y={componentsPos.Q1.y}
              rotation={componentsPos.Q1.rotation}
              label="Q1"
              subLabel="MOSFET"
              highlighted={hoveredComponent === 'Q1'}
            />
            <circle cx={allPinCoords.get("Q1.D")!.x} cy={allPinCoords.get("Q1.D")!.y} r="4" fill="#00f2fe" className="cursor-crosshair" onMouseDown={(e) => handleMouseDownPin(e, "Q1.D")} />
            <circle cx={allPinCoords.get("Q1.S")!.x} cy={allPinCoords.get("Q1.S")!.y} r="4" fill="#00f2fe" className="cursor-crosshair" onMouseDown={(e) => handleMouseDownPin(e, "Q1.S")} />
          </g>

          <g
            className="schematic-interactive-group"
            onMouseEnter={() => setHoveredComponent('T1')}
            onMouseLeave={() => setHoveredComponent(null)}
            onMouseDown={(e) => handleMouseDownComponent(e, 'T1')}
            onMouseUp={(e) => handleMouseUpComponent(e, 'T1')}
          >
            <SchematicTransformer
              x={componentsPos.T1.x}
              y={componentsPos.T1.y}
              rotation={componentsPos.T1.rotation}
              dotPosition="top-bottom"
              label="T1"
              subLabel={`${calcData?.design ? (calcData?.design?.lp_design_uh)?.toFixed(0) ?? '-' : '-'}uH`}
              highlighted={hoveredComponent === 'T1'}
            />
            <circle cx={allPinCoords.get("T1.Pri1")!.x} cy={allPinCoords.get("T1.Pri1")!.y} r="4" fill="#00f2fe" className="cursor-crosshair" onMouseDown={(e) => handleMouseDownPin(e, "T1.Pri1")} />
            <circle cx={allPinCoords.get("T1.Pri2")!.x} cy={allPinCoords.get("T1.Pri2")!.y} r="4" fill="#00f2fe" className="cursor-crosshair" onMouseDown={(e) => handleMouseDownPin(e, "T1.Pri2")} />
            <circle cx={allPinCoords.get("T1.Sec2")!.x} cy={allPinCoords.get("T1.Sec2")!.y} r="4" fill="#00f2fe" className="cursor-crosshair" onMouseDown={(e) => handleMouseDownPin(e, "T1.Sec2")} />
            <circle cx={allPinCoords.get("T1.Sec1")!.x} cy={allPinCoords.get("T1.Sec1")!.y} r="4" fill="#00f2fe" className="cursor-crosshair" onMouseDown={(e) => handleMouseDownPin(e, "T1.Sec1")} />
          </g>

          <g
            className="schematic-interactive-group"
            onMouseEnter={() => setHoveredComponent('D1')}
            onMouseLeave={() => setHoveredComponent(null)}
            onMouseDown={(e) => handleMouseDownComponent(e, 'D1')}
            onMouseUp={(e) => handleMouseUpComponent(e, 'D1')}
          >
            <SchematicDiode
              x={componentsPos.D1.x}
              y={componentsPos.D1.y}
              rotation={componentsPos.D1.rotation}
              label="D1"
              subLabel="Rectifier"
              highlighted={hoveredComponent === 'D1'}
            />
            <circle cx={allPinCoords.get("D1.A")!.x} cy={allPinCoords.get("D1.A")!.y} r="4" fill="#00f2fe" className="cursor-crosshair" onMouseDown={(e) => handleMouseDownPin(e, "D1.A")} />
            <circle cx={allPinCoords.get("D1.K")!.x} cy={allPinCoords.get("D1.K")!.y} r="4" fill="#00f2fe" className="cursor-crosshair" onMouseDown={(e) => handleMouseDownPin(e, "D1.K")} />
          </g>

          <g
            className="schematic-interactive-group"
            onMouseEnter={() => setHoveredComponent('Cout')}
            onMouseLeave={() => setHoveredComponent(null)}
            onMouseDown={(e) => handleMouseDownComponent(e, 'Cout')}
            onMouseUp={(e) => handleMouseUpComponent(e, 'Cout')}
          >
            <SchematicCapacitorPolar
              x={componentsPos.Cout.x}
              y={componentsPos.Cout.y}
              rotation={componentsPos.Cout.rotation}
              label="Co"
              subLabel={`${cUf || '-'} μF`}
              highlighted={hoveredComponent === 'Cout'}
            />
            <circle cx={allPinCoords.get("Cout.P")!.x} cy={allPinCoords.get("Cout.P")!.y} r="4" fill="#00f2fe" className="cursor-crosshair" onMouseDown={(e) => handleMouseDownPin(e, "Cout.P")} />
            <circle cx={allPinCoords.get("Cout.N")!.x} cy={allPinCoords.get("Cout.N")!.y} r="4" fill="#00f2fe" className="cursor-crosshair" onMouseDown={(e) => handleMouseDownPin(e, "Cout.N")} />
          </g>

          <g
            className="schematic-interactive-group"
            onMouseEnter={() => setHoveredComponent('RL')}
            onMouseLeave={() => setHoveredComponent(null)}
            onMouseDown={(e) => handleMouseDownComponent(e, 'RL')}
            onMouseUp={(e) => handleMouseUpComponent(e, 'RL')}
          >
            <SchematicResistor
              x={componentsPos.RL.x}
              y={componentsPos.RL.y}
              rotation={componentsPos.RL.rotation}
              label="RL"
              subLabel={`${iout > 0 ? (vout/iout).toFixed(1) : '-'} Ω`}
              highlighted={hoveredComponent === 'RL'}
            />
            <circle cx={allPinCoords.get("RL.Pin1")!.x} cy={allPinCoords.get("RL.Pin1")!.y} r="4" fill="#00f2fe" className="cursor-crosshair" onMouseDown={(e) => handleMouseDownPin(e, "RL.Pin1")} />
            <circle cx={allPinCoords.get("RL.Pin2")!.x} cy={allPinCoords.get("RL.Pin2")!.y} r="4" fill="#00f2fe" className="cursor-crosshair" onMouseDown={(e) => handleMouseDownPin(e, "RL.Pin2")} />
          </g>
        </svg>

        {drcViolation && (
          <div
            className="absolute p-3 rounded-lg bg-red-950/95 border border-red-500 text-red-200 text-xs font-semibold max-w-xs shadow-xl backdrop-blur-sm pointer-events-none transition-all duration-300 animate-in fade-in zoom-in-95"
            style={{
              left: `${Math.max(10, Math.min(850 - 260, (drcViolation.x / 850) * 100))}%`,
              top: `${Math.max(10, Math.min(300 - 80, (drcViolation.y / 300) * 100))}%`
            }}
          >
            {drcViolation.message}
          </div>
        )}
      </div>

      {activeModalComponent && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center z-50 animate-in fade-in duration-200">
          <div 
            className="bg-[#0f172a] border border-slate-800 rounded-xl shadow-2xl p-5 flex flex-col relative select-text"
            style={{ width: `${modalSize.width}px`, height: `${modalSize.height}px` }}
          >
            <div className="flex justify-between items-center pb-3 border-b border-slate-800 shrink-0">
              <div>
                <h3 className="text-sm font-bold text-white">
                  Device Parameters & Physics Models — [{activeModalComponent}]
                </h3>
                <p className="text-[10px] text-slate-400 mt-0.5">
                  Bidirectional data-binding. Modify parameters and inspect mathematical derivations.
                </p>
              </div>
              <button 
                onClick={() => handleRotateComponent(activeModalComponent)}
                className="text-[10px] px-2 py-1 bg-slate-900 border border-slate-800 hover:bg-slate-800 rounded-md font-semibold text-cyan-400 transition-colors"
                title="Rotate Symbol (90°)"
              >
                Rotate Symbol
              </button>
            </div>

            <div className="flex-1 overflow-y-auto py-4 space-y-4 pr-1 scrollbar-thin scrollbar-thumb-slate-800 select-text">
              <ComponentDesignDetails
                compId={activeModalComponent}
                vin={vin} setVin={setVin}
                vor={vor} setVor={setVor}
                vout={vout} setVout={setVout}
                iout={iout} setIout={setIout}
                fsw={fsw} setFsw={setFsw}
                krf={krf} setKrf={setKrf}
                bmax={bmax} setBmax={setBmax}
                ae={ae} setAe={setAe}
                lpUh={lpUh} setLpUh={setLpUh}
                cUf={cUf} setCUf={setCUf}
                rcEsr={rcEsr} setRcEsr={setRcEsr}
                rcdLlk={rcdLlk} setRcdLlk={setRcdLlk}
                rcdVspike={rcdVspike} setRcdVspike={setRcdVspike}
                calcData={calcData}
                defaultExpandFormula={true}
              />
            </div>
            
            <div className="flex justify-end pt-3 border-t border-slate-800 shrink-0">
              <Button
                onClick={() => setActiveModalComponent(null)}
                className="bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold px-4 py-2"
              >
                Confirm & Close
              </Button>
            </div>

            <div 
              className="absolute right-1 bottom-1 w-5 h-5 cursor-se-resize flex items-end justify-end p-0.5 select-none opacity-40 hover:opacity-100 transition-opacity"
              onMouseDown={handleResizeStart}
              title="Drag to resize modal"
            >
              <svg className="w-3.5 h-3.5 text-slate-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <line x1="6" y1="20" x2="20" y2="6" strokeLinecap="round" />
                <line x1="12" y1="20" x2="20" y2="12" strokeLinecap="round" />
                <line x1="18" y1="20" x2="20" y2="18" strokeLinecap="round" />
              </svg>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export interface ComponentDesignDetailsProps {
  compId: string;
  vin: number;
  setVin: (v: number) => void;
  vor: number;
  setVor: (v: number) => void;
  vout: number;
  setVout: (v: number) => void;
  iout: number;
  setIout: (v: number) => void;
  fsw: number;
  setFsw: (v: number) => void;
  krf: number;
  setKrf: (v: number) => void;
  bmax: number;
  setBmax: (v: number) => void;
  ae: number;
  setAe: (v: number) => void;
  lpUh: string;
  setLpUh: (v: string) => void;
  cUf: string;
  setCUf: (v: string) => void;
  rcEsr: number;
  setRcEsr: (v: number) => void;
  rcdLlk: number;
  setRcdLlk: (v: number) => void;
  rcdVspike: number;
  setRcdVspike: (v: number) => void;
  calcData: any;
  defaultExpandFormula?: boolean;
}

export function ComponentDesignDetails({
  compId,
  vin, setVin,
  vor, setVor,
  vout, setVout,
  iout, setIout,
  ae, setAe,
  cUf, setCUf,
  rcEsr, setRcEsr,
  rcdLlk, setRcdLlk,
  rcdVspike, setRcdVspike,
  bmax, setBmax,
  calcData,
  defaultExpandFormula = false
}: ComponentDesignDetailsProps) {
  const [expandFormula, setExpandFormula] = useState(defaultExpandFormula);
  const [expandDerivation, setExpandDerivation] = useState(false);

  const renderFormulaToggle = () => (
    <Button
      variant="link"
      onClick={() => setExpandFormula(!expandFormula)}
      className="h-auto p-0 text-[10px] text-cyan-400 hover:text-cyan-300 font-bold border-0"
    >
      {expandFormula ? 'Hide Equations' : 'Show Equations'}
    </Button>
  );

  const renderDerivationToggle = (label: string) => (
    <Button
      variant="link"
      onClick={() => setExpandDerivation(!expandDerivation)}
      className="h-auto p-0 text-[9px] text-cyan-500 hover:text-cyan-400 font-bold border-0 block text-left"
    >
      {expandDerivation ? 'Collapse Detailed Derivations' : `${label} (Volt-Second Balance & Integral Derivation)`}
    </Button>
  );

  const diodeVfNom = 0.7;
  const nps = vor / (vout + diodeVfNom);
  const dutyMaxEst = vor / (vin + vor);

  const pOut = vout * iout;
  const eff = calcData?.losses?.efficiency ?? 0.85;
  const pIn = pOut / eff;
  const iInAvg = pIn / vin;

  const sim = calcData?.simulation_time;
  const ipk = sim?.ipk ?? (iInAvg * 2.5);
  const ipRms = sim?.ip_rms ?? (iInAvg * 1.3);
  const isRms = sim?.is_rms ?? (iout * 1.3);
  const vdsMax = sim?.v_ds_max ?? (vin + vor + rcdVspike);
  const vrevMax = sim?.v_rev_max ?? (vout + vin / (nps || 1.0));

  switch (compId) {
    case 'Vin':
      return (
        <div className="space-y-4 text-xs">
          <div className="flex justify-between items-center mb-1 bg-slate-900/30 p-1.5 rounded border border-slate-800/40">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Physical Formulation</span>
            {renderFormulaToggle()}
          </div>
          {expandFormula && (
            <div className="p-3 bg-slate-950/40 rounded-lg border border-slate-800 space-y-2 animate-in fade-in slide-in-from-top-1 duration-150">
              <span className="text-[11px] font-semibold text-cyan-400 block">Mathematical Model</span>
              <div className="text-[11px] text-slate-400 leading-relaxed">
                Average input current is governed by rated output power and conversion efficiency:
              </div>
              <Latex math="P_{in} = \frac{V_{out} \cdot I_{out}}{\eta}" block />
              <Latex math="I_{in,avg} = \frac{P_{in}}{V_{in}}" block />
              
              {renderDerivationToggle("DC Input & Conservation of Energy")}
              {expandDerivation && (
                <div className="mt-2 p-2.5 bg-slate-950/60 rounded border border-slate-900/60 text-slate-400 text-[10px] leading-relaxed space-y-2">
                  <div>Under steady-state conditions, input energy equals output energy plus internal thermal dissipation:</div>
                  <Latex math="P_{in} = P_{out} + P_{loss} = \frac{P_{out}}{\eta}" block />
                  <div>The average DC input current over the switching period:</div>
                  <Latex math="I_{in,avg} = \frac{P_{in}}{V_{in}} = \frac{V_{out} \cdot I_{out}}{\eta \cdot V_{in}}" block />
                </div>
              )}
            </div>
          )}
          
          <div className="p-3 bg-slate-950/40 rounded-lg border border-slate-800 space-y-1 text-xs">
            <span className="text-[11px] font-semibold text-cyan-400 block mb-1">Stress & Operating Data</span>
            <div className="flex justify-between py-1 border-b border-slate-900">
              <span className="text-slate-400">DC Input Voltage Vin</span>
              <span className="font-mono text-slate-200"><span className="text-emerald-400 font-mono">{vin.toFixed(1)}</span> V</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-900">
              <span className="text-slate-400">Average Input Current Iin,avg</span>
              <span className="font-mono text-slate-200"><span className="text-emerald-400 font-mono">{iInAvg.toFixed(2)}</span> A</span>
            </div>
            <div className="flex justify-between py-1 text-cyan-300 font-semibold">
              <span>Total Input Power Pin</span>
              <span className="font-mono"><span className="text-emerald-400 font-mono">{pIn.toFixed(1)}</span> W</span>
            </div>
          </div>
          
          <div className="flex flex-col gap-1.5">
            <label className="text-[11px] text-slate-400 font-semibold">Adjust Vin (V)</label>
            <input className="flex h-8 w-full rounded-md border border-slate-850 bg-[#020617] px-3 py-1 text-xs outline-none focus:border-cyan-500 transition-colors font-mono text-cyan-400" type="number" value={vin} onChange={(e) => setVin(parseFloat(e.target.value) || 0)} />
          </div>
        </div>
      );

    case 'Cin':
      return (
        <div className="space-y-4 text-xs">
          <div className="flex justify-between items-center mb-1 bg-slate-900/30 p-1.5 rounded border border-slate-800/40">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Physical Formulation</span>
            {renderFormulaToggle()}
          </div>
          {expandFormula && (
            <div className="p-3 bg-slate-950/40 rounded-lg border border-slate-800 space-y-2 animate-in fade-in slide-in-from-top-1 duration-150">
              <span className="text-[11px] font-semibold text-cyan-400 block">Mathematical Model</span>
              <div className="text-[11px] text-slate-400 leading-relaxed">
                During switch on-time, the input capacitor provides primary current. Input ripple RMS is given by:
              </div>
              <Latex math="I_{cin,rms} = I_{in,avg} \cdot \sqrt{\frac{1 - D}{D}}" block />
              
              {renderDerivationToggle("Input Capacitor RMS Current Derivation")}
              {expandDerivation && (
                <div className="mt-2 p-2.5 bg-slate-950/60 rounded border border-slate-900/60 text-slate-400 text-[10px] leading-relaxed space-y-2">
                  <div>1. Waveform decomposition: During <Latex math="D \cdot T_{sw}" />, MOSFET conducts, capacitor current equals primary inductor current minus average input current. During <Latex math="(1-D) \cdot T_{sw}" />, MOSFET is off and capacitor current is <Latex math="-I_{in,avg}" />.</div>
                  <div>2. Integrating squared current yields:</div>
                  <Latex math="I_{cin,rms} = \sqrt{\frac{1}{T_{sw}} \left[ \int_0^{D T_{sw}} (i_p(t) - I_{in,avg})^2 dt + \int_{D T_{sw}}^{T_{sw}} (-I_{in,avg})^2 dt \right]}" block />
                  <div>Simplified approximation:</div>
                  <Latex math="I_{cin,rms} \approx I_{in,avg} \cdot \sqrt{\frac{1 - D}{D}}" block />
                </div>
              )}
            </div>
          )}
          
          <div className="p-3 bg-slate-950/40 rounded-lg border border-slate-800 space-y-1 text-xs">
            <span className="text-[11px] font-semibold text-cyan-400 block mb-1">Stress & Operating Data</span>
            <div className="flex justify-between py-1 border-b border-slate-900">
              <span className="text-slate-400">Input Capacitor Ripple Current RMS</span>
              <span className="font-mono text-slate-200">{calcData?.design ? (calcData?.design?.cin_rms_a)?.toFixed(2) ?? '-' : '-'} A</span>
            </div>
          </div>
        </div>
      );

    case 'Q1':
      return (
        <div className="space-y-4 text-xs">
          <div className="flex justify-between items-center mb-1 bg-slate-900/30 p-1.5 rounded border border-slate-800/40">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Physical Formulation</span>
            {renderFormulaToggle()}
          </div>
          {expandFormula && (
            <div className="p-3 bg-slate-950/40 rounded-lg border border-slate-800 space-y-2 animate-in fade-in slide-in-from-top-1 duration-150">
              <span className="text-[11px] font-semibold text-cyan-400 block">Mathematical Model</span>
              <div className="text-[11px] text-slate-400 leading-relaxed">
                Maximum Vds voltage stress, conduction loss, and estimated switching loss equations:
              </div>
              <Latex math="V_{ds,max} = V_{in} + V_{or} + V_{spike}" block />
              <Latex math="P_{cond} = I_{p,rms}^2 \cdot R_{ds(on)}" block />
              <Latex math="P_{sw} = \frac{1}{2} V_{ds,max} \cdot I_{p,pk} \cdot (t_{on} + t_{off}) \cdot f_{sw}" block />
              
              {renderDerivationToggle("MOSFET Voltage Stress & Dissipation")}
              {expandDerivation && (
                <div className="mt-2 p-2.5 bg-slate-950/60 rounded border border-slate-900/60 text-slate-400 text-[10px] leading-relaxed space-y-2.5">
                  <div>1. Voltage stress: At MOSFET turn-off, primary leakage energy dumps into the clamp network, creating voltage spike <Latex math="V_{spike}" /> on top of input voltage and reflected voltage <Latex math="V_{or}" />:</div>
                  <Latex math="V_{ds,max} = V_{in} + V_{or} + V_{spike}" block />
                  <div>Production design requires at least 20% voltage margin.</div>
                  <div>2. Conduction loss across channel resistance:</div>
                  <Latex math="P_{cond} = I_{p,rms}^2 \cdot R_{ds(on)}" block />
                  <div>3. Linear overlap switching loss model:</div>
                  <Latex math="P_{sw} = \frac{1}{2} V_{ds,max} \cdot I_{p,pk} \cdot (t_{on} + t_{off}) \cdot f_{sw}" block />
                </div>
              )}
            </div>
          )}
          
          <div className="p-3 bg-slate-950/40 rounded-lg border border-slate-800 space-y-1 text-xs">
            <span className="text-[11px] font-semibold text-cyan-400 block mb-1">Stress & Operating Data</span>
            <div className="flex justify-between py-1 border-b border-slate-900">
              <span className="text-slate-400">Peak Voltage Vds_max</span>
              <span className="font-mono text-slate-200"><span className="text-emerald-400 font-mono">{vdsMax.toFixed(1)}</span> V</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-900">
              <span className="text-slate-400">Primary Peak Current Ip,pk</span>
              <span className="font-mono text-slate-200"><span className="text-emerald-400 font-mono">{ipk.toFixed(2)}</span> A</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-900">
              <span className="text-slate-400">Primary RMS Current Ip,rms</span>
              <span className="font-mono text-slate-200"><span className="text-emerald-400 font-mono">{ipRms.toFixed(2)}</span> A</span>
            </div>
          </div>
        </div>
      );

    case 'T1':
      return (
        <div className="space-y-4 text-xs">
          <div className="flex justify-between items-center mb-1 bg-slate-900/30 p-1.5 rounded border border-slate-800/40">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Physical Formulation</span>
            {renderFormulaToggle()}
          </div>
          {expandFormula && (
            <div className="p-3 bg-slate-950/40 rounded-lg border border-slate-800 space-y-2 animate-in fade-in slide-in-from-top-1 duration-150">
              <span className="text-[11px] font-semibold text-cyan-400 block">Mathematical Model</span>
              <div className="text-[11px] text-slate-400 leading-relaxed">
                Recommended primary inductance Lp, turns count, and air gap equations:
              </div>
              <Latex math="L_p = \frac{V_{in}^2 \cdot D_{max}^2}{2 \cdot P_{in} \cdot f_{sw}}" block />
              <Latex math="N_p = \frac{L_p \cdot I_{p,pk}}{B_{max} \cdot A_e}" block />
              <Latex math="l_g \approx \frac{\mu_0 \cdot N_p^2 \cdot A_e}{L_p}" block />
              
              {renderDerivationToggle("Flyback Transformer Magnetics")}
              {expandDerivation && (
                <div className="mt-2 p-2.5 bg-slate-950/60 rounded border border-slate-900/60 text-slate-400 text-[10px] leading-relaxed space-y-2.5">
                  <div>1. Primary inductance Lp: Stores energy during conduction and transfers during off-time:</div>
                  <Latex math="L_p = \frac{V_{in}^2 \cdot D_{max}^2}{2 \cdot P_{in} \cdot f_{sw}}" block />
                  <div>2. Primary turns Np to prevent core saturation below <Latex math="B_{max}" />:</div>
                  <Latex math="N_p = \frac{L_p \cdot I_{p,pk}}{B_{max} \cdot A_e}" block />
                  <div>3. Physical air gap length lg ignoring core reluctance:</div>
                  <Latex math="l_g = \frac{\mu_0 \cdot N_p^2 \cdot A_e}{L_p}" block />
                </div>
              )}
            </div>
          )}
          
          <div className="p-3 bg-slate-950/40 rounded-lg border border-slate-800 space-y-1 text-xs">
            <span className="text-[11px] font-semibold text-cyan-400 block mb-1">Magnetic Design Data</span>
            <div className="flex justify-between py-1 border-b border-slate-900">
              <span className="text-slate-400">Primary Inductance Lp</span>
              <span className="font-mono text-slate-200">{calcData?.design ? (calcData?.design?.lp_design_uh)?.toFixed(1) ?? '-' : '-'} μH</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-900">
              <span className="text-slate-400">Primary Turns Np</span>
              <span className="font-mono text-slate-200">{calcData?.design ? calcData.design.np_design_turns : '-'} Turns</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-900">
              <span className="text-slate-400">Secondary Turns Ns</span>
              <span className="font-mono text-slate-200">{calcData?.design ? calcData.design.ns_design_turns : '-'} Turns</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-900">
              <span className="text-slate-400">Air Gap Length lg</span>
              <span className="font-mono text-slate-200">{calcData?.design ? (calcData?.design?.lg_design_mm)?.toFixed(3) ?? '-' : '-'} mm</span>
            </div>
          </div>
          
          <div className="grid grid-cols-3 gap-2">
            <div className="flex flex-col gap-1">
              <label className="text-[10px] text-slate-400 font-semibold">Reflected Vor (V)</label>
              <input className="flex h-8 w-full rounded-md border border-slate-850 bg-[#020617] px-2 py-1 text-xs outline-none focus:border-cyan-500 transition-colors font-mono text-cyan-400" type="number" value={vor} onChange={(e) => setVor(parseFloat(e.target.value) || 0)} />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-[10px] text-slate-400 font-semibold">Bmax (T)</label>
              <input className="flex h-8 w-full rounded-md border border-slate-850 bg-[#020617] px-2 py-1 text-xs outline-none focus:border-cyan-500 transition-colors font-mono text-cyan-400" type="number" step="0.05" value={bmax} onChange={(e) => setBmax(parseFloat(e.target.value) || 0)} />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-[10px] text-slate-400 font-semibold">Core Ae (mm²)</label>
              <input className="flex h-8 w-full rounded-md border border-slate-850 bg-[#020617] px-2 py-1 text-xs outline-none focus:border-cyan-500 transition-colors font-mono text-cyan-400" type="number" value={ae} onChange={(e) => setAe(parseFloat(e.target.value) || 0)} />
            </div>
          </div>
        </div>
      );

    case 'D_clamp':
    case 'R_clamp':
    case 'C_clamp':
      return (
        <div className="space-y-4 text-xs">
          <div className="flex justify-between items-center mb-1 bg-slate-900/30 p-1.5 rounded border border-slate-800/40">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Physical Formulation</span>
            {renderFormulaToggle()}
          </div>
          {expandFormula && (
            <div className="p-3 bg-slate-950/40 rounded-lg border border-slate-800 space-y-2 animate-in fade-in slide-in-from-top-1 duration-150">
              <span className="text-[11px] font-semibold text-cyan-400 block">Mathematical Model</span>
              <div className="text-[11px] text-slate-400 leading-relaxed">
                RCD snubber design equations for primary leakage clamp:
              </div>
              <Latex math="P_{clamp} = \frac{1}{2} L_{lk} \cdot I_{p,pk}^2 \cdot f_{sw} \cdot \frac{V_c}{V_c - V_{or}}" block />
              <Latex math="R_{clamp} = \frac{V_c^2}{P_{clamp}}" block />
              <Latex math="C_{clamp} = \frac{V_c}{\Delta V_c \cdot R_{clamp} \cdot f_{sw}}" block />
              
              {renderDerivationToggle("RCD Clamp Snubber Derivations")}
              {expandDerivation && (
                <div className="mt-2 p-2.5 bg-slate-950/60 rounded border border-slate-900/60 text-slate-400 text-[10px] leading-relaxed space-y-2.5">
                  <div>1. Leakage energy transfer: Leakage energy stored in <Latex math="L_{lk}" /> dumps through the diode into <Latex math="C_{clamp}" />. Dissipated power:</div>
                  <Latex math="P_{clamp} = \frac{1}{2} L_{lk} \cdot I_{p,pk}^2 \cdot f_{sw} \cdot \frac{V_c}{V_c - V_{or}}" block />
                  <div>2. Bleeder resistor value:</div>
                  <Latex math="R_{clamp} = \frac{V_c^2}{P_{clamp}}" block />
                  <div>3. Clamp capacitance for 10% ripple:</div>
                  <Latex math="C_{clamp} = \frac{V_c}{0.1 \cdot V_c \cdot R_{clamp} \cdot f_{sw}} = \frac{10}{R_{clamp} \cdot f_{sw}}" block />
                </div>
              )}
            </div>
          )}
          
          <div className="p-3 bg-slate-950/40 rounded-lg border border-slate-800 space-y-1 text-xs">
            <span className="text-[11px] font-semibold text-cyan-400 block mb-1">Snubber Design Data</span>
            <div className="flex justify-between py-1 border-b border-slate-900">
              <span className="text-slate-400">Recommended R_clamp</span>
              <span className="font-mono text-slate-200">{calcData?.design ? (calcData?.design?.r_clamp_recommend_kohm)?.toFixed(1) ?? '-' : '-'} kΩ</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-900">
              <span className="text-slate-400">Recommended C_clamp</span>
              <span className="font-mono text-slate-200">{calcData?.design ? (calcData?.design?.c_clamp_recommend_nf)?.toFixed(1) ?? '-' : '-'} nF</span>
            </div>
            <div className="flex justify-between py-1 text-cyan-300 font-semibold">
              <span>Snubber Dissipation P_loss</span>
              <span className="font-mono">{calcData?.design ? (calcData?.design?.p_clamp_recommend_w)?.toFixed(2) ?? '-' : '-'} W</span>
            </div>
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div className="flex flex-col gap-1.5">
              <label className="text-[11px] text-slate-400 font-semibold">Leakage Inductance L_lk (μH)</label>
              <input className="flex h-8 w-full rounded-md border border-slate-855 bg-[#020617] px-3 py-1 text-xs outline-none focus:border-cyan-500 transition-colors font-mono text-cyan-400" type="number" value={rcdLlk} onChange={(e) => setRcdLlk(parseFloat(e.target.value) || 0)} />
            </div>
            <div className="flex flex-col gap-1.5">
              <label className="text-[11px] text-slate-400 font-semibold">Max Allowable Spike V_spike (V)</label>
              <input className="flex h-8 w-full rounded-md border border-slate-855 bg-[#020617] px-3 py-1 text-xs outline-none focus:border-cyan-500 transition-colors font-mono text-cyan-400" type="number" value={rcdVspike} onChange={(e) => setRcdVspike(parseFloat(e.target.value) || 0)} />
            </div>
          </div>
        </div>
      );

    case 'D1':
      return (
        <div className="space-y-4 text-xs">
          <div className="flex justify-between items-center mb-1 bg-slate-900/30 p-1.5 rounded border border-slate-800/40">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Physical Formulation</span>
            {renderFormulaToggle()}
          </div>
          {expandFormula && (
            <div className="p-3 bg-slate-950/40 rounded-lg border border-slate-800 space-y-2 animate-in fade-in slide-in-from-top-1 duration-150">
              <span className="text-[11px] font-semibold text-cyan-400 block">Mathematical Model</span>
              <div className="text-[11px] text-slate-400 leading-relaxed">
                Secondary rectifier reverse voltage stress and conduction loss:
              </div>
              <Latex math="V_{rev,max} = V_{out} + \frac{V_{in}}{N_{ps}}" block />
              <Latex math="P_{diode,cond} = I_{out} \cdot V_f" block />
              
              {renderDerivationToggle("Rectifier Voltage Stress")}
              {expandDerivation && (
                <div className="mt-2 p-2.5 bg-slate-950/60 rounded border border-slate-900/60 text-slate-400 text-[10px] leading-relaxed space-y-2">
                  <div>1. Reverse voltage stress when Q1 conducts: Secondary diode reverse voltage is the sum of output voltage and transformed primary input voltage:</div>
                  <Latex math="V_{rev,max} = V_{out} + \frac{V_{in}}{N_{ps}}" block />
                  <div>2. Diode conduction dissipation:</div>
                  <Latex math="P_{diode,cond} = I_{diode,avg} \cdot V_f = I_{out} \cdot V_f" block />
                </div>
              )}
            </div>
          )}
          
          <div className="p-3 bg-slate-950/40 rounded-lg border border-slate-800 space-y-1 text-xs">
            <span className="text-[11px] font-semibold text-cyan-400 block mb-1">Stress & Operating Data</span>
            <div className="flex justify-between py-1 border-b border-slate-900">
              <span className="text-slate-400">Max Reverse Voltage Vr_max</span>
              <span className="font-mono text-slate-200"><span className="text-emerald-400 font-mono">{vrevMax.toFixed(1)}</span> V</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-900">
              <span className="text-slate-400">Secondary RMS Current Is,rms</span>
              <span className="font-mono text-slate-200"><span className="text-emerald-400 font-mono">{isRms.toFixed(2)}</span> A</span>
            </div>
            <div className="flex justify-between py-1 text-cyan-300 font-semibold">
              <span>Conduction Loss P_diode</span>
              <span className="font-mono">{(iout * diodeVfNom).toFixed(2)} W</span>
            </div>
          </div>
        </div>
      );

    case 'Cout':
      return (
        <div className="space-y-4 text-xs">
          <div className="flex justify-between items-center mb-1 bg-slate-900/30 p-1.5 rounded border border-slate-800/40">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Physical Formulation</span>
            {renderFormulaToggle()}
          </div>
          {expandFormula && (
            <div className="p-3 bg-slate-950/40 rounded-lg border border-slate-800 space-y-2 animate-in fade-in slide-in-from-top-1 duration-150">
              <span className="text-[11px] font-semibold text-cyan-400 block">Mathematical Model</span>
              <div className="text-[11px] text-slate-400 leading-relaxed">
                Output capacitor sizing constrained by ripple voltage and ESR:
              </div>
              <Latex math="C_{o,min} = \frac{I_{out} \cdot D_{max}}{f_{sw} \cdot \Delta V_{out,c}}" block />
              <Latex math="\Delta V_{out} \approx \frac{I_{out} \cdot D}{C_o \cdot f_{sw}} + I_{s,pk} \cdot ESR" block />
              
              {renderDerivationToggle("Output Filter Capacitor & Ripple")}
              {expandDerivation && (
                <div className="mt-2 p-2.5 bg-slate-950/60 rounded border border-slate-900/60 text-slate-400 text-[10px] leading-relaxed space-y-2.5">
                  <div>1. Capacitive ripple: During Q1 on-time, the capacitor alone supplies the load:</div>
                  <Latex math="\Delta V_c = \frac{\Delta Q}{C_o} = \frac{I_{out} \cdot D}{C_o \cdot f_{sw}}" block />
                  <div>2. Resistive ESR ripple: At Q1 turn-off, secondary current steps to <Latex math="I_{s,pk}" />:</div>
                  <Latex math="\Delta V_{ESR} = I_{s,pk} \cdot ESR" block />
                  <div>3. Total peak-to-peak output ripple:</div>
                  <Latex math="\Delta V_{out} = \Delta V_c + \Delta V_{ESR} = \frac{I_{out} \cdot D}{C_o \cdot f_{sw}} + I_{s,pk} \cdot ESR" block />
                </div>
              )}
            </div>
          )}
          
          <div className="p-3 bg-slate-950/40 rounded-lg border border-slate-800 space-y-1 text-xs">
            <span className="text-[11px] font-semibold text-cyan-400 block mb-1">Capacitor Design Data</span>
            <div className="flex justify-between py-1 border-b border-slate-900">
              <span className="text-slate-400">Min Required Capacitance Co,min</span>
              <span className="font-mono text-slate-200">{calcData?.design ? (calcData?.design?.c_out_design_uf)?.toFixed(1) ?? '-' : '-'} μF</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-900">
              <span className="text-slate-400">Secondary Ripple Current RMS</span>
              <span className="font-mono text-slate-200">{calcData?.design ? (calcData?.design?.cout_rms_a)?.toFixed(2) ?? '-' : '-'} A</span>
            </div>
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div className="flex flex-col gap-1.5">
              <label className="text-[11px] text-slate-400 font-semibold">Adjust Output Cap Co (μF)</label>
              <input className="flex h-8 w-full rounded-md border border-slate-855 bg-[#020617] px-3 py-1 text-xs outline-none focus:border-cyan-500 transition-colors font-mono text-cyan-400" type="text" value={cUf} onChange={(e) => setCUf(e.target.value)} />
            </div>
            <div className="flex flex-col gap-1.5">
              <label className="text-[11px] text-slate-400 font-semibold">Adjust ESR (mΩ)</label>
              <input className="flex h-8 w-full rounded-md border border-slate-855 bg-[#020617] px-3 py-1 text-xs outline-none focus:border-cyan-500 transition-colors font-mono text-cyan-400" type="number" value={rcEsr} onChange={(e) => setRcEsr(parseFloat(e.target.value) || 0)} />
            </div>
          </div>
        </div>
      );

    case 'RL':
      return (
        <div className="space-y-4 text-xs">
          <div className="flex justify-between items-center mb-1 bg-slate-900/30 p-1.5 rounded border border-slate-800/40">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Physical Formulation</span>
            {renderFormulaToggle()}
          </div>
          {expandFormula && (
            <div className="p-3 bg-slate-950/40 rounded-lg border border-slate-800 space-y-2 animate-in fade-in slide-in-from-top-1 duration-150">
              <span className="text-[11px] font-semibold text-cyan-400 block">Mathematical Model</span>
              <div className="text-[11px] text-slate-400 leading-relaxed">
                Rated load resistance and output power:
              </div>
              <Latex math="R_L = \frac{V_{out}}{I_{out}}" block />
              <Latex math="P_{out} = V_{out} \cdot I_{out}" block />
            </div>
          )}
          
          <div className="p-3 bg-slate-950/40 rounded-lg border border-slate-800 space-y-1 text-xs">
            <span className="text-[11px] font-semibold text-cyan-400 block mb-1">Load Operating Data</span>
            <div className="flex justify-between py-1 border-b border-slate-900">
              <span className="text-slate-400">Equivalent Load RL</span>
              <span className="font-mono text-slate-200">{(vout / (iout || 1.0)).toFixed(2)} Ω</span>
            </div>
            <div className="flex justify-between py-1 text-cyan-300 font-semibold">
              <span>Rated Output Power Pout</span>
              <span className="font-mono">{(vout * iout).toFixed(1)} W</span>
            </div>
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div className="flex flex-col gap-1.5">
              <label className="text-[11px] text-slate-400 font-semibold">Adjust Vout (V)</label>
              <input className="flex h-8 w-full rounded-md border border-slate-855 bg-[#020617] px-3 py-1 text-xs outline-none focus:border-cyan-500 transition-colors font-mono text-cyan-400" type="number" value={vout} onChange={(e) => setVout(parseFloat(e.target.value) || 0)} />
            </div>
            <div className="flex flex-col gap-1.5">
              <label className="text-[11px] text-slate-400 font-semibold">Adjust Iout (A)</label>
              <input className="flex h-8 w-full rounded-md border border-slate-855 bg-[#020617] px-3 py-1 text-xs outline-none focus:border-cyan-500 transition-colors font-mono text-cyan-400" type="number" value={iout} onChange={(e) => setIout(parseFloat(e.target.value) || 0)} />
            </div>
          </div>
        </div>
      );

    case 'GND':
    case 'GND_sec':
      return (
        <div className="space-y-4 text-xs">
          <div className="flex justify-between items-center mb-1 bg-slate-900/30 p-1.5 rounded border border-slate-800/40">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Ground Reference Notes</span>
            {renderFormulaToggle()}
          </div>
          {expandFormula && (
            <div className="p-3 bg-slate-950/40 rounded-lg border border-slate-800 space-y-2 animate-in fade-in slide-in-from-top-1 duration-150">
              <div className="text-[11px] text-slate-400 leading-relaxed">
                Primary PGND (power ground) and secondary SGND (signal/isolated ground) in a flyback converter must remain galvanically isolated to prevent high common-mode switching noise from corrupting sensitive loads.
              </div>
              <Latex math="V_{PGND} = 0\text{ V} \quad \text{vs} \quad V_{SGND} = 0\text{ V}" block />
            </div>
          )}
        </div>
      );

    default:
      return null;
  }
}