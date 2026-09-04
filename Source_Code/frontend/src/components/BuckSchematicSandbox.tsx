import React, { useState, useEffect, useRef } from 'react';
import katex from 'katex';
import 'katex/dist/katex.min.css';
import { Button } from './ui/Button';
import {
  SchematicCapacitorPolar,
  SchematicDCSource,
  SchematicDiode,
  SchematicGround,
  SchematicInductor,
  SchematicMosfetN,
  SchematicResistor
} from './ui/SchematicSymbols';

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

interface BuckSchematicSandboxProps {
  vin: number;
  setVin: (v: number) => void;
  vout: number;
  setVout: (v: number) => void;
  iout: number;
  setIout: (v: number) => void;
  fsw: number;
  setFsw: (v: number) => void;
  lir: number;
  setLir: (v: number) => void;
  vrip: number;
  setVrip: (v: number) => void;
  lUh: string;
  setLUh: (v: string) => void;
  cUf: string;
  setCUf: (v: string) => void;
  esr: number;
  setEsr: (v: number) => void;
  cinUf: string;
  setCinUf: (v: string) => void;
  cinEsr: number;
  setCinEsr: (v: number) => void;
  swRdsOn: number;
  setSwRdsOn: (v: number) => void;
  swTimes: number;
  setSwTimes: (v: number) => void;
  diodeVf: number;
  setDiodeVf: (v: number) => void;
  indDcr: number;
  setIndDcr: (v: number) => void;
  calcData: any;
  diodeType?: string;
  setDiodeType?: (v: string) => void;
  diodeQrr?: number;
  setDiodeQrr?: (v: number) => void;
  syncRdsOn?: number;
  setSyncRdsOn?: (v: number) => void;
  syncDeadTime?: number;
  setSyncDeadTime?: (v: number) => void;
  syncBodyVf?: number;
  setSyncBodyVf?: (v: number) => void;
}

const componentTemplates: { [key: string]: { [pin: string]: { x: number; y: number } } } = {
  Vin: { P: { x: -40, y: 0 }, N: { x: 40, y: 0 } },
  Cin: { P: { x: -40, y: 0 }, N: { x: 40, y: 0 } },
  Q1: { D: { x: 0, y: -40 }, S: { x: 0, y: 40 } },
  D1: { A: { x: -40, y: 0 }, K: { x: 40, y: 0 } },
  Lo: { Pin1: { x: -40, y: 0 }, Pin2: { x: 40, y: 0 } },
  Co: { P: { x: -40, y: 0 }, N: { x: 40, y: 0 } },
  RL: { Pin1: { x: -40, y: 0 }, Pin2: { x: 40, y: 0 } },
  GND: { Pin: { x: 0, y: 0 } }
};

const allPins = [
  "Vin.P", "Vin.N",
  "Cin.P", "Cin.N",
  "Q1.D", "Q1.S",
  "D1.A", "D1.K",
  "Lo.Pin1", "Lo.Pin2",
  "Co.P", "Co.N",
  "RL.Pin1", "RL.Pin2",
  "GND.Pin"
];

