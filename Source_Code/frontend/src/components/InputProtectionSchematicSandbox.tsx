import React, { useState, useEffect, useRef } from 'react';
import { Button } from './ui/Button';
import { Maximize2, Minimize2, Save } from 'lucide-react';
import {
  SchematicDCSource,
  SchematicACSource,
  SchematicGround,
  SchematicResistor,
  SchematicCapacitor,
  SchematicCapacitorPolar,
  SchematicFuse,
  SchematicNtc
} from './ui/SchematicSymbols';

interface InputProtectionSchematicSandboxProps {
  activeTab: 'fuse' | 'ntc' | 'rc';
  onConnectionChange: (isWired: boolean) => void;
  vin?: number;
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

export default function InputProtectionSchematicSandbox({
  activeTab,
  onConnectionChange,
  vin = 220
}: InputProtectionSchematicSandboxProps) {
  const [isFullScreen, setIsFullScreen] = useState(false);

  const templates: { [key: string]: { [pin: string]: { x: number; y: number } } } = {
    Vin: { P: { x: -40, y: 0 }, N: { x: 40, y: 0 } },
    VAC: { P: { x: -40, y: 0 }, N: { x: 40, y: 0 } },
    Fuse: { Pin1: { x: -40, y: 0 }, Pin2: { x: 40, y: 0 } },
    R_series: { Pin1: { x: -40, y: 0 }, Pin2: { x: 40, y: 0 } },
    C_bulk: { P: { x: -40, y: 0 }, N: { x: 40, y: 0 } },
    NTC: { Pin1: { x: -40, y: 0 }, Pin2: { x: 40, y: 0 } },
    CX: { Pin1: { x: -40, y: 0 }, Pin2: { x: 40, y: 0 } },
    R_discharge: { Pin1: { x: -40, y: 0 }, Pin2: { x: 40, y: 0 } },
    GND: { Pin: { x: 0, y: 0 } }
  };

  const getPinsForTab = () => {
    switch (activeTab) {
      case 'fuse':
        return ["Vin.P", "Vin.N", "Fuse.Pin1", "Fuse.Pin2", "R_series.Pin1", "R_series.Pin2", "C_bulk.P", "C_bulk.N", "GND.Pin"];
      case 'ntc':
        return ["Vin.P", "Vin.N", "NTC.Pin1", "NTC.Pin2", "C_bulk.P", "C_bulk.N", "GND.Pin"];
      case 'rc':
        return ["VAC.P", "VAC.N", "CX.Pin1", "CX.Pin2", "R_discharge.Pin1", "R_discharge.Pin2"];
      default:
        return [];
    }
  };

  const getNetGroupsForTab = () => {
    switch (activeTab) {
      case 'fuse':
        return {
          "Vin.P": "Net_In", "Fuse.Pin1": "Net_In",
          "Fuse.Pin2": "Net_Fuse_Out", "R_series.Pin1": "Net_Fuse_Out",
          "R_series.Pin2": "Net_Cap_In", "C_bulk.P": "Net_Cap_In",
          "Vin.N": "Net_GND", "C_bulk.N": "Net_GND", "GND.Pin": "Net_GND"
        } as { [pin: string]: string };
      case 'ntc':
        return {
          "Vin.P": "Net_In", "NTC.Pin1": "Net_In",
          "NTC.Pin2": "Net_Cap_In", "C_bulk.P": "Net_Cap_In",
          "Vin.N": "Net_GND", "C_bulk.N": "Net_GND", "GND.Pin": "Net_GND"
        } as { [pin: string]: string };
      case 'rc':
        return {
          "VAC.P": "Net_AC_L", "CX.Pin1": "Net_AC_L", "R_discharge.Pin1": "Net_AC_L",
          "VAC.N": "Net_AC_N", "CX.Pin2": "Net_AC_N", "R_discharge.Pin2": "Net_AC_N"
        } as { [pin: string]: string };
      default:
        return {};
    }
  };

  const pinToNetGroup = getNetGroupsForTab();
  const allPins = getPinsForTab();

  const [componentsPos, setComponentsPos] = useState<{ [key: string]: { x: number; y: number; rotation: number } }>(() => {
    return {
      Vin: { x: 100, y: 200, rotation: 90 },
      Fuse: { x: 260, y: 100, rotation: 0 },
      R_series: { x: 420, y: 100, rotation: 0 },
      C_bulk: { x: 580, y: 200, rotation: 90 },
      GND: { x: 380, y: 320, rotation: 0 }
    };
  });

  const [wires, setWires] = useState<{ from: string; to: string }[]>([]);
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saved'>('idle');

  const handleSaveLayout = () => {
    localStorage.setItem(`toolbox_inputprotection_layout_pos_${activeTab}`, JSON.stringify(componentsPos));
    localStorage.setItem(`toolbox_inputprotection_layout_wires_${activeTab}`, JSON.stringify(wires));
    setSaveStatus('saved');
    setTimeout(() => setSaveStatus('idle'), 1500);
  };

  useEffect(() => {
    const savedPos = localStorage.getItem(`toolbox_inputprotection_layout_pos_${activeTab}`);
    const savedWires = localStorage.getItem(`toolbox_inputprotection_layout_wires_${activeTab}`);

    if (savedPos) {
      try {
        setComponentsPos(JSON.parse(savedPos));
      } catch (e) {
        console.error("Failed to parse saved InputProtection component positions", e);
      }
    } else {
      switch (activeTab) {
        case 'fuse':
          setComponentsPos({
            Vin: { x: 100, y: 200, rotation: 90 },
            Fuse: { x: 260, y: 100, rotation: 0 },
            R_series: { x: 420, y: 100, rotation: 0 },
            C_bulk: { x: 580, y: 200, rotation: 90 },
            GND: { x: 380, y: 320, rotation: 0 }
          });
          break;
        case 'ntc':
          setComponentsPos({
            Vin: { x: 100, y: 200, rotation: 90 },
            NTC: { x: 300, y: 100, rotation: 0 },
            C_bulk: { x: 540, y: 200, rotation: 90 },
            GND: { x: 320, y: 320, rotation: 0 }
          });
          break;
        case 'rc':
          setComponentsPos({
            VAC: { x: 100, y: 200, rotation: 90 },
            CX: { x: 300, y: 200, rotation: 90 },
            R_discharge: { x: 500, y: 200, rotation: 90 }
          });
          break;
      }
    }

    if (savedWires) {
      try {
        setWires(JSON.parse(savedWires));
      } catch (e) {
        console.error("Failed to parse saved InputProtection wires", e);
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
    if (activeTab === 'fuse') {
      const w1 = wires.some(w => (w.from === 'Vin.P' && w.to === 'Fuse.Pin1') || (w.from === 'Fuse.Pin1' && w.to === 'Vin.P'));
      const w2 = wires.some(w => (w.from === 'Fuse.Pin2' && w.to === 'R_series.Pin1') || (w.from === 'R_series.Pin1' && w.to === 'Fuse.Pin2'));
      const w3 = wires.some(w => (w.from === 'R_series.Pin2' && w.to === 'C_bulk.P') || (w.from === 'C_bulk.P' && w.to === 'R_series.Pin2'));
      const gnd1 = wires.some(w => (w.from === 'Vin.N' && w.to === 'GND.Pin') || (w.from === 'GND.Pin' && w.to === 'Vin.N'));
      const gnd2 = wires.some(w => (w.from === 'C_bulk.N' && w.to === 'GND.Pin') || (w.from === 'GND.Pin' && w.to === 'C_bulk.N'));
      isComplete = w1 && w2 && w3 && gnd1 && gnd2;
    } else if (activeTab === 'ntc') {
      const w1 = wires.some(w => (w.from === 'Vin.P' && w.to === 'NTC.Pin1') || (w.from === 'NTC.Pin1' && w.to === 'Vin.P'));
      const w2 = wires.some(w => (w.from === 'NTC.Pin2' && w.to === 'C_bulk.P') || (w.from === 'C_bulk.P' && w.to === 'NTC.Pin2'));
      const gnd1 = wires.some(w => (w.from === 'Vin.N' && w.to === 'GND.Pin') || (w.from === 'GND.Pin' && w.to === 'Vin.N'));
      const gnd2 = wires.some(w => (w.from === 'C_bulk.N' && w.to === 'GND.Pin') || (w.from === 'GND.Pin' && w.to === 'C_bulk.N'));
      isComplete = w1 && w2 && gnd1 && gnd2;
    } else if (activeTab === 'rc') {
      const w1 = wires.some(w => (w.from === 'VAC.P' && w.to === 'CX.Pin1') || (w.from === 'CX.Pin1' && w.to === 'VAC.P'));
      const w2 = wires.some(w => (w.from === 'CX.Pin1' && w.to === 'R_discharge.Pin1') || (w.from === 'R_discharge.Pin1' && w.to === 'CX.Pin1'));
      const w3 = wires.some(w => (w.from === 'VAC.N' && w.to === 'CX.Pin2') || (w.from === 'CX.Pin2' && w.to === 'VAC.N'));
      const w4 = wires.some(w => (w.from === 'CX.Pin2' && w.to === 'R_discharge.Pin2') || (w.from === 'R_discharge.Pin2' && w.to === 'CX.Pin2'));
      isComplete = w1 && w2 && w3 && w4;
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
          if (startNet === 'Net_In' && targetNet === 'Net_GND') {
            explanation = ' (DC input direct short-circuit to GND, highly hazardous)';
          } else if (startNet === 'Net_AC_L' && targetNet === 'Net_AC_N') {
            explanation = ' (AC line-to-neutral direct short-circuit, causes severe electrical arcing)';
          } else {
            explanation = ' (Mismatched electrical net, refer to schematic topology)';
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
    switch (activeTab) {
      case 'fuse':
        setWires([
          { from: 'Vin.P', to: 'Fuse.Pin1' },
          { from: 'Fuse.Pin2', to: 'R_series.Pin1' },
          { from: 'R_series.Pin2', to: 'C_bulk.P' },
          { from: 'Vin.N', to: 'GND.Pin' },
          { from: 'C_bulk.N', to: 'GND.Pin' }
        ]);
        break;
      case 'ntc':
        setWires([
          { from: 'Vin.P', to: 'NTC.Pin1' },
          { from: 'NTC.Pin2', to: 'C_bulk.P' },
          { from: 'Vin.N', to: 'GND.Pin' },
          { from: 'C_bulk.N', to: 'GND.Pin' }
        ]);
        break;
      case 'rc':
        setWires([
          { from: 'VAC.P', to: 'CX.Pin1' },
          { from: 'CX.Pin1', to: 'R_discharge.Pin1' },
          { from: 'VAC.N', to: 'CX.Pin2' },
          { from: 'CX.Pin2', to: 'R_discharge.Pin2' }
        ]);
        break;
    }
  };

  const handleResetWires = () => {
    localStorage.removeItem(`toolbox_inputprotection_layout_pos_${activeTab}`);
    localStorage.removeItem(`toolbox_inputprotection_layout_wires_${activeTab}`);
    setWires([]);
    switch (activeTab) {
      case 'fuse':
        setComponentsPos({
          Vin: { x: 100, y: 200, rotation: 90 },
          Fuse: { x: 260, y: 100, rotation: 0 },
          R_series: { x: 420, y: 100, rotation: 0 },
          C_bulk: { x: 580, y: 200, rotation: 90 },
          GND: { x: 380, y: 320, rotation: 0 }
        });
        break;
      case 'ntc':
        setComponentsPos({
          Vin: { x: 100, y: 200, rotation: 90 },
          NTC: { x: 300, y: 100, rotation: 0 },
          C_bulk: { x: 540, y: 200, rotation: 90 },
          GND: { x: 320, y: 320, rotation: 0 }
        });
        break;
      case 'rc':
        setComponentsPos({
          VAC: { x: 100, y: 200, rotation: 90 },
          CX: { x: 300, y: 200, rotation: 90 },
          R_discharge: { x: 500, y: 200, rotation: 90 },
          GND: { x: 300, y: 320, rotation: 0 }
        });
        break;
    }
  };

  const renderRatsnest = () => {
    const list: { from: string; to: string }[] = [];
    const pinCoords = getPinCoordsMap();

    if (activeTab === 'fuse') {
      const conns = [
        { from: 'Vin.P', to: 'Fuse.Pin1' },
        { from: 'Fuse.Pin2', to: 'R_series.Pin1' },
        { from: 'R_series.Pin2', to: 'C_bulk.P' },
        { from: 'Vin.N', to: 'GND.Pin' },
        { from: 'C_bulk.N', to: 'GND.Pin' }
      ];
      for (const c of conns) {
        const connected = wires.some(w => (w.from === c.from && w.to === c.to) || (w.from === c.to && w.to === c.from));
        if (!connected) list.push(c);
      }
    } else if (activeTab === 'ntc') {
      const conns = [
        { from: 'Vin.P', to: 'NTC.Pin1' },
        { from: 'NTC.Pin2', to: 'C_bulk.P' },
        { from: 'Vin.N', to: 'GND.Pin' },
        { from: 'C_bulk.N', to: 'GND.Pin' }
      ];
      for (const c of conns) {
        const connected = wires.some(w => (w.from === c.from && w.to === c.to) || (w.from === c.to && w.to === c.from));
        if (!connected) list.push(c);
      }
    } else if (activeTab === 'rc') {
      const conns = [
        { from: 'VAC.P', to: 'CX.Pin1' },
        { from: 'CX.Pin1', to: 'R_discharge.Pin1' },
        { from: 'VAC.N', to: 'CX.Pin2' },
        { from: 'CX.Pin2', to: 'R_discharge.Pin2' }
      ];
      for (const c of conns) {
        const connected = wires.some(w => (w.from === c.from && w.to === c.to) || (w.from === c.to && w.to === c.from));
        if (!connected) list.push(c);
      }
    }

    return list.map((conn, idx) => {
      const p1 = pinCoords.get(conn.from);
      const p2 = pinCoords.get(conn.to);
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
              <path d={pathD} fill="none" stroke="#e0f2fe" strokeWidth="2.5" />
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
                <SchematicDCSource {...commonProps} subLabel="DC Source" />
              )}
              {compId === 'VAC' && (
                <SchematicACSource {...commonProps} subLabel="AC Source" />
              )}
              {compId === 'Fuse' && (
                <SchematicFuse {...commonProps} subLabel="Fuse" />
              )}
              {compId === 'R_series' && (
                <SchematicResistor {...commonProps} subLabel="Rs" />
              )}
              {compId === 'NTC' && (
                <SchematicNtc {...commonProps} subLabel="NTC" />
              )}
              {compId === 'C_bulk' && (
                <SchematicCapacitorPolar {...commonProps} subLabel="C_bulk" />
              )}
              {compId === 'CX' && (
                <SchematicCapacitor {...commonProps} subLabel="CX" />
              )}
              {compId === 'R_discharge' && (
                <SchematicResistor {...commonProps} subLabel="R_dis" />
              )}
              {compId === 'GND' && activeTab !== 'rc' && (
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
              fill={isHovered ? '#10b981' : '#f43f5e'}
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
                {activeTab === 'fuse' ? 'Fuse Sizing Circuit Topology (Fullscreen)' : (activeTab === 'ntc' ? 'NTC Inrush Limiter Circuit Topology (Fullscreen)' : 'X-Capacitor Discharge Circuit Topology (Fullscreen)')}
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
                <Save className="w-3.5 h-3.5" />
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
