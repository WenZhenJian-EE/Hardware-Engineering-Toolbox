import React, { useState, useEffect, useRef } from 'react';
import { Button } from './ui/Button';
import { Maximize2, Minimize2, Save } from 'lucide-react';
import {
  SchematicDCSource,
  SchematicACSource,
  SchematicZenerDiode,
  SchematicTvsDiode,
  SchematicGround,
  SchematicResistor,
  SchematicInductor
} from './ui/SchematicSymbols';

interface TvsZenerSchematicSandboxProps {
  activeTab: 'zener' | 'tvs';
  onConnectionChange: (isWired: boolean) => void;
  vinZener?: number;
  voutZener?: number;
  rLimit?: number;
  zenerPower?: number;
  vSurge?: number;
  rSrc?: number;
  iPeakAct?: number;
  vClampAct?: number;
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
  if (compId === 'GND') return 'V';
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

export default function TvsZenerSchematicSandbox({
  activeTab,
  onConnectionChange,
  vinZener = 12,
  voutZener = 5.1,
  rLimit = 100,
  zenerPower = 0.5,
  vSurge = 1000,
  rSrc = 2,
  iPeakAct = 150,
  vClampAct = 12.5
}: TvsZenerSchematicSandboxProps) {
  const [isFullScreen, setIsFullScreen] = useState(false);

  const templates: { [key: string]: { [pin: string]: { x: number; y: number } } } = {
    Vin: { P: { x: -40, y: 0 }, N: { x: 40, y: 0 } },
    R_limit: { Pin1: { x: -40, y: 0 }, Pin2: { x: 40, y: 0 } },
    Dz: { A: { x: -40, y: 0 }, K: { x: 40, y: 0 } },
    RL: { Pin1: { x: -40, y: 0 }, Pin2: { x: 40, y: 0 } },
    Vsurge: { P: { x: -40, y: 0 }, N: { x: 40, y: 0 } },
    R_src: { Pin1: { x: -40, y: 0 }, Pin2: { x: 40, y: 0 } },
    L_line: { Pin1: { x: -40, y: 0 }, Pin2: { x: 40, y: 0 } },
    TVS: { A: { x: -40, y: 0 }, K: { x: 40, y: 0 } },
    EUT: { Pin1: { x: -40, y: 0 }, Pin2: { x: 40, y: 0 } },
    GND: { Pin: { x: 0, y: 0 } }
  };

  const getPinsForTab = () => {
    if (activeTab === 'zener') {
      return [
        "Vin.P", "Vin.N",
        "R_limit.Pin1", "R_limit.Pin2",
        "Dz.A", "Dz.K",
        "RL.Pin1", "RL.Pin2",
        "GND.Pin"
      ];
    } else {
      return [
        "Vsurge.P", "Vsurge.N",
        "R_src.Pin1", "R_src.Pin2",
        "L_line.Pin1", "L_line.Pin2",
        "TVS.A", "TVS.K",
        "EUT.Pin1", "EUT.Pin2",
        "GND.Pin"
      ];
    }
  };

  const getNetGroupsForTab = () => {
    if (activeTab === 'zener') {
      return {
        "Vin.P": "Net_Vin", "R_limit.Pin1": "Net_Vin",
        "R_limit.Pin2": "Net_Vout", "Dz.K": "Net_Vout", "RL.Pin1": "Net_Vout",
        "Vin.N": "Net_GND", "Dz.A": "Net_GND", "RL.Pin2": "Net_GND", "GND.Pin": "Net_GND"
      } as { [pin: string]: string };
    } else {
      return {
        "Vsurge.P": "Net_Surge_In", "R_src.Pin1": "Net_Surge_In",
        "R_src.Pin2": "Net_Line_Mid", "L_line.Pin1": "Net_Line_Mid",
        "L_line.Pin2": "Net_Clamp_Out", "TVS.K": "Net_Clamp_Out", "EUT.Pin1": "Net_Clamp_Out",
        "Vsurge.N": "Net_GND", "TVS.A": "Net_GND", "EUT.Pin2": "Net_GND", "GND.Pin": "Net_GND"
      } as { [pin: string]: string };
    }
  };

  const pinToNetGroup = getNetGroupsForTab();
  const allPins = getPinsForTab();

  const [componentsPos, setComponentsPos] = useState<{ [key: string]: { x: number; y: number; rotation: number } }>(() => {
    if (activeTab === 'zener') {
      return {
        Vin: { x: 100, y: 200, rotation: 90 },
        R_limit: { x: 280, y: 100, rotation: 0 },
        Dz: { x: 420, y: 200, rotation: 90 },
        RL: { x: 580, y: 200, rotation: 90 },
        GND: { x: 420, y: 320, rotation: 0 }
      };
    } else {
      return {
        Vsurge: { x: 80, y: 200, rotation: 90 },
        R_src: { x: 220, y: 100, rotation: 0 },
        L_line: { x: 380, y: 100, rotation: 0 },
        TVS: { x: 500, y: 200, rotation: 90 },
        EUT: { x: 650, y: 200, rotation: 90 },
        GND: { x: 500, y: 320, rotation: 0 }
      };
    }
  });

  const [wires, setWires] = useState<{ from: string; to: string }[]>([]);
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saved'>('idle');

  const handleSaveLayout = () => {
    localStorage.setItem(`toolbox_tvszener_layout_pos_${activeTab}`, JSON.stringify(componentsPos));
    localStorage.setItem(`toolbox_tvszener_layout_wires_${activeTab}`, JSON.stringify(wires));
    setSaveStatus('saved');
    setTimeout(() => setSaveStatus('idle'), 1500);
  };

  useEffect(() => {
    const savedPos = localStorage.getItem(`toolbox_tvszener_layout_pos_${activeTab}`);
    const savedWires = localStorage.getItem(`toolbox_tvszener_layout_wires_${activeTab}`);

    if (savedPos) {
      try {
        setComponentsPos(JSON.parse(savedPos));
      } catch (e) {
        console.error("Failed to parse saved TVS/Zener component positions", e);
      }
    } else {
      if (activeTab === 'zener') {
        setComponentsPos({
          Vin: { x: 100, y: 200, rotation: 90 },
          R_limit: { x: 280, y: 100, rotation: 0 },
          Dz: { x: 420, y: 200, rotation: 90 },
          RL: { x: 580, y: 200, rotation: 90 },
          GND: { x: 420, y: 320, rotation: 0 }
        });
      } else {
        setComponentsPos({
          Vsurge: { x: 80, y: 200, rotation: 90 },
          R_src: { x: 220, y: 100, rotation: 0 },
          L_line: { x: 380, y: 100, rotation: 0 },
          TVS: { x: 500, y: 200, rotation: 90 },
          EUT: { x: 650, y: 200, rotation: 90 },
          GND: { x: 500, y: 320, rotation: 0 }
        });
      }
    }

    if (savedWires) {
      try {
        setWires(JSON.parse(savedWires));
      } catch (e) {
        console.error("Failed to parse saved TVS/Zener wires", e);
        setWires([]);
      }
    } else {
      setWires([]);
    }
  }, [activeTab]);

  const [activeDragComponent, setActiveDragComponent] = useState<string | null>(null);
  const [dragStartPin, setDragStartPin] = useState<string | null>(null);
  const [tempWireEnd, setTempWireEnd] = useState<{ x: number; y: number } | null>(null);
  const [snapTargetPin, setSnapTargetPin] = useState<string | null>(null);
  const [drcViolation, setDrcViolation] = useState<{ message: string; x: number; y: number } | null>(null);

  const dragStartOffset = useRef({ x: 0, y: 0 });
  const hasDragged = useRef(false);
  const canvasRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    let isComplete = false;
    if (activeTab === 'zener') {
      const v_in = wires.some(w => (w.from === 'Vin.P' && w.to === 'R_limit.Pin1') || (w.from === 'R_limit.Pin1' && w.to === 'Vin.P'));
      const v_out1 = wires.some(w => (w.from === 'R_limit.Pin2' && w.to === 'Dz.K') || (w.from === 'Dz.K' && w.to === 'R_limit.Pin2'));
      const v_out2 = wires.some(w => (w.from === 'Dz.K' && w.to === 'RL.Pin1') || (w.from === 'RL.Pin1' && w.to === 'Dz.K'));
      const gnd1 = wires.some(w => (w.from === 'Vin.N' && w.to === 'GND.Pin') || (w.from === 'GND.Pin' && w.to === 'Vin.N'));
      const gnd2 = wires.some(w => (w.from === 'Dz.A' && w.to === 'GND.Pin') || (w.from === 'GND.Pin' && w.to === 'Dz.A'));
      const gnd3 = wires.some(w => (w.from === 'RL.Pin2' && w.to === 'GND.Pin') || (w.from === 'GND.Pin' && w.to === 'RL.Pin2'));

      isComplete = v_in && (v_out1 || v_out2) && gnd1 && gnd2 && gnd3;
    } else {
      const surge_in = wires.some(w => (w.from === 'Vsurge.P' && w.to === 'R_src.Pin1') || (w.from === 'R_src.Pin1' && w.to === 'Vsurge.P'));
      const mid = wires.some(w => (w.from === 'R_src.Pin2' && w.to === 'L_line.Pin1') || (w.from === 'L_line.Pin1' && w.to === 'R_src.Pin2'));
      const out1 = wires.some(w => (w.from === 'L_line.Pin2' && w.to === 'TVS.K') || (w.from === 'TVS.K' && w.to === 'L_line.Pin2'));
      const out2 = wires.some(w => (w.from === 'TVS.K' && w.to === 'EUT.Pin1') || (w.from === 'EUT.Pin1' && w.to === 'TVS.K'));
      const gnd1 = wires.some(w => (w.from === 'Vsurge.N' && w.to === 'GND.Pin') || (w.from === 'GND.Pin' && w.to === 'Vsurge.N'));
      const gnd2 = wires.some(w => (w.from === 'TVS.A' && w.to === 'GND.Pin') || (w.from === 'GND.Pin' && w.to === 'TVS.A'));
      const gnd3 = wires.some(w => (w.from === 'EUT.Pin2' && w.to === 'GND.Pin') || (w.from === 'GND.Pin' && w.to === 'EUT.Pin2'));

      isComplete = surge_in && mid && (out1 || out2) && gnd1 && gnd2 && gnd3;
    }
    onConnectionChange(isComplete);
  }, [wires, activeTab]);

  const getPinCoordsMap = () => {
    const map = new Map<string, { x: number; y: number }>();
    for (const [compId, pos] of Object.entries(componentsPos)) {
      const pins = templates[compId];
      if (!pins) continue;
      for (const [pinName, offset] of Object.entries(pins)) {
        const pinId = `${compId}.${pinName}`;
        if (!allPins.includes(pinId)) continue;
        const globalCoords = getGlobalPinCoords(pos.x, pos.y, pos.rotation, offset.x, offset.y);
        map.set(pinId, globalCoords);
      }
    }
    return map;
  };

  const allPinCoords = getPinCoordsMap();

  const getSvgCoords = (e: React.MouseEvent) => {
    if (!canvasRef.current) return { x: 0, y: 0 };
    const rect = canvasRef.current.getBoundingClientRect();
    const x = Math.round(((e.clientX - rect.left) / rect.width) * 800);
    const y = Math.round(((e.clientY - rect.top) / rect.height) * 400);
    return { x, y };
  };

  const handleComponentMouseDown = (compId: string, e: React.MouseEvent) => {
    e.preventDefault();
    setDrcViolation(null);
    const pos = componentsPos[compId];
    if (!pos) return;
    const coords = getSvgCoords(e);
    dragStartOffset.current = { x: coords.x - pos.x, y: coords.y - pos.y };
    setActiveDragComponent(compId);
    hasDragged.current = false;
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    const coords = getSvgCoords(e);

    if (activeDragComponent) {
      let newX = coords.x - dragStartOffset.current.x;
      let newY = coords.y - dragStartOffset.current.y;
      hasDragged.current = true;

      newX = Math.round(newX / 20) * 20;
      newY = Math.round(newY / 20) * 20;

      newX = Math.max(60, Math.min(740, newX));
      newY = Math.max(60, Math.min(340, newY));

      setComponentsPos(prev => ({
        ...prev,
        [activeDragComponent]: {
          ...prev[activeDragComponent],
          x: newX,
          y: newY
        }
      }));
    } else if (dragStartPin) {
      let target = null;
      let minTargetDist = 30;

      for (const [pinId, pinCoords] of allPinCoords.entries()) {
        if (pinId === dragStartPin) continue;
        const dist = Math.hypot(coords.x - pinCoords.x, coords.y - pinCoords.y);
        if (dist < minTargetDist) {
          target = pinId;
          minTargetDist = dist;
        }
      }

      if (target) {
        if (pinToNetGroup[target] === pinToNetGroup[dragStartPin]) {
          const pinCoords = allPinCoords.get(target)!;
          setTempWireEnd({ x: pinCoords.x, y: pinCoords.y });
          setSnapTargetPin(target);
        } else {
          setTempWireEnd({ x: coords.x, y: coords.y });
          setSnapTargetPin(null);
        }
      } else {
        setTempWireEnd({ x: coords.x, y: coords.y });
        setSnapTargetPin(null);
      }
    }
  };

  const handleMouseUp = (e: React.MouseEvent) => {
    const coords = getSvgCoords(e);

    if (activeDragComponent) {
      if (!hasDragged.current) {
        setComponentsPos(prev => ({
          ...prev,
          [activeDragComponent]: {
            ...prev[activeDragComponent],
            rotation: (prev[activeDragComponent].rotation + 90) % 360
          }
        }));
      }
      setActiveDragComponent(null);
    } else if (dragStartPin) {
      let finalSnapPin = snapTargetPin;
      if (!finalSnapPin) {
        let minTargetDist = 30;
        for (const [pinId, pinCoords] of allPinCoords.entries()) {
          if (pinId === dragStartPin) continue;
          const dist = Math.hypot(coords.x - pinCoords.x, coords.y - pinCoords.y);
          if (dist < minTargetDist && pinToNetGroup[pinId] === pinToNetGroup[dragStartPin]) {
            finalSnapPin = pinId;
            minTargetDist = dist;
          }
        }
      }

      if (finalSnapPin) {
        const exists = wires.some(w => 
          (w.from === dragStartPin && w.to === finalSnapPin) ||
          (w.from === finalSnapPin && w.to === dragStartPin)
        );
        if (!exists) {
          setWires(prev => [...prev, { from: dragStartPin, to: finalSnapPin }]);
        }
      } else {
        let illegalTarget = null;
        for (const [pinId, pinCoords] of allPinCoords.entries()) {
          if (pinId === dragStartPin) continue;
          const dist = Math.hypot(coords.x - pinCoords.x, coords.y - pinCoords.y);
          if (dist <= 30) {
            illegalTarget = pinId;
            break;
          }
        }

        if (illegalTarget) {
          const targetCoords = allPinCoords.get(illegalTarget)!;
          const startNet = pinToNetGroup[dragStartPin];
          const targetNet = pinToNetGroup[illegalTarget];
          
          let explanation = '';
          if (startNet === 'Net_Vin' && targetNet === 'Net_GND') {
            explanation = ' (Input voltage short-circuit to GND, burns out power supply)';
          } else if (startNet === 'Net_Surge_In' && targetNet === 'Net_GND') {
            explanation = ' (Surge voltage short-circuit to GND, causes severe breakdown damage)';
          } else {
            explanation = ' (Mismatched electrical net, illegal connection)';
          }

          const msg = `Cannot connect ${dragStartPin} and ${illegalTarget}${explanation}!`;
          setDrcViolation({
            message: msg,
            x: targetCoords.x,
            y: targetCoords.y
          });
        }
      }

      setDragStartPin(null);
      setTempWireEnd(null);
      setSnapTargetPin(null);
    }
  };

  const handleAutoConnect = () => {
    if (activeTab === 'zener') {
      setWires([
        { from: 'Vin.P', to: 'R_limit.Pin1' },
        { from: 'R_limit.Pin2', to: 'Dz.K' },
        { from: 'Dz.K', to: 'RL.Pin1' },
        { from: 'Vin.N', to: 'GND.Pin' },
        { from: 'Dz.A', to: 'GND.Pin' },
        { from: 'RL.Pin2', to: 'GND.Pin' }
      ]);
    } else {
      setWires([
        { from: 'Vsurge.P', to: 'R_src.Pin1' },
        { from: 'R_src.Pin2', to: 'L_line.Pin1' },
        { from: 'L_line.Pin2', to: 'TVS.K' },
        { from: 'TVS.K', to: 'EUT.Pin1' },
        { from: 'Vsurge.N', to: 'GND.Pin' },
        { from: 'TVS.A', to: 'GND.Pin' },
        { from: 'EUT.Pin2', to: 'GND.Pin' }
      ]);
    }
  };

  const handleResetWires = () => {
    localStorage.removeItem(`toolbox_tvszener_layout_pos_${activeTab}`);
    localStorage.removeItem(`toolbox_tvszener_layout_wires_${activeTab}`);
    setWires([]);
    if (activeTab === 'zener') {
      setComponentsPos({
        Vin: { x: 100, y: 200, rotation: 90 },
        R_limit: { x: 280, y: 100, rotation: 0 },
        Dz: { x: 420, y: 200, rotation: 90 },
        RL: { x: 580, y: 200, rotation: 90 },
        GND: { x: 420, y: 320, rotation: 0 }
      });
    } else {
      setComponentsPos({
        Vsurge: { x: 80, y: 200, rotation: 90 },
        R_src: { x: 220, y: 100, rotation: 0 },
        L_line: { x: 380, y: 100, rotation: 0 },
        TVS: { x: 500, y: 200, rotation: 90 },
        EUT: { x: 650, y: 200, rotation: 90 },
        GND: { x: 500, y: 320, rotation: 0 }
      });
    }
  };

  const renderRatsnest = () => {
    const list: { from: string; to: string }[] = [];
    if (activeTab === 'zener') {
      const conns = [
        { from: 'Vin.P', to: 'R_limit.Pin1' },
        { from: 'R_limit.Pin2', to: 'Dz.K' },
        { from: 'Dz.K', to: 'RL.Pin1' },
        { from: 'Vin.N', to: 'GND.Pin' },
        { from: 'Dz.A', to: 'GND.Pin' },
        { from: 'RL.Pin2', to: 'GND.Pin' }
      ];
      for (const c of conns) {
        const connected = wires.some(w => (w.from === c.from && w.to === c.to) || (w.from === c.to && w.to === c.from));
        if (!connected) list.push(c);
      }
    } else {
      const conns = [
        { from: 'Vsurge.P', to: 'R_src.Pin1' },
        { from: 'R_src.Pin2', to: 'L_line.Pin1' },
        { from: 'L_line.Pin2', to: 'TVS.K' },
        { from: 'TVS.K', to: 'EUT.Pin1' },
        { from: 'Vsurge.N', to: 'GND.Pin' },
        { from: 'TVS.A', to: 'GND.Pin' },
        { from: 'EUT.Pin2', to: 'GND.Pin' }
      ];
      for (const c of conns) {
        const connected = wires.some(w => (w.from === c.from && w.to === c.to) || (w.from === c.to && w.to === c.from));
        if (!connected) list.push(c);
      }
    }

    return list.map((conn, idx) => {
      const p1 = allPinCoords.get(conn.from);
      const p2 = allPinCoords.get(conn.to);
      if (!p1 || !p2) return null;
      return (
        <g key={`rats-${idx}`} className="pointer-events-none opacity-45">
          <line
            x1={p1.x}
            y1={p1.y}
            x2={p2.x}
            y2={p2.y}
            stroke="#64748b"
            strokeWidth="1.2"
            strokeDasharray="4 4"
            className="animate-pulse"
          />
          <circle
            cx={(p1.x + p2.x) / 2}
            cy={(p1.y + p2.y) / 2}
            r="2"
            fill="#38bdf8"
            className="animate-ping"
          />
        </g>
      );
    });
  };

  const renderCanvas = (isFull: boolean) => (
    <div className={`relative border border-slate-850 rounded-xl overflow-hidden bg-slate-950 ${isFull ? 'flex-1' : 'h-[320px]'}`}>
      <svg
        ref={canvasRef}
        width="100%"
        height="100%"
        viewBox="0 0 800 400"
        className="text-slate-350 w-full h-full select-none"
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
      >
        <defs>
          <pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
            <path d="M 20 0 L 0 0 0 20" fill="none" stroke="rgba(255,255,255,0.03)" strokeWidth="1" />
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#grid)" />

        {wires.map((w, idx) => {
          const cA = allPinCoords.get(w.from);
          const cB = allPinCoords.get(w.to);
          if (!cA || !cB) return null;
          const points = routeOrthogonal(w.from, w.to, cA, cB, componentsPos[w.from.split('.')[0]].rotation, componentsPos[w.to.split('.')[0]].rotation);
          let pathD = `M ${points[0][0]} ${points[0][1]}`;
          for (let i = 1; i < points.length; i++) pathD += ` L ${points[i][0]} ${points[i][1]}`;

          return (
            <g key={idx} className="group">
              <path d={pathD} fill="none" stroke="#22d3ee" strokeWidth="2.5" />
              <circle cx={(cA.x + cB.x) / 2} cy={(cA.y + cB.y) / 2} r="6" fill="#ef4444" className="opacity-0 group-hover:opacity-100 cursor-pointer" onClick={() => setWires(prev => prev.filter((_, i) => i !== idx))} />
              <path d={`M ${(cA.x + cB.x) / 2 - 3} ${(cA.y + cB.y) / 2} L ${(cA.x + cB.x) / 2 + 3} ${(cA.y + cB.y) / 2}`} stroke="white" strokeWidth="1.2" className="opacity-0 group-hover:opacity-100 pointer-events-none" />
            </g>
          );
        })}

        {renderRatsnest()}

        {dragStartPin && tempWireEnd && (() => {
          const cA = allPinCoords.get(dragStartPin)!;
          const dirA = getPinDirection(dragStartPin, componentsPos[dragStartPin.split('.')[0]].rotation);
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
          const isHovered = activeDragComponent === compId;
          const commonProps = {
            x: pos.x,
            y: pos.y,
            rotation: pos.rotation,
            label: compId,
            highlighted: isHovered
          };

          return (
            <g
              key={compId}
              onMouseDown={(e) => handleComponentMouseDown(compId, e)}
              className="cursor-move font-mono"
            >
              {compId === 'Vin' && (
                <SchematicDCSource {...commonProps} subLabel={`${vinZener.toFixed(1)}V`} />
              )}
              {compId === 'R_limit' && (
                <SchematicResistor {...commonProps} subLabel={`${rLimit}Ω`} />
              )}
              {compId === 'Dz' && (
                <SchematicZenerDiode {...commonProps} subLabel={`${voutZener.toFixed(1)}V`} />
              )}
              {compId === 'RL' && (
                <SchematicResistor {...commonProps} subLabel="Load" />
              )}
              {compId === 'Vsurge' && (
                <SchematicACSource {...commonProps} subLabel={`${vSurge}V (Surge)`} />
              )}
              {compId === 'R_src' && (
                <SchematicResistor {...commonProps} subLabel={`${rSrc}Ω`} />
              )}
              {compId === 'L_line' && (
                <SchematicInductor {...commonProps} subLabel="Line Ind" />
              )}
              {compId === 'TVS' && (
                <SchematicTvsDiode {...commonProps} subLabel="TVS" />
              )}
              {compId === 'EUT' && (
                <SchematicResistor {...commonProps} subLabel="IC Load" />
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
              r={isHovered ? 8 : 4}
              fill={isHovered ? '#10b981' : '#38bdf8'}
              stroke="#0f172a"
              strokeWidth="1.5"
              className="cursor-crosshair transition-all"
              onMouseDown={(e) => {
                e.stopPropagation();
                setDrcViolation(null);
                setDragStartPin(pinId);
              }}
            />
          );
        })}
      </svg>

      {drcViolation && (
        <div
          className="absolute z-10 px-3 py-1.5 text-[10px] bg-red-950 border border-red-500 rounded-lg text-red-200 pointer-events-none shadow-lg"
          style={{
            left: `${(drcViolation.x / 800) * 100}%`,
            top: `${(drcViolation.y / 400) * 100 - 15}%`,
            transform: 'translate(-50%, -100%)'
          }}
        >
          ❌ {drcViolation.message}
        </div>
      )}
    </div>
  );

  return (
    <>
      {isFullScreen ? (
        <div className="fixed inset-0 z-50 bg-slate-950/98 backdrop-blur-md flex flex-col p-6 space-y-4 animate-in fade-in zoom-in duration-150">
          <div className="flex justify-between items-center bg-slate-900/60 p-3 rounded-lg border border-slate-800/80 shadow-2xl">
            <div className="flex items-center gap-3">
              <span className="w-2.5 h-2.5 bg-cyan-500 rounded-full animate-ping"></span>
              <span className="text-xs font-bold text-white uppercase tracking-wider">
                {activeTab === 'zener' ? 'Zener Diode Regulator Circuit Topology (Fullscreen)' : 'TVS Diode Transient Clamping Topology (Fullscreen)'}
              </span>
            </div>
            <div className="flex gap-2">
              <Button onClick={handleSaveLayout} size="sm" className="bg-emerald-600 hover:bg-emerald-500 text-white text-xs flex items-center gap-1 cursor-pointer">
                <Save className="w-3.5 h-3.5" />
                {saveStatus === 'saved' ? 'Saved ✓' : 'Save Wiring'}
              </Button>
              <Button onClick={handleAutoConnect} size="sm" variant="outline" className="border-cyan-500/30 text-cyan-400 hover:bg-cyan-950/20 text-xs cursor-pointer">Auto Connect</Button>
              <Button onClick={handleResetWires} size="sm" variant="outline" className="border-red-500/30 text-red-400 hover:bg-red-950/20 text-xs cursor-pointer">Reset Wires</Button>
              <Button onClick={() => setIsFullScreen(false)} size="sm" variant="default" className="bg-slate-800 hover:bg-slate-700 text-white text-xs flex items-center gap-1 cursor-pointer">
                <Minimize2 className="w-3.5 h-3.5" /> Exit Fullscreen
              </Button>
            </div>
          </div>
          {renderCanvas(true)}
        </div>
      ) : (
        <div className="flex flex-col gap-3 h-full">
          <div className="flex justify-between items-center bg-slate-900/60 p-2 rounded-lg border border-slate-800/80">
            <div className="flex gap-2">
              <Button onClick={handleSaveLayout} size="sm" className="bg-emerald-600 hover:bg-emerald-500 text-white text-[10px] flex items-center gap-1 cursor-pointer">
                <Save className="w-3 h-3" />
                {saveStatus === 'saved' ? 'Saved ✓' : 'Save Wiring'}
              </Button>
              <Button onClick={handleAutoConnect} size="sm" variant="outline" className="border-cyan-500/30 text-cyan-400 hover:bg-cyan-950/20 text-[10px] cursor-pointer">Auto Connect</Button>
              <Button onClick={handleResetWires} size="sm" variant="outline" className="border-red-500/30 text-red-400 hover:bg-red-950/20 text-[10px] cursor-pointer">Reset Wires</Button>
              <Button onClick={() => setIsFullScreen(true)} size="sm" variant="outline" className="border-slate-700 text-slate-350 hover:bg-slate-800 text-[10px] flex items-center gap-1 cursor-pointer">
                <Maximize2 className="w-3.5 h-3.5" /> Fullscreen
              </Button>
            </div>
            <span className="text-[10px] text-slate-400">💡 Tip: Click components to rotate 90°; drag between pin terminals to route wires.</span>
          </div>
          {renderCanvas(false)}
        </div>
      )}
    </>
  );
}