const pinToNetGroup: { [pin: string]: string } = {
  "Vin.P": "Net_Vin", "Cin.P": "Net_Vin", "Q1.D": "Net_Vin",
  "Q1.S": "Net_SW", "D1.K": "Net_SW", "Lo.Pin1": "Net_SW",
  "Lo.Pin2": "Net_Vout", "Co.P": "Net_Vout", "RL.Pin1": "Net_Vout",
  "Vin.N": "Net_GND", "Cin.N": "Net_GND", "D1.A": "Net_GND", "Co.N": "Net_GND", "RL.Pin2": "Net_GND", "GND.Pin": "Net_GND"
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
  if (compId === 'GND') return 'V';
  if (compId === 'Vin' || compId === 'Cin' || compId === 'Co' || compId === 'RL') {
    return rotation % 180 === 90 ? 'V' : 'H';
  }
  if (compId === 'Q1') {
    return rotation % 180 === 90 ? 'H' : 'V';
  }
  if (compId === 'D1') {
    return rotation % 180 === 90 ? 'V' : 'H';
  }
  if (compId === 'Lo') {
    return rotation % 180 === 90 ? 'V' : 'H';
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

  if (cA.x === cB.x && cA.y === cB.y) {
    return [[cA.x, cA.y]];
  }

  if (dirA !== dirB) {
    if (dirA === 'V' && dirB === 'H') {
      const midY = cB.y + offset;
      return [[cA.x, cA.y], [cA.x, midY], [cB.x, midY], [cB.x, cB.y]];
    } else {
      const midX = cB.x + offset;
      return [[cA.x, cA.y], [midX, cA.y], [midX, cB.y], [cB.x, cB.y]];
    }
  }

  if (dirA === 'V' && dirB === 'V') {
    const midY = Math.round((cA.y + cB.y) / 2) + offset;
    return [[cA.x, cA.y], [cA.x, midY], [cB.x, midY], [cB.x, cB.y]];
  } else {
    const midX = Math.round((cA.x + cB.x) / 2) + offset;
    return [[cA.x, cA.y], [midX, cA.y], [midX, cB.y], [cB.x, cB.y]];
  }
}

export default function BuckSchematicSandbox({
  vin, setVin,
  vout, setVout,
  iout, setIout,
  fsw, setFsw,
  lir, setLir,
  vrip, setVrip,
  lUh, setLUh,
  cUf, setCUf,
  esr, setEsr,
  cinUf, setCinUf,
  cinEsr, setCinEsr,
  swRdsOn, setSwRdsOn,
  swTimes, setSwTimes,
  diodeVf, setDiodeVf,
  indDcr, setIndDcr,
  calcData,
  diodeType = 'schottky',
  setDiodeType,
  diodeQrr = 0,
  setDiodeQrr,
  syncRdsOn = 10,
  setSyncRdsOn,
  syncDeadTime = 50,
  setSyncDeadTime,
  syncBodyVf = 0.8,
  setSyncBodyVf
}: BuckSchematicSandboxProps) {
  const [componentsPos, setComponentsPos] = useState<{ [key: string]: { x: number; y: number; rotation: number } }>(() => {
    const saved = localStorage.getItem('toolbox_buck_layout_pos');
    if (saved) {
      try { return JSON.parse(saved); } catch (e) { console.error("Error loading layout pos", e); }
    }
    return {
      Vin: { x: 100, y: 200, rotation: 90 },
      Cin: { x: 200, y: 200, rotation: 90 },
      Q1: { x: 300, y: 100, rotation: 270 },
      D1: { x: 400, y: 200, rotation: 270 },
      Lo: { x: 500, y: 100, rotation: 0 },
      Co: { x: 600, y: 200, rotation: 90 },
      RL: { x: 700, y: 200, rotation: 90 },
      GND: { x: 400, y: 280, rotation: 0 }
    };
  });

  const [wires, setWires] = useState<{ from: string; to: string }[]>(() => {
    const saved = localStorage.getItem('toolbox_buck_layout_wires');
    if (saved) {
      try { return JSON.parse(saved); } catch (e) { console.error("Error loading layout wires", e); }
    }
    return [
      { from: 'Vin.P', to: 'Cin.P' },
      { from: 'Cin.P', to: 'Q1.D' },
      { from: 'Q1.S', to: 'D1.K' },
      { from: 'D1.K', to: 'Lo.Pin1' },
      { from: 'Lo.Pin2', to: 'Co.P' },
      { from: 'Co.P', to: 'RL.Pin1' },
      { from: 'Vin.N', to: 'Cin.N' },
      { from: 'Cin.N', to: 'D1.A' },
      { from: 'D1.A', to: 'GND.Pin' },
      { from: 'GND.Pin', to: 'Co.N' },
      { from: 'Co.N', to: 'RL.Pin2' }
    ];
  });

  const [activeDragComponent, setActiveDragComponent] = useState<string | null>(null);
  const [dragStartPin, setDragStartPin] = useState<string | null>(null);
  const [tempWireEnd, setTempWireEnd] = useState<{ x: number; y: number } | null>(null);
  const [snapTargetPin, setSnapTargetPin] = useState<string | null>(null);
  const [drcViolation, setDrcViolation] = useState<{ message: string; x: number; y: number } | null>(null);
  const [selectedWire, setSelectedWire] = useState<number | null>(null);
  const [hoveredWire, setHoveredWire] = useState<number | null>(null);
  const [selectedComponent, setSelectedComponent] = useState<string | null>(null);
  const [hoveredComponent, setHoveredComponent] = useState<string | null>(null);
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

  const [wireOffsets, setWireOffsets] = useState<{ [key: string]: number }>(() => {
    const saved = localStorage.getItem('toolbox_buck_layout_offsets');
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

  const dragStartOffset = useRef<{ x: number; y: number }>({ x: 0, y: 0 });
  const dragStartCoords = useRef<{ x: number; y: number }>({ x: 0, y: 0 });
  const hasDragged = useRef<boolean>(false);
  const svgRef = useRef<SVGSVGElement>(null);

  const allPinCoords = new Map<string, { x: number; y: number }>();
  Object.entries(componentsPos).forEach(([compId, pos]) => {
    const template = componentTemplates[compId];
    if (template) {
      Object.entries(template).forEach(([pinName, local]) => {
        const globalCoords = getGlobalPinCoords(pos.x, pos.y, pos.rotation, local.x, local.y);
        allPinCoords.set(`${compId}.${pinName}`, globalCoords);
      });
    }
  });

  interface Flyline {
    from: string;
    to: string;
    fromCoords: { x: number; y: number };
    toCoords: { x: number; y: number };
  }

  const getRatsnestLines = (): Flyline[] => {
    const parent = new Map<string, string>();
    allPins.forEach(p => parent.set(p, p));

    function find(i: string): string {
      if (parent.get(i) === i) return i;
      const root = find(parent.get(i)!);
      parent.set(i, root);
      return root;
    }

    function union(i: string, j: string) {
      const rootI = find(i);
      const rootJ = find(j);
      if (rootI !== rootJ) {
        parent.set(rootI, rootJ);
      }
    }

    wires.forEach(w => {
      if (parent.has(w.from) && parent.has(w.to)) {
        union(w.from, w.to);
      }
    });

    const netPinGroups: { [net: string]: string[] } = {};
    allPins.forEach(p => {
      const net = pinToNetGroup[p];
      if (!netPinGroups[net]) netPinGroups[net] = [];
      netPinGroups[net].push(p);
    });

    const flylines: Flyline[] = [];

    Object.values(netPinGroups).forEach(groupPins => {
      const connectedComponents: { [root: string]: string[] } = {};
      groupPins.forEach(p => {
        const root = find(p);
        if (!connectedComponents[root]) connectedComponents[root] = [];
        connectedComponents[root].push(p);
      });

      const roots = Object.keys(connectedComponents);
      if (roots.length > 1) {
        for (let i = 1; i < roots.length; i++) {
          const compA = connectedComponents[roots[0]];
          const compB = connectedComponents[roots[i]];
          let minDist = Infinity;
          let bestPair: [string, string] = [compA[0], compB[0]];

          compA.forEach(pA => {
            const cA = allPinCoords.get(pA);
            compB.forEach(pB => {
              const cB = allPinCoords.get(pB);
              if (cA && cB) {
                const dist = Math.hypot(cA.x - cB.x, cA.y - cB.y);
                if (dist < minDist) {
                  minDist = dist;
                  bestPair = [pA, pB];
                }
              }
            });
          });

          const pA = bestPair[0];
          const pB = bestPair[1];
          const cA = allPinCoords.get(pA)!;
          const cB = allPinCoords.get(pB)!;
          flylines.push({
            from: pA,
            to: pB,
            fromCoords: cA,
            toCoords: cB
          });
        }
      }
    });

    return flylines;
  };

  const ratsnestLines = getRatsnestLines();

  useEffect(() => {
    if (Object.keys(componentsPos).length > 0) {
      localStorage.setItem('toolbox_buck_layout_pos', JSON.stringify(componentsPos));
    }
  }, [componentsPos]);

  useEffect(() => {
    localStorage.setItem('toolbox_buck_layout_wires', JSON.stringify(wires));
  }, [wires]);

  useEffect(() => {
    localStorage.setItem('toolbox_buck_layout_offsets', JSON.stringify(wireOffsets));
  }, [wireOffsets]);

  const [saveTip, setSaveTip] = useState<string | null>(null);

  const handleSaveLayout = () => {
    localStorage.setItem('toolbox_buck_layout_pos', JSON.stringify(componentsPos));
    localStorage.setItem('toolbox_buck_layout_wires', JSON.stringify(wires));
    localStorage.setItem('toolbox_buck_layout_offsets', JSON.stringify(wireOffsets));
    setSaveTip("Saved layout & wires!");
    setTimeout(() => setSaveTip(null), 2500);
  };

  const getSvgCoords = (e: React.MouseEvent) => {
    if (!svgRef.current) return { x: 0, y: 0 };
    const rect = svgRef.current.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * 800;
    const y = ((e.clientY - rect.top) / rect.height) * 400;
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

      newX = Math.max(40, Math.min(760, newX));
      newY = Math.max(40, Math.min(360, newY));

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
    } else if (dragStartPin) {
      setTempWireEnd(coords);
      let target: string | null = null;
      let minTargetDist = 30;

      Array.from(allPinCoords.entries()).forEach(([pinId, pinCoords]) => {
        if (pinId !== dragStartPin) {
          const dist = Math.hypot(coords.x - pinCoords.x, coords.y - pinCoords.y);
          if (dist < minTargetDist) {
            minTargetDist = dist;
            target = pinId;
          }
        }
      });

      if (target && pinToNetGroup[target] === pinToNetGroup[dragStartPin]) {
        setSnapTargetPin(target);
      } else {
        setSnapTargetPin(null);
      }
    }
  };

  const handleMouseUp = (e: React.MouseEvent) => {
    if (activeDragWire) {
      setActiveDragWire(null);
      return;
    }

    if (activeDragComponent) {
      const compId = activeDragComponent;
      setActiveDragComponent(null);
      if (!hasDragged.current) {
        setActiveModalComponent(compId);
      }
    } else if (dragStartPin) {
      let finalTarget = snapTargetPin;
      
      if (!finalTarget) {
        const coords = getSvgCoords(e);
        let minTargetDist = 30;
        Array.from(allPinCoords.entries()).forEach(([pinId, pinCoords]) => {
          if (pinId !== dragStartPin) {
            const dist = Math.hypot(coords.x - pinCoords.x, coords.y - pinCoords.y);
            if (dist < minTargetDist) {
              minTargetDist = dist;
              finalTarget = pinId;
            }
          }
        });
      }

      if (finalTarget) {
        const startNet = pinToNetGroup[dragStartPin];
        const targetNet = pinToNetGroup[finalTarget];

        if (startNet === targetNet) {
          const exists = wires.some(
            w => (w.from === dragStartPin && w.to === finalTarget) ||
                 (w.from === finalTarget && w.to === dragStartPin)
          );
          if (!exists) {
            setWires(prev => [...prev, { from: dragStartPin, to: finalTarget! }]);
          }
        } else {
          const coords = getSvgCoords(e);
          let illegalTarget: string | null = null;
          let minIllegalDist = 30;
          let targetCoords = coords;
          
          Array.from(allPinCoords.entries()).forEach(([pinId, pinC]) => {
            if (pinId !== dragStartPin) {
              const dist = Math.hypot(coords.x - pinC.x, coords.y - pinC.y);
              if (dist < minIllegalDist) {
                minIllegalDist = dist;
                illegalTarget = pinId;
                targetCoords = pinC;
              }
            }
          });

          let explanation = '';
          if (startNet === 'Net_SW' && targetNet === 'Net_GND') {
            explanation = ' (Shorts the switching node directly to ground, destroying the MOSFET switch)';
          } else if (startNet === 'Net_Vin' && targetNet === 'Net_GND') {
            explanation = ' (Causes a dead short across the DC input power source, highly hazardous)';
          } else if (startNet === 'Net_SW' && targetNet === 'Net_Vout') {
            explanation = ' (Bypasses the power inductor, passing Vin directly to the output load)';
          } else {
            explanation = ' (Different electrical nets cannot be connected)';
          }

          const msg = `Cannot connect ${dragStartPin} and ${finalTarget || illegalTarget}: ${explanation}`;
          setDrcViolation({
            message: msg,
            x: targetCoords.x,
            y: targetCoords.y
          });
          setTimeout(() => {
            setDrcViolation(prev => {
              if (prev && prev.message === msg) return null;
              return prev;
            });
          }, 4000);
        }
      }

      setDragStartPin(null);
      setTempWireEnd(null);
      setSnapTargetPin(null);
    }
  };

  const getWirePoints = (w: { from: string; to: string }) => {
    const cA = allPinCoords.get(w.from);
    const cB = allPinCoords.get(w.to);
    if (!cA || !cB) return [];
    
    const compA = w.from.split('.')[0];
    const compB = w.to.split('.')[0];
    const rotA = componentsPos[compA]?.rotation ?? 0;
    const rotB = componentsPos[compB]?.rotation ?? 0;

    const wireKey = `${w.from}->${w.to}`;
    const offset = wireOffsets[wireKey] ?? 0;
    return routeOrthogonal(w.from, w.to, cA, cB, rotA, rotB, offset);
  };

  const handleResetScattered = () => {
    localStorage.removeItem('toolbox_buck_layout_pos');
    localStorage.removeItem('toolbox_buck_layout_wires');
    localStorage.removeItem('toolbox_buck_layout_offsets');
    setComponentsPos({
      Vin: { x: 100, y: 300, rotation: 90 },
      Cin: { x: 160, y: 120, rotation: 90 },
      Q1: { x: 300, y: 260, rotation: 270 },
      D1: { x: 260, y: 100, rotation: 270 },
      Lo: { x: 460, y: 280, rotation: 0 },
      Co: { x: 500, y: 120, rotation: 90 },
      RL: { x: 680, y: 260, rotation: 90 },
      GND: { x: 400, y: 360, rotation: 0 }
    });
    setWires([]);
    setWireOffsets({});
    setDrcViolation(null);
  };

  const handleAutoAlign = () => {
    localStorage.removeItem('toolbox_buck_layout_pos');
    localStorage.removeItem('toolbox_buck_layout_wires');
    localStorage.removeItem('toolbox_buck_layout_offsets');
    setComponentsPos({
      Vin: { x: 100, y: 200, rotation: 90 },
      Cin: { x: 200, y: 200, rotation: 90 },
      Q1: { x: 300, y: 100, rotation: 270 },
      D1: { x: 400, y: 200, rotation: 270 },
      Lo: { x: 500, y: 100, rotation: 0 },
      Co: { x: 600, y: 200, rotation: 90 },
      RL: { x: 700, y: 200, rotation: 90 },
      GND: { x: 400, y: 280, rotation: 0 }
    });
    setWires([
      { from: 'Vin.P', to: 'Cin.P' },
      { from: 'Cin.P', to: 'Q1.D' },
      { from: 'Q1.S', to: 'D1.K' },
      { from: 'D1.K', to: 'Lo.Pin1' },
      { from: 'Lo.Pin2', to: 'Co.P' },
      { from: 'Co.P', to: 'RL.Pin1' },
      { from: 'Vin.N', to: 'Cin.N' },
      { from: 'Cin.N', to: 'D1.A' },
      { from: 'D1.A', to: 'GND.Pin' },
      { from: 'GND.Pin', to: 'Co.N' },
      { from: 'Co.N', to: 'RL.Pin2' }
    ]);
    setWireOffsets({});
    setDrcViolation(null);
  };

  const getModalTitle = (compId: string) => {
    switch (compId) {
      case 'Vin': return 'Vin - DC Input Voltage Source Parameters';
      case 'Cin': return 'Cin - Input Filter Capacitor Parameters';
      case 'Q1': return 'Q1 - Main Switching MOSFET Parameters';
      case 'D1': return 'D1 - Freewheeling Diode / Synchronous Rectifier Parameters';
      case 'Lo': return 'Lo - Power Filter Inductor Parameters';
      case 'Co': return 'Co - Output Filter Capacitor Parameters';
      case 'RL': return 'RL - System Equivalent Rated Load Resistor';
      case 'GND': return 'GND - System Ground Reference';
      default: return '';
    }
  };

  const handleWireSegmentMouseDown = (
    wireKey: string,
    _wireIdx: number,
    isHorizontal: boolean,
    e: React.MouseEvent
  ) => {
    e.stopPropagation();
    e.preventDefault();
    const coords = getSvgCoords(e);
    const currentOffset = wireOffsets[wireKey] ?? 0;
    setActiveDragWire({
      wireKey,
      isHorizontal,
      startMouseCoord: isHorizontal ? coords.y : coords.x,
      startOffset: currentOffset,
      hasDragged: false
    });
  };

  const handleComponentMouseDown = (compId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    const coords = getSvgCoords(e);
    dragStartOffset.current = {
      x: coords.x - componentsPos[compId].x,
      y: coords.y - componentsPos[compId].y
    };
    dragStartCoords.current = {
      x: componentsPos[compId].x,
      y: componentsPos[compId].y
    };
    hasDragged.current = false;
    setActiveDragComponent(compId);
  };

  const handlePinMouseDown = (pinId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    const coords = allPinCoords.get(pinId)!;
    setDragStartPin(pinId);
    setTempWireEnd({ x: coords.x, y: coords.y });
  };

  const handleResizeStart = (e: React.MouseEvent) => {
    e.stopPropagation();
    e.preventDefault();
    const startX = e.clientX;
    const startY = e.clientY;
    const startWidth = modalSize.width;
    const startHeight = modalSize.height;

    const handleMouseMove = (moveEvent: MouseEvent) => {
      const deltaX = moveEvent.clientX - startX;
      const deltaY = moveEvent.clientY - startY;
      
      const newWidth = Math.max(450, Math.min(window.innerWidth - 40, startWidth + 2 * deltaX));
      const newHeight = Math.max(400, Math.min(window.innerHeight - 40, startHeight + 2 * deltaY));
      
      setModalSize({ width: newWidth, height: newHeight });
    };

    const handleMouseUp = () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
  };

  const actualLVal = lUh && !isNaN(parseFloat(lUh)) ? parseFloat(lUh) : (calcData ? calcData.actual_l_uh : 0);
  const dutyVal = calcData ? calcData.basic.duty : (vin > 0 ? vout / vin : 0.5);
  const deltaIL = (actualLVal > 0 && calcData) ? (vout * (1.0 - dutyVal) * 1000.0) / (actualLVal * fsw) : 0;

  return (
    <div className="w-full flex flex-col gap-3">
      <div className="flex justify-between items-center bg-slate-900/60 p-2.5 rounded-xl border border-slate-800/80">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-yellow-400 animate-pulse"></span>
          <span className="text-xs font-semibold text-slate-200">Interactive Schematic Sandbox & DRC Checks (DRC Mode)</span>
        </div>
        <div className="flex gap-2 items-center">
          {saveTip && (
            <span className="text-[10px] text-emerald-400 bg-emerald-950/40 border border-emerald-500/20 px-2.5 py-0.5 rounded animate-in fade-in slide-in-from-right-1 duration-150 mr-1">
              {saveTip}
            </span>
          )}
          <Button
            onClick={handleSaveLayout}
            className="text-[11px] h-7 bg-emerald-950/40 hover:bg-emerald-900/40 text-emerald-400 border border-emerald-500/30 font-semibold flex items-center gap-1 px-3 rounded-lg transition-all cursor-pointer"
          >
            <span>Save</span> Layout
          </Button>
          <Button
            onClick={handleResetScattered}
            className="text-[11px] h-7 bg-slate-900/60 hover:bg-slate-800 text-slate-200 border border-slate-700/80 font-semibold px-3 rounded-lg transition-all cursor-pointer"
          >
            Reset Scattered
          </Button>
          <Button
            onClick={handleAutoAlign}
            className="text-[11px] h-7 bg-cyan-950/40 hover:bg-cyan-900/40 text-cyan-400 border border-cyan-500/30 font-semibold px-3 rounded-lg transition-all cursor-pointer"
          >
            Auto-Align Layout
          </Button>
        </div>
      </div>

      <div className="relative w-full border border-slate-800 rounded-xl overflow-hidden bg-slate-950/40 p-2">
        <svg
          ref={svgRef}
          width="100%"
          height="100%"
          viewBox="0 0 800 400"
          className="schematic-canvas-svg w-full h-auto block select-none"
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onClick={() => {
            setSelectedComponent(null);
            setSelectedWire(null);
          }}
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
            {Array.from({ length: 41 }).map((_, i) => (
              <line key={`v-${i}`} x1={i * 20} y1={0} x2={i * 20} y2={400} />
            ))}
            {Array.from({ length: 21 }).map((_, i) => (
              <line key={`h-${i}`} x1={0} y1={i * 20} x2={800} y2={i * 20} />
            ))}
          </g>

          {wires.map((wire, idx) => {
            const points = getWirePoints(wire);
            const isHovered = hoveredWire === idx;
            const isSelected = selectedWire === idx;
            const wireKey = `${wire.from}->${wire.to}`;
            const pathD = points.length >= 2 ? `M ${points[0][0]} ${points[0][1]} ${points.slice(1).map(p => `L ${p[0]} ${p[1]}`).join(' ')}` : '';
            
            return (
              <g 
                key={wireKey}
                onMouseEnter={() => setHoveredWire(idx)}
                onMouseLeave={() => setHoveredWire(null)}
                onClick={(e) => {
                  e.stopPropagation();
                  setSelectedWire(idx);
                  setSelectedComponent(null);
                }}
              >
                <path
                  d={pathD}
                  fill="none"
                  stroke={isSelected ? '#f43f5e' : (isHovered ? '#ef4444' : 'var(--primary-active, #3b82f6)')}
                  strokeWidth={isSelected ? 4 : (isHovered ? 3 : 2)}
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  filter={isSelected || isHovered ? 'url(#wire-glow)' : 'none'}
                  style={{ transition: 'stroke 0.2s, stroke-width 0.2s' }}
                />
                
                {points.map((p, i) => {
                  if (i === points.length - 1) return null;
                  const nextP = points[i + 1];
                  const isHorizontal = Math.abs(p[1] - nextP[1]) < 0.5;
                  return (
                    <line
                      key={`seg-${i}`}
                      x1={p[0]}
                      y1={p[1]}
                      x2={nextP[0]}
                      y2={nextP[1]}
                      stroke="transparent"
                      strokeWidth="10"
                      style={{ cursor: isHorizontal ? 'ns-resize' : 'ew-resize' }}
                      onMouseDown={(e) => handleWireSegmentMouseDown(wireKey, idx, isHorizontal, e)}
                    />
                  );
                })}

                {isHovered && points.length >= 2 && (
                  <g 
                    transform={`translate(${(points[0][0] + points[points.length-1][0]) / 2}, ${(points[0][1] + points[points.length-1][1]) / 2 - 10})`}
                    style={{ cursor: 'pointer' }}
                    onClick={(e) => {
                      e.stopPropagation();
                      setWires(prev => prev.filter((_, i) => i !== idx));
                      setHoveredWire(null);
                    }}
                  >
                    <rect x="-45" y="-12" width="90" height="16" rx="3" fill="#ef4444" opacity="0.9" />
                    <text x="0" y="0" textAnchor="middle" fill="white" fontSize="8" fontWeight="bold">Click to cut wire</text>
                  </g>
                )}
              </g>
            );
          })}

          {ratsnestLines.map((line, idx) => (
            <line
              key={`ratsnest-${idx}`}
              x1={line.fromCoords.x}
              y1={line.fromCoords.y}
              x2={line.toCoords.x}
              y2={line.toCoords.y}
              stroke="rgba(234, 179, 8, 0.45)"
              strokeWidth="1.5"
              strokeDasharray="4 4"
            />
          ))}

          {dragStartPin && tempWireEnd && (() => {
            const cA = allPinCoords.get(dragStartPin)!;
            const compA = dragStartPin.split('.')[0];
            const rotA = componentsPos[compA]?.rotation ?? 0;
            const dirA = getPinDirection(dragStartPin, rotA);
            const points = dirA === 'V'
              ? [[cA.x, cA.y], [cA.x, tempWireEnd.y], [tempWireEnd.x, tempWireEnd.y]]
              : [[cA.x, cA.y], [tempWireEnd.x, cA.y], [tempWireEnd.x, tempWireEnd.y]];
            return (
              <path
                d={`M ${points[0][0]} ${points[0][1]} L ${points[1][0]} ${points[1][1]} L ${points[2][0]} ${points[2][1]}`}
                fill="none"
                stroke={snapTargetPin ? '#10b981' : '#f59e0b'}
                strokeWidth="2.5"
                strokeDasharray="3 3"
              />
            );
          })()}

           {Object.entries(componentsPos).map(([compId, pos]) => {
             const isHovered = hoveredComponent === compId || activeDragComponent === compId;
             const isSelected = selectedComponent === compId;
             const commonProps = {
               x: pos.x,
               y: pos.y,
               rotation: pos.rotation,
               label: compId,
               highlighted: isHovered || isSelected,
               onMouseEnter: () => setHoveredComponent(compId),
               onMouseLeave: () => setHoveredComponent(null),
               onClick: (e: React.MouseEvent) => {
                 e.stopPropagation();
                 setSelectedComponent(compId);
                 setSelectedWire(null);
                 setActiveModalComponent(compId);
               }
             };

             return (
               <g 
                 key={compId}
                 onMouseDown={(e) => handleComponentMouseDown(compId, e)}
                 onClick={(e) => {
                   e.stopPropagation();
                   setSelectedComponent(compId);
                   setSelectedWire(null);
                 }}
                 className="cursor-move font-mono"
               >
                 {isSelected && (
                   <rect
                     x={pos.x - 40}
                     y={pos.y - 40}
                     width={80}
                     height={80}
                     fill="none"
                     stroke="#06b6d4"
                     strokeWidth="1.5"
                     strokeDasharray="4 3"
                     className="animate-pulse"
                     rx="8"
                   />
                 )}
                {compId === 'Vin' && (
                  <SchematicDCSource {...commonProps} pinLength={40} subLabel={`${vin.toFixed(1)} V`} />
                )}
                {compId === 'Cin' && (
                  <SchematicCapacitorPolar {...commonProps} subLabel={`${calcData ? (calcData?.basic?.c_in_uf)?.toFixed(0) ?? '-' : '-'} uF`} />
                )}
                {compId === 'Q1' && (
                  <SchematicMosfetN {...commonProps} subLabel={`${swRdsOn} mΩ`} />
                )}
                {compId === 'D1' && (
                  <SchematicDiode {...commonProps} subLabel={`${diodeVf.toFixed(1)} V`} />
                )}
                {compId === 'Lo' && (
                  <SchematicInductor {...commonProps} subLabel={`${lUh || '-'} uH`} />
                )}
                {compId === 'Co' && (
                  <SchematicCapacitorPolar {...commonProps} subLabel={`${cUf || '-'} uF`} />
                )}
                {compId === 'RL' && (
                  <SchematicResistor {...commonProps} subLabel={`${iout > 0 ? (vout/iout).toFixed(1) : '-'} Ω`} />
                )}
                {compId === 'GND' && (
                  <SchematicGround {...commonProps} />
                )}
              </g>
            );
          })}

          {Array.from(allPinCoords.entries()).map(([pinId, coords]) => {
            const isHovered = snapTargetPin === pinId || dragStartPin === pinId;
            return (
              <circle
                key={pinId}
                cx={coords.x}
                cy={coords.y}
                r={isHovered ? 7 : 5}
                fill={isHovered ? '#10b981' : 'rgba(59, 130, 246, 0.7)'}
                stroke="white"
                strokeWidth="1.5"
                className="transition-all duration-150 cursor-crosshair hover:scale-150"
                onMouseDown={(e) => handlePinMouseDown(pinId, e)}
              />
            );
          })}

          {drcViolation && (
            <g transform={`translate(${drcViolation.x}, ${drcViolation.y - 35})`} className="pointer-events-none">
              <rect
                x="-170"
                y="-45"
                width="340"
                height="55"
                rx="8"
                fill="#1e1b4b"
                stroke="#ef4444"
                strokeWidth="1.5"
                filter="drop-shadow(0 4px 12px rgba(0,0,0,0.5))"
              />
              <text x="0" y="-25" fill="#fca5a5" fontSize="10" textAnchor="middle" fontWeight="bold">
                DRC Violation
              </text>
              <text x="0" y="-8" fill="#fecaca" fontSize="8.5" textAnchor="middle">
                {drcViolation.message}
              </text>
              <polygon points="-6,10 6,10 0,16" fill="#ef4444" />
              <polygon points="-5,10 5,10 0,15" fill="#1e1b4b" />
            </g>
          )}

          {!activeDragComponent && !dragStartPin && hoveredComponent === 'Vin' && (
            <g transform="translate(60, 20)">
              <rect width="180" height="75" rx="6" fill="rgba(15, 23, 42, 0.95)" stroke="#00f2fe" strokeWidth="1.5" filter="drop-shadow(0 4px 12px rgba(0,0,0,0.5))" />
              <text x="12" y="20" fill="#ffffff" fontSize="10" fontWeight="bold">DC Input Voltage Source (Vin)</text>
              <text x="12" y="38" fill="#94a3b8" fontSize="9">Set Voltage: <tspan fill="#f1f5f9" fontWeight="bold">{vin.toFixed(1)} V</tspan></text>
              <text x="12" y="52" fill="#94a3b8" fontSize="9">Avg Current: <tspan fill="#f1f5f9" fontWeight="bold">{calcData?.losses ? (calcData.losses.p_in / vin).toFixed(2) : (iout * (vout / vin)).toFixed(2)} A</tspan></text>
              <text x="12" y="66" fill="#94a3b8" fontSize="9">Total Input Power: <tspan fill="#00f2fe" fontWeight="bold">{calcData?.losses ? (calcData?.losses?.p_in)?.toFixed(1) ?? '-' : (vin * iout * (vout / vin)).toFixed(1)} W</tspan></text>
            </g>
          )}

          {!activeDragComponent && !dragStartPin && hoveredComponent === 'Cin' && (
            <g transform="translate(160, 20)">
              <rect width="180" height="90" rx="6" fill="rgba(15, 23, 42, 0.95)" stroke="#00f2fe" strokeWidth="1.5" filter="drop-shadow(0 4px 12px rgba(0,0,0,0.5))" />
              <text x="12" y="20" fill="#ffffff" fontSize="10" fontWeight="bold">Input Filter Cap (Cin)</text>
              <text x="12" y="38" fill="#94a3b8" fontSize="9">Min Required Cap: <tspan fill="#f1f5f9" fontWeight="bold">{calcData ? (calcData?.basic?.c_in_uf)?.toFixed(1) ?? '-' : '-'} μF</tspan></text>
              <text x="12" y="52" fill="#94a3b8" fontSize="9">Actual Set Cap: <tspan fill="#f1f5f9" fontWeight="bold">{cinUf && !isNaN(parseFloat(cinUf)) ? parseFloat(cinUf).toFixed(1) : (calcData ? (calcData?.basic?.c_in_uf)?.toFixed(1) ?? '-' : '-')} μF</tspan></text>
              <text x="12" y="66" fill="#94a3b8" fontSize="9">Ripple Limit: <tspan fill="#f1f5f9" fontWeight="bold">1% ({(0.01*vin).toFixed(2)}V)</tspan></text>
              <text x="12" y="80" fill="#94a3b8" fontSize="9">Cap RMS Current: <tspan fill="#00f2fe" fontWeight="bold">{calcData ? (calcData?.basic?.cin_rms_a)?.toFixed(2) ?? '-' : '-'} A</tspan></text>
            </g>
          )}

          {!activeDragComponent && !dragStartPin && hoveredComponent === 'Q1' && (
            <g transform="translate(260, 20)">
              <rect width="190" height="95" rx="6" fill="rgba(15, 23, 42, 0.95)" stroke="#3b82f6" strokeWidth="1.5" filter="drop-shadow(0 4px 12px rgba(0,0,0,0.5))" />
              <text x="12" y="20" fill="#ffffff" fontSize="10" fontWeight="bold">Main Switching MOSFET (Q1)</text>
              <text x="12" y="38" fill="#94a3b8" fontSize="9">Vds Voltage: <tspan fill="#f1f5f9" fontWeight="bold">{vin.toFixed(1)} V</tspan></text>
              <text x="12" y="52" fill="#94a3b8" fontSize="9">RMS Current Id: <tspan fill="#f1f5f9" fontWeight="bold">{calcData?.stresses?.sw_i_rms?.toFixed(2)} A</tspan></text>
              <text x="12" y="66" fill="#94a3b8" fontSize="9">Rds(on): <tspan fill="#3b82f6" fontWeight="bold">{swRdsOn} mΩ</tspan></text>
              <text x="12" y="80" fill="#94a3b8" fontSize="9">Total Loss: <tspan fill="#f59e0b" fontWeight="bold">{calcData?.losses ? (calcData.losses.p_sw_cond + calcData.losses.p_sw_sw).toFixed(2) : '-'} W</tspan></text>
            </g>
          )}

          {!activeDragComponent && !dragStartPin && hoveredComponent === 'D1' && (
            <g transform="translate(390, 20)">
              <rect width="190" height="80" rx="6" fill="rgba(15, 23, 42, 0.95)" stroke="#ef4444" strokeWidth="1.5" filter="drop-shadow(0 4px 12px rgba(0,0,0,0.5))" />
              <text x="12" y="20" fill="#ffffff" fontSize="10" fontWeight="bold">Freewheeling Diode (D1)</text>
              <text x="12" y="38" fill="#94a3b8" fontSize="9">Reverse Voltage Vr: <tspan fill="#f1f5f9" fontWeight="bold">{vin.toFixed(1)} V</tspan></text>
              <text x="12" y="52" fill="#94a3b8" fontSize="9">Average Current Iavg: <tspan fill="#f1f5f9" fontWeight="bold">{calcData?.stresses?.diode_i_avg?.toFixed(2)} A</tspan></text>
              <text x="12" y="66" fill="#94a3b8" fontSize="9">Conduction Loss: <tspan fill="#f59e0b" fontWeight="bold">{calcData?.losses ? (calcData?.losses?.p_diode_cond)?.toFixed(2) ?? '-' : '-'} W</tspan></text>
            </g>
          )}

          {!activeDragComponent && !dragStartPin && hoveredComponent === 'Lo' && (
            <g transform="translate(430, 20)">
              <rect width="190" height="95" rx="6" fill="rgba(15, 23, 42, 0.95)" stroke="#10b981" strokeWidth="1.5" filter="drop-shadow(0 4px 12px rgba(0,0,0,0.5))" />
              <text x="12" y="20" fill="#ffffff" fontSize="10" fontWeight="bold">Power Inductor (Lo)</text>
              <text x="12" y="38" fill="#94a3b8" fontSize="9">Set Inductance: <tspan fill="#f1f5f9" fontWeight="bold">{actualLVal.toFixed(2)} μH</tspan></text>
              <text x="12" y="52" fill="#94a3b8" fontSize="9">Peak Current Ipeak: <tspan fill="#f1f5f9" fontWeight="bold">{(iout + deltaIL / 2.0).toFixed(2)} A</tspan></text>
              <text x="12" y="66" fill="#94a3b8" fontSize="9">Copper Loss: <tspan fill="#10b981" fontWeight="bold">{calcData?.losses ? (calcData?.losses?.p_ind_copper)?.toFixed(2) ?? '-' : '-'} W</tspan></text>
              <text x="12" y="80" fill="#94a3b8" fontSize="9">Core Loss: <tspan fill="#059669" fontWeight="bold">{calcData?.losses ? (calcData?.losses?.p_ind_core)?.toFixed(2) ?? '-' : '-'} W</tspan></text>
            </g>
          )}

          {!activeDragComponent && !dragStartPin && hoveredComponent === 'Co' && (
            <g transform="translate(480, 20)">
              <rect width="180" height="80" rx="6" fill="rgba(15, 23, 42, 0.95)" stroke="#10b981" strokeWidth="1.5" filter="drop-shadow(0 4px 12px rgba(0,0,0,0.5))" />
              <text x="12" y="20" fill="#ffffff" fontSize="10" fontWeight="bold">Output Filter Cap (Co)</text>
              <text x="12" y="38" fill="#94a3b8" fontSize="9">Actual Set Cap: <tspan fill="#f1f5f9" fontWeight="bold">{cUf && !isNaN(parseFloat(cUf)) ? parseFloat(cUf).toFixed(2) : (calcData ? (calcData?.actual_c_uf)?.toFixed(2) ?? '-' : '-')} μF</tspan></text>
              <text x="12" y="52" fill="#94a3b8" fontSize="9">RMS Ripple Current: <tspan fill="#f1f5f9" fontWeight="bold">{calcData ? (calcData?.basic?.cout_rms_a)?.toFixed(2) ?? '-' : '-'} A</tspan></text>
              <text x="12" y="66" fill="#94a3b8" fontSize="9">ESR Loss: <tspan fill="#f59e0b" fontWeight="bold">{calcData?.losses ? (calcData?.losses?.p_cap_esr)?.toFixed(2) ?? '-' : '-'} W</tspan></text>
            </g>
          )}

          {!activeDragComponent && !dragStartPin && hoveredComponent === 'RL' && (
            <g transform="translate(590, 20)">
              <rect width="180" height="75" rx="6" fill="rgba(15, 23, 42, 0.95)" stroke="#3b82f6" strokeWidth="1.5" filter="drop-shadow(0 4px 12px rgba(0,0,0,0.5))" />
              <text x="12" y="20" fill="#ffffff" fontSize="10" fontWeight="bold">Rated Load Resistance (RL)</text>
              <text x="12" y="38" fill="#94a3b8" fontSize="9">Equivalent Load: <tspan fill="#f1f5f9" fontWeight="bold">{iout > 0 ? (vout/iout).toFixed(2) : '-'} Ω</tspan></text>
              <text x="12" y="52" fill="#94a3b8" fontSize="9">Output Voltage: <tspan fill="#f1f5f9" fontWeight="bold">{vout.toFixed(1)} V</tspan></text>
              <text x="12" y="66" fill="#94a3b8" fontSize="9">Rated Power: <tspan fill="#3b82f6" fontWeight="bold">{(vout * iout).toFixed(1)} W</tspan></text>
            </g>
          )}
        </svg>
      </div>

      {activeModalComponent && (
        <div 
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md transition-all duration-200 animate-in fade-in"
          onClick={() => setActiveModalComponent(null)}
        >
          <div 
            style={{ width: modalSize.width, height: modalSize.height, maxWidth: '95vw', maxHeight: '95vh' }}
            className="relative bg-slate-950/85 backdrop-blur-xl border border-cyan-500/30 rounded-2xl p-6 text-white shadow-[0_0_30px_rgba(6,182,212,0.15)] flex flex-col gap-4 overflow-hidden animate-in zoom-in-95 duration-200"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between border-b border-slate-800 pb-3 shrink-0">
              <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-pulse"></span>
                {getModalTitle(activeModalComponent)}
              </h3>
              <button
                onClick={() => setActiveModalComponent(null)}
                className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-400 hover:text-white transition-colors"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            
            <div className="flex-1 overflow-y-auto pr-1.5 scrollbar-thin">
              <ComponentDesignDetails
                compId={activeModalComponent}
                vin={vin}
                setVin={setVin}
                vout={vout}
                setVout={setVout}
                iout={iout}
                setIout={setIout}
                fsw={fsw}
                setFsw={setFsw}
                lir={lir}
                setLir={setLir}
                vrip={vrip}
                setVrip={setVrip}
                lUh={lUh}
                setLUh={setLUh}
                cUf={cUf}
                setCUf={setCUf}
                esr={esr}
                setEsr={setEsr}
                cinUf={cinUf}
                setCinUf={setCinUf}
                cinEsr={cinEsr}
                setCinEsr={setCinEsr}
                swRdsOn={swRdsOn}
                setSwRdsOn={setSwRdsOn}
                swTimes={swTimes}
                setSwTimes={setSwTimes}
                diodeVf={diodeVf}
                setDiodeVf={setDiodeVf}
                indDcr={indDcr}
                setIndDcr={setIndDcr}
                calcData={calcData}
                defaultExpandFormula={true}
                diodeType={diodeType}
                setDiodeType={setDiodeType}
                diodeQrr={diodeQrr}
                setDiodeQrr={setDiodeQrr}
                syncRdsOn={syncRdsOn}
                setSyncRdsOn={setSyncRdsOn}
                syncDeadTime={syncDeadTime}
                setSyncDeadTime={setSyncDeadTime}
                syncBodyVf={syncBodyVf}
                setSyncBodyVf={setSyncBodyVf}
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
  compId?: string;
  partKey?: string;
  vin: number;
  setVin: (v: number) => void;
  vout: number;
  setVout: (v: number) => void;
  iout: number;
  setIout: (v: number) => void;
  fsw: number;
  setFsw: (v: number) => void;
  lir: number;
  setLir: (v: number) => void;
  vrip: number;
  setVrip: (v: number) => void;
  lUh: string;
  setLUh: (v: string) => void;
  cUf: string;
  setCUf: (v: string) => void;
  esr: number;
  setEsr: (v: number) => void;
  cinUf: string;
  setCinUf: (v: string) => void;
  cinEsr: number;
  setCinEsr: (v: number) => void;
  swRdsOn: number;
  setSwRdsOn: (v: number) => void;
  swTimes: number;
  setSwTimes: (v: number) => void;
  diodeVf: number;
  setDiodeVf: (v: number) => void;
  indDcr: number;
  setIndDcr: (v: number) => void;
  calcData: any;
  defaultExpandFormula?: boolean;
  diodeType?: string;
  setDiodeType?: (v: string) => void;
  diodeQrr?: number;
  setDiodeQrr?: (v: number) => void;
  syncRdsOn?: number;
  setSyncRdsOn?: (v: number) => void;
  syncDeadTime?: number;
  setSyncDeadTime?: (v: number) => void;
  syncBodyVf?: number;
  setSyncBodyVf?: (v: number) => void;
}

export function ComponentDesignDetails({
  compId,
  partKey,
  vin, setVin,
  vout, setVout,
  iout, setIout,
  fsw,
  lUh, setLUh,
  cUf, setCUf,
  esr, setEsr,
  cinUf, setCinUf,
  cinEsr, setCinEsr,
  swRdsOn, setSwRdsOn,
  swTimes, setSwTimes,
  diodeVf, setDiodeVf,
  indDcr, setIndDcr,
  calcData,
  defaultExpandFormula = false,
  diodeType = 'schottky',
  setDiodeType,
  diodeQrr = 0,
  setDiodeQrr,
  syncRdsOn = 10,
  setSyncRdsOn,
  syncDeadTime = 50,
  setSyncDeadTime,
  syncBodyVf = 0.8,
  setSyncBodyVf
}: ComponentDesignDetailsProps) {
  const [expandFormula, setExpandFormula] = useState(defaultExpandFormula);
  const [expandDerivation, setExpandDerivation] = useState(false);

  const renderFormulaToggle = () => (
    <button
      onClick={(e) => {
        e.stopPropagation();
        setExpandFormula(!expandFormula);
      }}
      className="text-[10px] text-cyan-400 hover:text-cyan-300 bg-cyan-950/40 hover:bg-cyan-900/40 border border-cyan-800/50 px-2 py-0.5 rounded transition-all flex items-center gap-1 font-semibold ml-auto shrink-0 select-none cursor-pointer"
    >
      <span>📘</span> {expandFormula ? 'Hide Equations' : 'Show Equations'}
    </button>
  );

  const renderDerivationToggle = (title: string = "Detailed Mathematical & Volt-Second Derivations") => (
    <div className="mt-2.5 pt-2.5 border-t border-slate-900/60">
      <button
        type="button"
        onClick={(e) => {
          e.stopPropagation();
          setExpandDerivation(!expandDerivation);
        }}
        className="text-[10px] text-cyan-400 hover:text-cyan-300 font-semibold flex items-center gap-1 cursor-pointer select-none"
      >
        <span>{expandDerivation ? '▼' : '▶'}</span>
        <span>{expandDerivation ? `Collapse ${title}` : `Expand ${title}`}</span>
      </button>
    </div>
  );

  const actualLVal = lUh && !isNaN(parseFloat(lUh)) ? parseFloat(lUh) : (calcData ? calcData.actual_l_uh : 0);
  const dutyVal = calcData ? calcData.basic.duty : (vin > 0 ? vout / vin : 0.5);
  const deltaIL = (actualLVal > 0 && calcData) ? (vout * (1.0 - dutyVal) * 1000.0) / (actualLVal * fsw) : 0;
  const ilRms = Math.sqrt(Math.pow(iout, 2) + Math.pow(deltaIL, 2) / 12);

  const activeKey = partKey || compId;

  switch (activeKey) {
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
                The DC input voltage source Vin supplies main power to the Buck topology. Average input power equation:
              </div>
              <Latex math="P_{in} = V_{in} \cdot I_{in} = \frac{V_{out} \cdot I_{out}}{\eta}" block />
              
              {renderDerivationToggle("Conservation of Energy Derivation")}
              {expandDerivation && (
                <div className="mt-2 p-2.5 bg-slate-950/60 rounded border border-slate-900/60 text-slate-400 text-[10px] leading-relaxed space-y-1">
                  <div>Under lossless conditions, input power equals output power:</div>
                  <Latex math="P_{in} = P_{out} = V_{out} \cdot I_{out}" block />
                  <div>Accounting for efficiency <Latex math="\eta" /> to cover internal losses:</div>
                  <Latex math="P_{in} = \frac{P_{out}}{\eta} \implies V_{in} \cdot I_{in} = \frac{V_{out} \cdot I_{out}}{\eta}" block />
                </div>
              )}
            </div>
          )}
          
          <div className="p-3 bg-slate-950/40 rounded-lg border border-slate-800 space-y-1 text-xs">
            <span className="text-[11px] font-semibold text-cyan-400 block mb-1">Stress & Operating Data</span>
            <div className="flex justify-between py-1 border-b border-slate-900">
              <span className="text-slate-400">Input Voltage Vin</span>
              <span className="font-mono text-slate-200"><span className="text-emerald-400 font-mono">{vin.toFixed(1)}</span> V</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-900 font-mono">
              <span className="text-slate-400 font-mono">Average Input Current Iin</span>
              <span className="font-mono text-slate-200">
                {calcData?.losses ? (calcData.losses.p_in / vin).toFixed(2) : (iout * (vout / vin)).toFixed(2)} A
              </span>
            </div>
            <div className="flex justify-between py-1 font-mono">
              <span className="text-slate-400 font-mono">Total Input Power Pin</span>
              <span className="font-mono text-slate-200">
                {calcData?.losses ? (calcData?.losses?.p_in)?.toFixed(1) ?? '-' : (vin * iout * (vout / vin)).toFixed(1)} W
              </span>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="flex flex-col gap-1.5 col-span-2">
              <label className="text-[11px] text-slate-400 font-semibold">Adjust Vin (V)</label>
              <input className="flex h-8 w-full rounded-md border border-slate-850 bg-[#020617] px-3 py-1 text-xs outline-none focus:border-cyan-500 transition-colors font-mono text-cyan-400" type="number" value={vin} onChange={(e) => setVin(parseFloat(e.target.value) || 0)} />
            </div>
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
                The input capacitor provides pulsed current during switch on-time. RMS ripple current is:
              </div>
              <Latex math="I_{Cin,rms} = I_{out} \cdot \sqrt{D \cdot (1 - D)}" block />
              
              {renderDerivationToggle("RMS Ripple Current Derivation")}
              {expandDerivation && (
                <div className="mt-2 p-2.5 bg-slate-950/60 rounded border border-slate-900/60 text-slate-400 text-[10px] leading-relaxed space-y-2.5">
                  <div>Integrating squared capacitor current over one period:</div>
                  <Latex math="I_{Cin,rms} = \sqrt{\frac{1}{T_{sw}} \int_0^{T_{sw}} i_{Cin}^2(t) dt}" block />
                  <div>During <Latex math="D \cdot T_{sw}" />, switch is on and capacitor discharges. During off-time, capacitor charges from source.</div>
                  <Latex math="i_{Cin}(t) = \begin{cases} I_{out} - I_{in}, & 0 < t \le D T_{sw} \\ -I_{in}, & D T_{sw} < t \le T_{sw} \end{cases}" block />
                  <div>Substituting <Latex math="I_{in} = D \cdot I_{out}" /> gives:</div>
                  <Latex math="I_{Cin,rms} = I_{out} \sqrt{D \cdot (1 - D)}" block />
                  <div>Peak RMS occurs at <Latex math="D = 0.5" /> where <Latex math="I_{Cin,rms} = 0.5 I_{out}" />.</div>
                </div>
              )}
            </div>
          )}
          
          <div className="p-3 bg-slate-950/40 rounded-lg border border-slate-800 space-y-1 text-xs">
            <span className="text-[11px] font-semibold text-cyan-400 block mb-1">Stress & Operating Data</span>
            <div className="flex justify-between py-1 border-b border-slate-900">
              <span className="text-slate-400">Min Required Capacitance Cin,min</span>
              <span className="font-mono text-slate-200">{calcData ? (calcData?.basic?.c_in_uf)?.toFixed(1) ?? '-' : '-'} μF</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-900">
              <span className="text-slate-400">Set Capacitance Cin</span>
              <span className="font-mono text-slate-200">{cinUf && !isNaN(parseFloat(cinUf)) ? parseFloat(cinUf).toFixed(2) : '-'} μF</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-900">
              <span className="text-slate-400">Capacitor RMS Current</span>
              <span className="font-mono text-slate-200">{calcData ? (calcData?.basic?.cin_rms_a)?.toFixed(2) ?? '-' : '-'} A</span>
            </div>
            <div className="flex justify-between py-1 font-mono">
              <span className="text-slate-400 font-mono">ESR Power Loss</span>
              <span className="font-mono text-slate-200">
                {calcData ? (Math.pow(calcData.basic.cin_rms_a, 2) * (cinEsr / 1000)).toFixed(3) : '-'} W
              </span>
            </div>
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div className="flex flex-col gap-1.5">
              <label className="text-[11px] text-slate-400 font-semibold">Adjust Cin (μF)</label>
              <input className="flex h-8 w-full rounded-md border border-slate-850 bg-[#020617] px-3 py-1 text-xs outline-none focus:border-cyan-500 transition-colors font-mono text-cyan-400" type="text" value={cinUf} onChange={(e) => setCinUf(e.target.value)} />
            </div>
            <div className="flex flex-col gap-1.5">
              <label className="text-[11px] text-slate-400 font-semibold">Adjust ESR (mΩ)</label>
              <input className="flex h-8 w-full rounded-md border border-slate-850 bg-[#020617] px-3 py-1 text-xs outline-none focus:border-cyan-500 transition-colors font-mono text-cyan-400" type="number" value={cinEsr} onChange={(e) => setCinEsr(parseFloat(e.target.value) || 0)} />
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
                High-side MOSFET total dissipation consists of conduction and switching losses:
              </div>
              <Latex math="P_{cond} = I_{Q,rms}^2 \cdot R_{ds(on)}" block />
              <Latex math="P_{sw} = \frac{1}{2} V_{in} \cdot I_{out} \cdot (t_{on} + t_{off}) \cdot f_{sw}" block />
              
              {renderDerivationToggle("MOSFET Dissipation Derivations")}
              {expandDerivation && (
                <div className="mt-2 p-2.5 bg-slate-950/60 rounded border border-slate-900/60 text-slate-400 text-[10px] leading-relaxed space-y-2">
                  <div>1. Conduction loss across channel resistance:</div>
                  <Latex math="P_{cond} = I_{Q,rms}^2 \cdot R_{ds(on)} = I_{out}^2 \cdot D \cdot R_{ds(on)}" block />
                  <div>2. Switching overlap loss model:</div>
                  <Latex math="P_{sw} = \frac{1}{2} V_{in} \cdot I_{out} \cdot (t_{on} + t_{off}) \cdot f_{sw}" block />
                </div>
              )}
            </div>
          )}
          
          <div className="p-3 bg-slate-950/40 rounded-lg border border-slate-800 space-y-1 text-xs">
            <span className="text-[11px] font-semibold text-cyan-400 block mb-1">Stress & Operating Data</span>
            <div className="flex justify-between py-1 border-b border-slate-900">
              <span className="text-slate-400">Drain-Source Voltage Vds</span>
              <span className="font-mono text-slate-200">{calcData ? (calcData?.stresses?.sw_v)?.toFixed(1) ?? '-' : '-'} V</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-900">
              <span className="text-slate-400">RMS Switch Current Id,rms</span>
              <span className="font-mono text-slate-200">{calcData ? (calcData?.stresses?.sw_i_rms)?.toFixed(2) ?? '-' : '-'} A</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-900">
              <span className="text-slate-400">Conduction Loss P_cond</span>
              <span className="font-mono text-amber-400">{calcData?.losses?.p_sw_cond?.toFixed(2) ?? '-'} W</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-900">
              <span className="text-slate-400">Switching Loss P_sw</span>
              <span className="font-mono text-amber-400">{calcData?.losses?.p_sw_sw?.toFixed(2) ?? '-'} W</span>
            </div>
            <div className="flex justify-between py-1 text-cyan-300 font-semibold">
              <span className="font-mono">Total Power Dissipation P_loss</span>
              <span className="font-mono">
                {calcData?.losses ? (calcData.losses.p_sw_cond + calcData.losses.p_sw_sw).toFixed(2) : '-'} W
              </span>
            </div>
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div className="flex flex-col gap-1.5">
              <label className="text-[11px] text-slate-400 font-semibold">Adjust Rds(on) (mΩ)</label>
              <input className="flex h-8 w-full rounded-md border border-slate-850 bg-[#020617] px-3 py-1 text-xs outline-none focus:border-cyan-500 transition-colors font-mono text-cyan-400" type="number" value={swRdsOn} onChange={(e) => setSwRdsOn(parseFloat(e.target.value) || 0)} />
            </div>
            <div className="flex flex-col gap-1.5">
              <label className="text-[11px] text-slate-400 font-semibold">Adjust Switching Time ton+toff (ns)</label>
              <input className="flex h-8 w-full rounded-md border border-slate-850 bg-[#020617] px-3 py-1 text-xs outline-none focus:border-cyan-500 transition-colors font-mono text-cyan-400" type="number" value={swTimes} onChange={(e) => setSwTimes(parseFloat(e.target.value) || 0)} />
            </div>
          </div>
        </div>
      );
      
    case 'D1':
      const isSync = diodeType === 'sync';
      const isFast = diodeType === 'fast_recovery';
      const totalDiodeLoss = calcData?.losses?.p_diode_cond ?? 0;
      const rrLoss = calcData?.losses?.p_diode_rr ?? 0;
      const dtLoss = calcData?.losses?.p_diode_dt ?? 0;
      const condLoss = totalDiodeLoss - rrLoss - dtLoss;

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
                The freewheeling path conducts when Q1 turns off. Supported device loss formulations:
              </div>
              <div className="text-[11px] text-slate-400 leading-relaxed space-y-1 pl-2 border-l-2 border-slate-700">
                <div>• <b>Schottky Diode</b>: <Latex math="P_{loss} = I_{diode,avg} \cdot V_f" /></div>
                <div>• <b>Fast Recovery Diode</b>: <Latex math="P_{loss} = I_{diode,avg} \cdot V_f + Q_{rr} \cdot V_{in} \cdot f_{sw}" /></div>
                <div>• <b>Synchronous MOSFET</b>: <Latex math="P_{loss} = I_{sync,rms}^2 \cdot R_{ds(on),sync} + 2 \cdot I_{out} \cdot V_{f,body} \cdot t_{dead} \cdot f_{sw}" /></div>
              </div>
              
              {renderDerivationToggle("Freewheeling Path Dissipation Derivations")}
              {expandDerivation && (
                <div className="mt-2 p-2.5 bg-slate-950/60 rounded border border-slate-900/60 text-slate-400 text-[10px] leading-relaxed space-y-2">
                  <div>Average current is <Latex math="I_{avg} = I_{out}(1-D)" /> and RMS current is <Latex math="I_{rms} = I_{out}\sqrt{1-D}" />.</div>
                  <div>1. <b>Standard Diode</b>: Combines forward drop conduction loss and reverse recovery switching loss.</div>
                  <div>2. <b>Synchronous MOSFET</b>: Channel conducts through low <Latex math="R_{ds(on)}" />, with body diode conduction across the dead-time interval: <Latex math="P_{body} = 2 \cdot I_{out} \cdot V_{f,body} \cdot t_{dead} \cdot f_{sw}" />.</div>
                </div>
              )}
            </div>
          )}
          
          <div className="p-3 bg-slate-950/40 rounded-lg border border-slate-800 space-y-1 text-xs">
            <span className="text-[11px] font-semibold text-cyan-400 block mb-1">Stress & Operating Data</span>
            <div className="flex justify-between py-1 border-b border-slate-900">
              <span className="text-slate-400">Reverse Voltage Stress Vr</span>
              <span className="font-mono text-slate-200">{calcData ? (calcData?.stresses?.diode_v)?.toFixed(1) ?? '-' : '-'} V</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-900">
              <span className="text-slate-400">Average Forward Current Iavg</span>
              <span className="font-mono text-slate-200">{calcData ? (calcData?.stresses?.diode_i_avg)?.toFixed(2) ?? '-' : '-'} A</span>
            </div>
            {isSync ? (
              <>
                <div className="flex justify-between py-1 border-b border-slate-900 text-slate-400">
                  <span>Channel Conduction Loss P_cond</span>
                  <span className="font-mono text-slate-200"><span className="text-emerald-400 font-mono">{condLoss.toFixed(2)}</span> W</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-900 text-slate-400">
                  <span>Dead-Time Body Diode Loss P_deadtime</span>
                  <span className="font-mono text-slate-200"><span className="text-emerald-400 font-mono">{dtLoss.toFixed(2)}</span> W</span>
                </div>
              </>
            ) : (
              <>
                <div className="flex justify-between py-1 border-b border-slate-900 text-slate-400">
                  <span>Forward Conduction Loss P_cond</span>
                  <span className="font-mono text-slate-200"><span className="text-emerald-400 font-mono">{condLoss.toFixed(2)}</span> W</span>
                </div>
                {isFast && (
                  <div className="flex justify-between py-1 border-b border-slate-900 text-slate-400">
                    <span>Reverse Recovery Loss P_rr</span>
                    <span className="font-mono text-slate-200"><span className="text-emerald-400 font-mono">{rrLoss.toFixed(2)}</span> W</span>
                  </div>
                )}
              </>
            )}
            <div className="flex justify-between py-1 text-cyan-300 font-semibold">
              <span>Total Dissipation P_loss</span>
              <span className="font-mono"><span className="text-emerald-400 font-mono">{totalDiodeLoss.toFixed(2)}</span> W</span>
            </div>
          </div>
          
          <div className="space-y-3">
            <div className="flex flex-col gap-1.5">
              <label className="text-[11px] text-slate-400 font-semibold">Select Rectifier Model</label>
              <select className="bg-slate-900 border border-slate-850 rounded px-2.5 py-1 text-xs outline-none focus:border-cyan-500 transition-colors font-mono text-cyan-400" value={diodeType} onChange={(e) => setDiodeType?.(e.target.value)}>
                <option value="schottky">Schottky Diode</option>
                <option value="fast_recovery">Fast Recovery Diode</option>
                <option value="sync">Synchronous MOSFET</option>
              </select>
            </div>

            {diodeType === 'sync' ? (
              <div className="grid grid-cols-2 gap-3">
                <div className="flex flex-col gap-1.5">
                  <label className="text-[11px] text-slate-400 font-semibold">Channel Rds(on) (mΩ)</label>
                  <input className="flex h-8 w-full rounded-md border border-slate-850 bg-[#020617] px-3 py-1 text-xs outline-none focus:border-cyan-500 transition-colors font-mono text-cyan-400" type="number" value={syncRdsOn} onChange={(e) => setSyncRdsOn?.(parseFloat(e.target.value) || 0)} />
                </div>
                <div className="flex flex-col gap-1.5">
                  <label className="text-[11px] text-slate-400 font-semibold">Dead-Time (ns)</label>
                  <input className="flex h-8 w-full rounded-md border border-slate-850 bg-[#020617] px-3 py-1 text-xs outline-none focus:border-cyan-500 transition-colors font-mono text-cyan-400" type="number" value={syncDeadTime} onChange={(e) => setSyncDeadTime?.(parseFloat(e.target.value) || 0)} />
                </div>
                <div className="flex flex-col gap-1.5 col-span-2">
                  <label className="text-[11px] text-slate-400 font-semibold">Body Diode Forward Drop Vf_body (V)</label>
                  <input className="flex h-8 w-full rounded-md border border-slate-850 bg-[#020617] px-3 py-1 text-xs outline-none focus:border-cyan-500 transition-colors font-mono text-cyan-400" type="number" step="0.1" value={syncBodyVf} onChange={(e) => setSyncBodyVf?.(parseFloat(e.target.value) || 0)} />
                </div>
              </div>
            ) : (
              <div className="grid grid-cols-2 gap-3">
                <div className="flex flex-col gap-1.5 col-span-2">
                  <label className="text-[11px] text-slate-400 font-semibold">Forward Voltage Vf (V)</label>
                  <input className="flex h-8 w-full rounded-md border border-slate-850 bg-[#020617] px-3 py-1 text-xs outline-none focus:border-cyan-500 transition-colors font-mono text-cyan-400" type="number" step="0.1" value={diodeVf} onChange={(e) => setDiodeVf(parseFloat(e.target.value) || 0)} />
                </div>
                {diodeType === 'fast_recovery' && (
                  <div className="flex flex-col gap-1.5 col-span-2">
                    <label className="text-[11px] text-slate-400 font-semibold">Reverse Recovery Qrr (nC)</label>
                    <input className="flex h-8 w-full rounded-md border border-slate-850 bg-[#020617] px-3 py-1 text-xs outline-none focus:border-cyan-500 transition-colors font-mono text-cyan-400" type="number" value={diodeQrr} onChange={(e) => setDiodeQrr?.(parseFloat(e.target.value) || 0)} />
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      );
      
    case 'Lo':
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
                The filter inductor operates on volt-second balance to deliver continuous current:
              </div>
              <Latex math="\Delta I_L = \frac{V_{out} \cdot (1 - D)}{L_{design} \cdot f_{sw}}" block />
              <Latex math="P_{copper} = I_{L,rms}^2 \cdot DCR" block />
              
              {renderDerivationToggle("Volt-Second Balance & Inductor Derivation")}
              {expandDerivation && (
                <div className="mt-2 p-2.5 bg-slate-950/60 rounded border border-slate-900/60 text-slate-400 text-[10px] leading-relaxed space-y-2.5">
                  <div>1. Volt-second balance requires zero net inductor voltage per switching period:</div>
                  <Latex math="\int_0^{T_{sw}} v_L(t) dt = 0" block />
                  <div>During on-time: <Latex math="v_L = V_{in} - V_{out}" />. During off-time: <Latex math="v_L = -V_{out}" />.</div>
                  <Latex math="(V_{in} - V_{out}) D T_{sw} + (-V_{out})(1-D) T_{sw} = 0 \implies D = \frac{V_{out}}{V_{in}}" block />
                  <div>2. Peak-to-peak inductor ripple current:</div>
                  <Latex math="\Delta I_L = \frac{V_{out} \cdot (1 - D)}{L \cdot f_{sw}}" block />
                  <div>3. Critical inductance for continuous conduction mode (CCM):</div>
                  <Latex math="L_{crit} = \frac{V_{out}(1-D)}{2 I_{out} f_{sw}}" block />
                </div>
              )}
            </div>
          )}
          
          <div className="p-3 bg-slate-950/40 rounded-lg border border-slate-800 space-y-1 text-xs">
            <span className="text-[11px] font-semibold text-cyan-400 block mb-1">Stress & Operating Data</span>
            <div className="flex justify-between py-1 border-b border-slate-900">
              <span className="text-slate-400">Set Inductance Lo</span>
              <span className="font-mono text-slate-200">{lUh && !isNaN(parseFloat(lUh)) ? parseFloat(lUh).toFixed(2) : '-'} μH</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-900">
              <span className="text-slate-400">Ripple Current Peak-to-Peak ΔI_L</span>
              <span className="font-mono text-slate-200"><span className="text-emerald-400 font-mono">{deltaIL.toFixed(2)}</span> A</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-900">
              <span className="text-slate-400">RMS Inductor Current Il,rms</span>
              <span className="font-mono text-slate-200"><span className="text-emerald-400 font-mono">{ilRms.toFixed(2)}</span> A</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-900">
              <span className="text-slate-400">Peak Inductor Current I_peak</span>
              <span className="font-mono text-slate-200">{calcData ? (iout + deltaIL / 2.0).toFixed(2) : '-'} A</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-900">
              <span className="text-slate-400">DCR Copper Loss</span>
              <span className="font-mono text-amber-400">{calcData?.losses?.p_ind_copper?.toFixed(2) ?? '-'} W</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-900">
              <span className="text-slate-400">Core Loss</span>
              <span className="font-mono text-amber-400">{calcData?.losses?.p_ind_core?.toFixed(2) ?? '-'} W</span>
            </div>
            <div className="flex justify-between py-1 text-cyan-300 font-semibold">
              <span className="font-mono">Total Inductor Dissipation P_loss</span>
              <span className="font-mono">
                {calcData?.losses ? (calcData.losses.p_ind_copper + calcData.losses.p_ind_core).toFixed(2) : '-'} W
              </span>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="flex flex-col gap-1.5">
              <label className="text-[11px] text-slate-400 font-semibold">Actual Inductance Lo (μH)</label>
              <input className="flex h-8 w-full rounded-md border border-slate-850 bg-[#020617] px-3 py-1 text-xs outline-none focus:border-cyan-500 transition-colors font-mono text-cyan-400" type="text" value={lUh} onChange={(e) => setLUh(e.target.value)} />
            </div>
            <div className="flex flex-col gap-1.5">
              <label className="text-[11px] text-slate-400 font-semibold">DCR Resistance (mΩ)</label>
              <input className="flex h-8 w-full rounded-md border border-slate-850 bg-[#020617] px-3 py-1 text-xs outline-none focus:border-cyan-500 transition-colors font-mono text-cyan-400" type="number" value={indDcr} onChange={(e) => setIndDcr(parseFloat(e.target.value) || 0)} />
            </div>
          </div>
        </div>
      );
      
    case 'Co':
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
                Output capacitor ripple voltage combination of capacitive charge and resistive ESR:
              </div>
              <Latex math="\Delta V_{out} = \frac{\Delta I_L}{8 \cdot f_{sw} \cdot C} + \Delta I_L \cdot ESR" block />
              
              {renderDerivationToggle("Output Ripple Voltage Derivation")}
              {expandDerivation && (
                <div className="mt-2 p-2.5 bg-slate-950/60 rounded border border-slate-900/60 text-slate-400 text-[10px] leading-relaxed space-y-2.5">
                  <div>1. Capacitive ripple: Integrating ripple charge over half a cycle:</div>
                  <Latex math="\Delta Q = \frac{1}{2} \left(\frac{T_{sw}}{2}\right) \left(\frac{\Delta I_L}{2}\right) = \frac{\Delta I_L}{8 f_{sw}}" block />
                  <Latex math="\Delta V_C = \frac{\Delta Q}{C} = \frac{\Delta I_L}{8 f_{sw} C}" block />
                  <div>2. Resistive ESR drop:</div>
                  <Latex math="\Delta V_{ESR} = \Delta I_L \cdot ESR" block />
                  <div>3. Worst-case peak-to-peak superposition:</div>
                  <Latex math="\Delta V_{out} = \frac{\Delta I_L}{8 f_{sw} C} + \Delta I_L \cdot ESR" block />
                </div>
              )}
            </div>
          )}
          
          <div className="p-3 bg-slate-950/40 rounded-lg border border-slate-800 space-y-1 text-xs">
            <span className="text-[11px] font-semibold text-cyan-400 block mb-1">Stress & Operating Data</span>
            <div className="flex justify-between py-1 border-b border-slate-900">
              <span className="text-slate-400">Min Required Capacitance Co,min</span>
              <span className="font-mono text-slate-200">{calcData ? (calcData?.basic?.c_min_uf)?.toFixed(1) ?? '-' : '-'} μF</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-900">
              <span className="text-slate-400">Actual Set Capacitance Co</span>
              <span className="font-mono text-slate-200">{cUf && !isNaN(parseFloat(cUf)) ? parseFloat(cUf).toFixed(2) : '-'} μF</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-900">
              <span className="text-slate-400">Capacitor RMS Current</span>
              <span className="font-mono text-slate-200">{calcData ? (calcData?.basic?.cout_rms_a)?.toFixed(2) ?? '-' : '-'} A</span>
            </div>
            <div className="flex justify-between py-1 text-cyan-300 font-semibold">
              <span>ESR Loss</span>
              <span className="font-mono"><span className="text-emerald-400 font-mono">{calcData?.losses?.p_cap_esr?.toFixed(2) ?? '-'}</span> W</span>
            </div>
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div className="flex flex-col gap-1.5">
              <label className="text-[11px] text-slate-400 font-semibold">Actual Output Cap Co (μF)</label>
              <input className="flex h-8 w-full rounded-md border border-slate-850 bg-[#020617] px-3 py-1 text-xs outline-none focus:border-cyan-500 transition-colors font-mono text-cyan-400" type="text" value={cUf} onChange={(e) => setCUf(e.target.value)} />
            </div>
            <div className="flex flex-col gap-1.5">
              <label className="text-[11px] text-slate-400 font-semibold">Capacitor ESR (mΩ)</label>
              <input className="flex h-8 w-full rounded-md border border-slate-850 bg-[#020617] px-3 py-1 text-xs outline-none focus:border-cyan-500 transition-colors font-mono text-cyan-400" type="number" value={esr} onChange={(e) => setEsr(parseFloat(e.target.value) || 0)} />
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
                Rated load resistance RL from output voltage Vout and rated current Iout:
              </div>
              <Latex math="R_L = \frac{V_{out}}{I_{out}}" block />
              <Latex math="P_{out} = V_{out} \cdot I_{out}" block />
            </div>
          )}
          
          <div className="p-3 bg-slate-950/40 rounded-lg border border-slate-800 space-y-1 text-xs">
            <span className="text-[11px] font-semibold text-cyan-400 block mb-1">Stress & Operating Data</span>
            <div className="flex justify-between py-1 border-b border-slate-900 font-mono">
              <span className="text-slate-400 font-mono">Equivalent Resistance RL</span>
              <span className="font-mono text-slate-200">
                {iout > 0 ? (vout / iout).toFixed(2) : '-'} Ω
              </span>
            </div>
            <div className="flex justify-between py-1 text-cyan-300 font-semibold">
              <span>Rated Output Power Pout</span>
              <span className="font-mono">{(vout * iout).toFixed(1)} W</span>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="flex flex-col gap-1.5">
              <label className="text-[11px] text-slate-400 font-semibold">Adjust Vout (V)</label>
              <input className="flex h-8 w-full rounded-md border border-slate-850 bg-[#020617] px-3 py-1 text-xs outline-none focus:border-cyan-500 transition-colors font-mono text-cyan-400" type="number" value={vout} onChange={(e) => setVout(parseFloat(e.target.value) || 0)} />
            </div>
            <div className="flex flex-col gap-1.5">
              <label className="text-[11px] text-slate-400 font-semibold">Adjust Iout (A)</label>
              <input className="flex h-8 w-full rounded-md border border-slate-850 bg-[#020617] px-3 py-1 text-xs outline-none focus:border-cyan-500 transition-colors font-mono text-cyan-400" type="number" value={iout} onChange={(e) => setIout(parseFloat(e.target.value) || 0)} />
            </div>
          </div>
        </div>
      );
      
    case 'GND':
      return (
        <div className="space-y-4 text-xs">
          <div className="flex justify-between items-center mb-1 bg-slate-900/30 p-1.5 rounded border border-slate-800/40">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Ground Reference Notes</span>
            {renderFormulaToggle()}
          </div>
          {expandFormula && (
            <div className="p-3 bg-slate-950/40 rounded-lg border border-slate-800 space-y-2 animate-in fade-in slide-in-from-top-1 duration-150">
              <div className="text-[11px] text-slate-400 leading-relaxed">
                The GND reference node establishes the zero-potential benchmark across the Buck converter. Star grounding is recommended to minimize common-mode switching noise coupling into analog feedback pins.
              </div>
              <Latex math="V_{GND} = 0\text{ V}" block />
            </div>
          )}
        </div>
      );
      
    default:
      return null;
  }
}