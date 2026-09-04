import React, { useState, useEffect } from 'react';
import ReactECharts from 'echarts-for-react';
import { apiFetch } from '../lib/api';
import { useDragDeckLayout, DragDeck, DragCard } from './ui/LayoutEngine';
import { 
  Plus, 
  Trash2, 
  Check, 
  AlertTriangle, 
  ArrowLeft
} from 'lucide-react';

interface Manufacturer {
  id: number;
  name: string;
  url?: string;
}

interface SwitchDevice {
  id?: number;
  name: string;
  manufacturer_id: number;
  manufacturer?: string;
  type: string;
  v_ds_max: number;
  i_d_max: number;
  r_ds_on: number;
  q_g?: number;
  c_oss?: number;
  package?: string;
  r_jc?: number;
}

interface DiodeDevice {
  id?: number;
  name: string;
  manufacturer_id: number;
  manufacturer?: string;
  type: string;
  v_r_max: number;
  i_f_max: number;
  v_f: number;
  package?: string;
  r_jc?: number;
}

interface ZenerDevice {
  id?: number;
  name: string;
  manufacturer_id: number;
  manufacturer?: string;
  vz: number;
  izt?: number;
  izk?: number;
  zzt?: number;
  p_d?: number;
  package?: string;
}

interface TvsDevice {
  id?: number;
  name: string;
  manufacturer_id: number;
  manufacturer?: string;
  vrwm: number;
  vbr: number;
  vc: number;
  ipp: number;
  pppm: number;
  package?: string;
}

interface FuseDevice {
  id?: number;
  name: string;
  manufacturer_id: number;
  manufacturer?: string;
  i_rated: number;
  v_rated: number;
  i2t: number;
  package?: string;
}

interface NtcDevice {
  id?: number;
  name: string;
  manufacturer_id: number;
  manufacturer?: string;
  r25: number;
  i_max: number;
  joule_rating: number;
  dissipation: number;
  package?: string;
}

interface CapacitorDevice {
  id?: number;
  name: string;
  manufacturer_id: number;
  manufacturer?: string;
  type: string;
  capacitance: number;
  voltage_rating: number;
  esr?: number;
  esl?: number;
  ripple_current?: number;
  temp_max?: number;
  lifetime_hours?: number;
}

interface Material {
  id?: number;
  name: string;
  type: string;
  permeability: number;
  b_sat_25?: number;
  b_sat_100?: number;
  steinmetz_cm_25?: number;
  steinmetz_x_25?: number;
  steinmetz_y_25?: number;
  steinmetz_cm_100?: number;
  steinmetz_x_100?: number;
  steinmetz_y_100?: number;
}

interface Core {
  id?: number;
  name: string;
  shape: string;
  material_id: number;
  material?: string;
  ae: number;
  le: number;
  ve: number;
  wa: number;
  al?: number;
}

export default function DatabaseManagementPanel({ onBack }: { onBack: () => void; setActiveModule?: any }) {
  const [activeTab, setActiveTab] = useState<'switches' | 'diodes' | 'zeners' | 'tvs' | 'capacitors' | 'fuses' | 'ntcs' | 'materials' | 'cores'>('switches');
  const [selectedSwitch, setSelectedSwitch] = useState<SwitchDevice | null>(null);
  const [selectedDiode, setSelectedDiode] = useState<DiodeDevice | null>(null);
  const [selectedZener, setSelectedZener] = useState<ZenerDevice | null>(null);
  const [selectedTvs, setSelectedTvs] = useState<TvsDevice | null>(null);
  const [selectedCap, setSelectedCap] = useState<CapacitorDevice | null>(null);
  const [selectedFuse, setSelectedFuse] = useState<FuseDevice | null>(null);
  const [selectedNtc, setSelectedNtc] = useState<NtcDevice | null>(null);
  const [selectedMaterial, setSelectedMaterial] = useState<Material | null>(null);
  const [selectedCore, setSelectedCore] = useState<Core | null>(null);

  const {
    isDesktop,
    leftSpan,
    rightSpan,
    leftCards,
    rightCards,
    draggedKey,
    cardHeights,
    handleDragStart,
    handleDragEnter,
    handleDragEnd,
    handleResizeStart,
    handleHeightResizeStart,
    handleDropOnColumn,
    handleResetLayout
  } = useDragDeckLayout({
    panelKey: 'layout_databasemanagementpanel_v5',
    activeTab: activeTab,
    defaultCards: ['input', 'results', 'detail'],
    defaultColumns: { input: 'left', results: 'right', detail: 'right' },
    defaultSpans: { input: 4, results: 8, detail: 8 },
    defaultHeights: { input: 850, results: 480, detail: 360 }
  });

  const [manufacturers, setManufacturers] = useState<Manufacturer[]>([]);
  const [switches, setSwitches] = useState<SwitchDevice[]>([]);
  const [diodes, setDiodes] = useState<DiodeDevice[]>([]);
  const [zeners, setZeners] = useState<ZenerDevice[]>([]);
  const [tvsList, setTvsList] = useState<TvsDevice[]>([]);
  const [caps, setCaps] = useState<CapacitorDevice[]>([]);
  const [fuses, setFuses] = useState<FuseDevice[]>([]);
  const [ntcs, setNtcs] = useState<NtcDevice[]>([]);
  const [materials, setMaterials] = useState<Material[]>([]);
  const [cores, setCores] = useState<Core[]>([]);

  // Status indicators
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // New manufacturer modal/input
  const [showMfgForm, setShowMfgForm] = useState(false);
  const [newMfgName, setNewMfgName] = useState('');
  const [newMfgUrl, setNewMfgUrl] = useState('');

  // Form states
  const [newSwitch, setNewSwitch] = useState({
    name: '',
    manufacturer_id: 0,
    type: 'Si',
    v_ds_max: 600,
    i_d_max: 20,
    r_ds_on: 0.08,
    q_g: 50,
    c_oss: 150,
    package: 'TO-247',
    r_jc: 0.8
  });

  const [newDiode, setNewDiode] = useState({
    name: '',
    manufacturer_id: 0,
    type: 'Schottky',
    v_r_max: 600,
    i_f_max: 15,
    v_f: 1.2,
    package: 'TO-220',
    r_jc: 1.5
  });

  const [newZener, setNewZener] = useState({
    name: '',
    manufacturer_id: 0,
    vz: 5.1,
    izt: 5.0,
    izk: 1.0,
    zzt: 10.0,
    p_d: 1.0,
    package: 'SOD-123'
  });

  const [newTvs, setNewTvs] = useState({
    name: '',
    manufacturer_id: 0,
    vrwm: 24.0,
    vbr: 26.7,
    vc: 38.9,
    ipp: 15.4,
    pppm: 600.0,
    package: 'SMB'
  });

  const [newFuse, setNewFuse] = useState({
    name: '',
    manufacturer_id: 0,
    i_rated: 5.0,
    v_rated: 250.0,
    i2t: 5.0,
    package: 'SMD-Nano2'
  });

  const [newNtc, setNewNtc] = useState({
    name: '',
    manufacturer_id: 0,
    r25: 10.0,
    i_max: 3.0,
    joule_rating: 30.0,
    dissipation: 11.0,
    package: 'Radial'
  });

  const [newCap, setNewCap] = useState({
    name: '',
    manufacturer_id: 0,
    type: 'Electrolytic',
    capacitance: 100e-6,
    voltage_rating: 50.0,
    esr: 0.1,
    esl: 15e-9,
    ripple_current: 1.5,
    temp_max: 105.0,
    lifetime_hours: 5000
  });

  const [newMaterial, setNewMaterial] = useState({
    name: '',
    type: 'Ferrite',
    permeability: 2300,
    b_sat_25: 0.51,
    b_sat_100: 0.39,
    steinmetz_cm_25: 0.008,
    steinmetz_x_25: 1.7,
    steinmetz_y_25: 2.7,
    steinmetz_cm_100: 0.012,
    steinmetz_x_100: 1.6,
    steinmetz_y_100: 2.5
  });

  const [newCore, setNewCore] = useState({
    name: '',
    shape: 'EE',
    material_id: 0,
    ae: 52.5,
    le: 57.5,
    ve: 3020,
    wa: 76.0,
    al: 2100
  });

  const API_BASE = '/api/database';

  const getSteinmetzChartOption = (mat: Material) => {
    const cm = mat.steinmetz_cm_100 || mat.steinmetz_cm_25 || 12.0; 
    const x = mat.steinmetz_x_100 || mat.steinmetz_x_25 || 1.6;
    const y = mat.steinmetz_y_100 || mat.steinmetz_y_25 || 2.5;

    const freqs = [50000, 100000, 200000]; // 50k, 100k, 200k Hz
    const bacs: number[] = [];
    const steps = 30;
    const minBac = 10; 
    const maxBac = 300; 
    
    for (let i = 0; i <= steps; i++) {
      const val = minBac * Math.pow(maxBac / minBac, i / steps);
      bacs.push(parseFloat(val.toFixed(1)));
    }

    const seriesData = freqs.map((f) => {
      const fKhz = f / 1000;
      const points = bacs.map((bac) => {
        const pv = cm * Math.pow(fKhz, x) * Math.pow(bac / 1000, y);
        return [bac, parseFloat(pv.toFixed(2))];
      });
      return {
        name: `${fKhz} kHz`,
        type: 'line',
        data: points,
        smooth: true,
        showSymbol: false,
        lineStyle: { width: 3 }
      };
    });

    return {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(15, 23, 42, 0.85)',
        borderColor: '#38bdf8',
        borderWidth: 1.5,
        shadowColor: 'rgba(56, 189, 248, 0.3)',
        shadowBlur: 8,
        textStyle: { color: '#f1f5f9', fontSize: 10 },
        extraCssText: 'backdrop-filter: blur(8px); border-radius: 8px;',
        formatter: (params: any) => {
          let str = `<div class="font-bold text-xs mb-1 text-white">${params[0].axisValue} mT</div>`;
          params.forEach((p: any) => {
            str += `<div class="flex items-center gap-1.5 text-[10px] text-slate-350 mt-0.5">
              <span style="display:inline-block;width:6px;height:6px;border-radius:50%;background-color:${p.color}"></span>
              ${p.seriesName}: <span class="font-mono text-cyan-400 font-bold">${p.data[1]} kW/m³</span>
            </div>`;
          });
          return str;
        }
      },
      legend: {
        data: ['50 kHz', '100 kHz', '200 kHz'],
        textStyle: { color: '#94a3b8', fontSize: 9 },
        bottom: 0
      },
      grid: { left: '10%', right: '10%', bottom: '15%', top: '15%', containLabel: true },
      xAxis: {
        type: 'log',
        name: 'Bac (mT)',
        nameTextStyle: { color: '#94a3b8', fontSize: 8 },
        axisLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } },
        axisLabel: { color: '#94a3b8', fontSize: 8 },
        splitLine: { lineStyle: { color: 'rgba(255,255,255,0.04)' } }
      },
      yAxis: {
        type: 'log',
        name: 'Core Loss Density Pv (kW/m³)',
        nameTextStyle: { color: '#94a3b8', fontSize: 8 },
        axisLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } },
        axisLabel: { color: '#94a3b8', fontSize: 8 },
        splitLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } }
      },
      dataZoom: [
        { type: 'inside', start: 0, end: 100 },
        {
          type: 'slider',
          start: 0,
          end: 100,
          bottom: 25,
          height: 16,
          textStyle: { color: '#94a3b8', fontSize: 8 },
          borderColor: 'rgba(255,255,255,0.04)',
          fillerColor: 'rgba(56, 189, 248, 0.15)'
        }
      ],
      series: seriesData.map((s, idx) => {
        const colors = ['#38bdf8', '#10b981', '#f43f5e'];
        return {
          ...s,
          lineStyle: {
            ...s.lineStyle,
            color: colors[idx],
            shadowColor: colors[idx],
            shadowBlur: 8
          }
        };
      })
    };
  };

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      // Fetch manufacturers
      const mfgRes = await apiFetch(`${API_BASE}/manufacturers`);
      if (!mfgRes.ok) throw new Error('Failed to load manufacturer list');
      const mfgData = await mfgRes.json();
      setManufacturers(mfgData);

      // Fetch switches
      const swRes = await apiFetch(`${API_BASE}/switches`);
      if (!swRes.ok) throw new Error('Failed to load switch device list');
      const swData = await swRes.json();
      setSwitches(swData);

      // Fetch diodes
      const diodeRes = await apiFetch(`${API_BASE}/diodes`);
      if (!diodeRes.ok) throw new Error('Failed to load diode list');
      const diodeData = await diodeRes.json();
      setDiodes(diodeData);

      // Fetch zeners
      const zenerRes = await apiFetch(`${API_BASE}/zeners`);
      if (zenerRes.ok) {
        const zenerData = await zenerRes.json();
        setZeners(zenerData);
      }

      // Fetch tvs
      const tvsRes = await apiFetch(`${API_BASE}/tvs`);
      if (tvsRes.ok) {
        const tvsData = await tvsRes.json();
        setTvsList(tvsData);
      }

      // Fetch capacitors
      const capRes = await apiFetch(`${API_BASE}/capacitors`);
      if (capRes.ok) {
        const capData = await capRes.json();
        setCaps(capData);
      }

      // Fetch fuses
      const fuseRes = await apiFetch(`${API_BASE}/fuses`);
      if (fuseRes.ok) {
        const fuseData = await fuseRes.json();
        setFuses(fuseData);
      }

      // Fetch ntcs
      const ntcRes = await apiFetch(`${API_BASE}/ntcs`);
      if (ntcRes.ok) {
        const ntcData = await ntcRes.json();
        setNtcs(ntcData);
      }

      // Fetch materials
      const matRes = await apiFetch(`${API_BASE}/materials`);
      if (!matRes.ok) throw new Error('Failed to load core material list');
      const matData = await matRes.json();
      setMaterials(matData);

      // Fetch cores
      const coreRes = await apiFetch(`${API_BASE}/cores`);
      if (!coreRes.ok) throw new Error('Failed to load core geometry list');
      const coreData = await coreRes.json();
      setCores(coreData);

      // Set default manufacturer IDs in forms if list not empty
      if (mfgData.length > 0) {
        setNewSwitch(prev => ({ ...prev, manufacturer_id: prev.manufacturer_id || mfgData[0].id }));
        setNewDiode(prev => ({ ...prev, manufacturer_id: prev.manufacturer_id || mfgData[0].id }));
        setNewZener(prev => ({ ...prev, manufacturer_id: prev.manufacturer_id || mfgData[0].id }));
        setNewTvs(prev => ({ ...prev, manufacturer_id: prev.manufacturer_id || mfgData[0].id }));
        setNewFuse(prev => ({ ...prev, manufacturer_id: prev.manufacturer_id || mfgData[0].id }));
        setNewNtc(prev => ({ ...prev, manufacturer_id: prev.manufacturer_id || mfgData[0].id }));
        setNewCap(prev => ({ ...prev, manufacturer_id: prev.manufacturer_id || mfgData[0].id }));
      }
      if (matData.length > 0) {
        setNewCore(prev => ({ ...prev, material_id: prev.material_id || matData[0].id }));
      }

    } catch (err: any) {
      setError(err.message || 'Failed to load component database');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    setSelectedSwitch(null);
    setSelectedDiode(null);
    setSelectedZener(null);
    setSelectedTvs(null);
    setSelectedCap(null);
    setSelectedFuse(null);
    setSelectedNtc(null);
    setSelectedMaterial(null);
    setSelectedCore(null);
  }, [activeTab]);

  const handleAddMfg = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMfgName.trim()) return;

    setError(null);
    setSuccess(null);
    try {
      const res = await apiFetch(`${API_BASE}/manufacturers`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: newMfgName, url: newMfgUrl || null })
      });
      if (!res.ok) {
        const detail = await res.json();
        throw new Error(detail.detail || 'Failed to add manufacturer');
      }
      const data = await res.json();
      setSuccess(`Manufacturer '${newMfgName}' added successfully!`);
      setNewMfgName('');
      setNewMfgUrl('');
      setShowMfgForm(false);
      
      const mfgRes = await apiFetch(`${API_BASE}/manufacturers`);
      const mfgData = await mfgRes.json();
      setManufacturers(mfgData);
      
      if (data && data.id) {
        setNewSwitch(prev => ({ ...prev, manufacturer_id: data.id }));
        setNewDiode(prev => ({ ...prev, manufacturer_id: data.id }));
      }
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleAddSwitch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newSwitch.name.trim()) {
      setError('Part number cannot be empty');
      return;
    }
    setError(null);
    setSuccess(null);
    try {
      const res = await apiFetch(`${API_BASE}/switches`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newSwitch)
      });
      if (!res.ok) {
        const detail = await res.json();
        throw new Error(detail.detail || 'Failed to add switch device');
      }
      setSuccess(`Switch '${newSwitch.name}' added successfully!`);
      setNewSwitch(prev => ({ ...prev, name: '' }));
      fetchData();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleDeleteSwitch = async (name: string) => {
    if (!window.confirm(`Are you sure you want to permanently delete switch '${name}' from database?`)) return;
    setError(null);
    setSuccess(null);
    try {
      const res = await apiFetch(`${API_BASE}/switches/${encodeURIComponent(name)}`, {
        method: 'DELETE'
      });
      if (!res.ok) throw new Error('Failed to delete switch device');
      setSuccess(`Switch '${name}' deleted successfully`);
      fetchData();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleAddDiode = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newDiode.name.trim()) {
      setError('Diode part number cannot be empty');
      return;
    }
    setError(null);
    setSuccess(null);
    try {
      const res = await apiFetch(`${API_BASE}/diodes`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newDiode)
      });
      if (!res.ok) {
        const detail = await res.json();
        throw new Error(detail.detail || 'Failed to add diode');
      }
      setSuccess(`Diode '${newDiode.name}' added successfully!`);
      setNewDiode(prev => ({ ...prev, name: '' }));
      fetchData();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleDeleteDiode = async (name: string) => {
    if (!window.confirm(`Are you sure you want to permanently delete diode '${name}' from database?`)) return;
    setError(null);
    setSuccess(null);
    try {
      const res = await apiFetch(`${API_BASE}/diodes/${encodeURIComponent(name)}`, {
        method: 'DELETE'
      });
      if (!res.ok) throw new Error('Failed to delete diode');
      setSuccess(`Diode '${name}' deleted successfully`);
      fetchData();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleAddZener = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newZener.name.trim()) {
      setError('Zener part number cannot be empty');
      return;
    }
    setError(null);
    setSuccess(null);
    try {
      const res = await apiFetch(`${API_BASE}/zeners`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newZener)
      });
      if (!res.ok) {
        const detail = await res.json();
        throw new Error(detail.detail || 'Failed to add zener diode');
      }
      setSuccess(`Zener diode '${newZener.name}' added successfully!`);
      setNewZener(prev => ({ ...prev, name: '' }));
      fetchData();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleDeleteZener = async (name: string) => {
    if (!window.confirm(`Are you sure you want to permanently delete zener '${name}' from database?`)) return;
    setError(null);
    setSuccess(null);
    try {
      const res = await apiFetch(`${API_BASE}/zeners/${encodeURIComponent(name)}`, {
        method: 'DELETE'
      });
      if (!res.ok) throw new Error('Failed to delete zener diode');
      setSuccess(`Zener diode '${name}' deleted successfully`);
      fetchData();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleAddTvs = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTvs.name.trim()) {
      setError('TVS part number cannot be empty');
      return;
    }
    setError(null);
    setSuccess(null);
    try {
      const res = await apiFetch(`${API_BASE}/tvs`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newTvs)
      });
      if (!res.ok) {
        const detail = await res.json();
        throw new Error(detail.detail || 'Failed to add TVS diode');
      }
      setSuccess(`TVS diode '${newTvs.name}' added successfully!`);
      setNewTvs(prev => ({ ...prev, name: '' }));
      fetchData();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleDeleteTvs = async (name: string) => {
    if (!window.confirm(`Are you sure you want to permanently delete TVS '${name}' from database?`)) return;
    setError(null);
    setSuccess(null);
    try {
      const res = await apiFetch(`${API_BASE}/tvs/${encodeURIComponent(name)}`, {
        method: 'DELETE'
      });
      if (!res.ok) throw new Error('Failed to delete TVS diode');
      setSuccess(`TVS diode '${name}' deleted successfully`);
      fetchData();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleAddCapacitor = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newCap.name.trim()) {
      setError('Capacitor part number cannot be empty');
      return;
    }
    setError(null);
    setSuccess(null);
    try {
      const res = await apiFetch(`${API_BASE}/capacitors`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newCap)
      });
      if (!res.ok) {
        const detail = await res.json();
        throw new Error(detail.detail || 'Failed to add capacitor');
      }
      setSuccess(`Capacitor '${newCap.name}' added successfully!`);
      setNewCap(prev => ({ ...prev, name: '' }));
      fetchData();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleDeleteCapacitor = async (name: string) => {
    if (!window.confirm(`Are you sure you want to permanently delete capacitor '${name}' from database?`)) return;
    setError(null);
    setSuccess(null);
    try {
      const res = await apiFetch(`${API_BASE}/capacitors/${encodeURIComponent(name)}`, {
        method: 'DELETE'
      });
      if (!res.ok) throw new Error('Failed to delete capacitor');
      setSuccess(`Capacitor '${name}' deleted successfully`);
      fetchData();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleAddFuse = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newFuse.name.trim()) {
      setError('Fuse part number cannot be empty');
      return;
    }
    setError(null);
    setSuccess(null);
    try {
      const res = await apiFetch(`${API_BASE}/fuses`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newFuse)
      });
      if (!res.ok) {
        const detail = await res.json();
        throw new Error(detail.detail || 'Failed to add fuse');
      }
      setSuccess(`Fuse '${newFuse.name}' added successfully!`);
      setNewFuse(prev => ({ ...prev, name: '' }));
      fetchData();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleDeleteFuse = async (name: string) => {
    if (!window.confirm(`Are you sure you want to permanently delete fuse '${name}' from database?`)) return;
    setError(null);
    setSuccess(null);
    try {
      const res = await apiFetch(`${API_BASE}/fuses/${encodeURIComponent(name)}`, {
        method: 'DELETE'
      });
      if (!res.ok) throw new Error('Failed to delete fuse');
      setSuccess(`Fuse '${name}' deleted successfully`);
      fetchData();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleAddNtc = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newNtc.name.trim()) {
      setError('NTC part number cannot be empty');
      return;
    }
    setError(null);
    setSuccess(null);
    try {
      const res = await apiFetch(`${API_BASE}/ntcs`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newNtc)
      });
      if (!res.ok) {
        const detail = await res.json();
        throw new Error(detail.detail || 'Failed to add NTC thermistor');
      }
      setSuccess(`NTC thermistor '${newNtc.name}' added successfully!`);
      setNewNtc(prev => ({ ...prev, name: '' }));
      fetchData();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleDeleteNtc = async (name: string) => {
    if (!window.confirm(`Are you sure you want to permanently delete NTC '${name}' from database?`)) return;
    setError(null);
    setSuccess(null);
    try {
      const res = await apiFetch(`${API_BASE}/ntcs/${encodeURIComponent(name)}`, {
        method: 'DELETE'
      });
      if (!res.ok) throw new Error('Failed to delete NTC thermistor');
      setSuccess(`NTC thermistor '${name}' deleted successfully`);
      fetchData();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleAddMaterial = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMaterial.name.trim()) {
      setError('Material name cannot be empty');
      return;
    }
    setError(null);
    setSuccess(null);
    try {
      const res = await apiFetch(`${API_BASE}/materials`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newMaterial)
      });
      if (!res.ok) throw new Error('Failed to add core material');
      setSuccess(`Core material '${newMaterial.name}' added successfully!`);
      setNewMaterial(prev => ({ ...prev, name: '' }));
      fetchData();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleAddCore = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newCore.name.trim()) {
      setError('Core name cannot be empty');
      return;
    }
    setError(null);
    setSuccess(null);
    try {
      const res = await apiFetch(`${API_BASE}/cores`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newCore)
      });
      if (!res.ok) throw new Error('Failed to add core geometry');
      setSuccess(`Core geometry '${newCore.name}' added successfully!`);
      setNewCore(prev => ({ ...prev, name: '' }));
      fetchData();
    } catch (err: any) {
      setError(err.message);
    }
  };

  return (
    <div className="flex-1 overflow-y-auto scrollbar-thin">
      <div className="space-y-6 max-w-7xl mx-auto p-4">
        {/* Title block */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 bg-slate-900/50 border border-slate-800/80 p-5 rounded-xl backdrop-blur-md">
          <div className="flex items-center gap-3">
            <button 
              onClick={onBack}
              className="flex items-center space-x-2 bg-slate-900 hover:bg-slate-800 border border-slate-800 px-3 py-2 rounded-lg text-slate-300 transition mr-2 cursor-pointer"
            >
              <ArrowLeft className="w-4 h-4" />
              <span className="text-xs">Back</span>
            </button>
            <div>
              <h2 className="text-xl font-bold text-white tracking-wide">Component & Material Database</h2>
              <p className="text-xs text-slate-400 mt-1">Manage power switches, rectifiers, magnetics, passive components, and material characteristics in local SQLite database.</p>
            </div>
          </div>
          <button 
            onClick={() => setShowMfgForm(!showMfgForm)}
            className="flex items-center gap-2 text-xs font-semibold px-3 py-2 bg-violet-600 hover:bg-violet-500 text-white rounded-lg transition-colors border border-violet-500/30 cursor-pointer"
          >
            <Plus size={14} />
            <span>Add Manufacturer</span>
          </button>
        </div>

        {/* Manufacturer Addition Form */}
        {showMfgForm && (
          <form onSubmit={handleAddMfg} className="p-4 bg-slate-900 border border-violet-500/30 rounded-xl space-y-4 animate-in fade-in slide-in-from-top-4 duration-200">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold text-white">Add Component Manufacturer</h3>
              <button type="button" onClick={() => setShowMfgForm(false)} className="text-slate-400 hover:text-white text-xs cursor-pointer">Cancel</button>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs text-slate-400 mb-1">Manufacturer Name <span className="text-red-500">*</span></label>
                <input 
                  type="text" 
                  value={newMfgName} 
                  onChange={(e) => setNewMfgName(e.target.value)}
                  placeholder="e.g. Infineon, Wolfspeed, TDK"
                  className="w-full bg-slate-950 border border-slate-800 text-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-violet-500"
                  required
                />
              </div>
              <div>
                <label className="block text-xs text-slate-400 mb-1">Website URL (Optional)</label>
                <input 
                  type="text" 
                  value={newMfgUrl} 
                  onChange={(e) => setNewMfgUrl(e.target.value)}
                  placeholder="https://..."
                  className="w-full bg-slate-950 border border-slate-800 text-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-violet-500"
                />
              </div>
            </div>
            <button type="submit" className="text-xs font-semibold px-4 py-2 bg-violet-600 hover:bg-violet-500 text-white rounded-lg transition-colors cursor-pointer">
              Confirm Add Manufacturer
            </button>
          </form>
        )}

        {/* Message Notifications */}
        {error && (
          <div className="flex items-center gap-3 p-3 bg-red-950/30 border border-red-500/30 rounded-lg text-red-400 text-xs">
            <AlertTriangle size={16} />
            <span>{error}</span>
          </div>
        )}
        {success && (
          <div className="flex items-center gap-3 p-3 bg-emerald-950/30 border border-emerald-500/30 rounded-lg text-emerald-400 text-xs">
            <Check size={16} />
            <span>{success}</span>
          </div>
        )}

        {/* Tabs list */}
        <div className="flex flex-wrap border-b border-slate-800/80 gap-1">
          <button 
            onClick={() => { setActiveTab('switches'); setError(null); setSuccess(null); }}
            className={`px-3 py-2 text-xs font-semibold border-b-2 transition-colors cursor-pointer ${activeTab === 'switches' ? 'border-violet-500 text-violet-400' : 'border-transparent text-slate-400 hover:text-slate-200'}`}
          >
            Power Switches
          </button>
          <button 
            onClick={() => { setActiveTab('diodes'); setError(null); setSuccess(null); }}
            className={`px-3 py-2 text-xs font-semibold border-b-2 transition-colors cursor-pointer ${activeTab === 'diodes' ? 'border-violet-500 text-violet-400' : 'border-transparent text-slate-400 hover:text-slate-200'}`}
          >
            Diodes
          </button>
          <button 
            onClick={() => { setActiveTab('zeners'); setError(null); setSuccess(null); }}
            className={`px-3 py-2 text-xs font-semibold border-b-2 transition-colors cursor-pointer ${activeTab === 'zeners' ? 'border-violet-500 text-violet-400' : 'border-transparent text-slate-400 hover:text-slate-200'}`}
          >
            Zener Diodes
          </button>
          <button 
            onClick={() => { setActiveTab('tvs'); setError(null); setSuccess(null); }}
            className={`px-3 py-2 text-xs font-semibold border-b-2 transition-colors cursor-pointer ${activeTab === 'tvs' ? 'border-violet-500 text-violet-400' : 'border-transparent text-slate-400 hover:text-slate-200'}`}
          >
            TVS Diodes
          </button>
          <button 
            onClick={() => { setActiveTab('capacitors'); setError(null); setSuccess(null); }}
            className={`px-3 py-2 text-xs font-semibold border-b-2 transition-colors cursor-pointer ${activeTab === 'capacitors' ? 'border-violet-500 text-violet-400' : 'border-transparent text-slate-400 hover:text-slate-200'}`}
          >
            Capacitors
          </button>
          <button 
            onClick={() => { setActiveTab('fuses'); setError(null); setSuccess(null); }}
            className={`px-3 py-2 text-xs font-semibold border-b-2 transition-colors cursor-pointer ${activeTab === 'fuses' ? 'border-violet-500 text-violet-400' : 'border-transparent text-slate-400 hover:text-slate-200'}`}
          >
            Fuses
          </button>
          <button 
            onClick={() => { setActiveTab('ntcs'); setError(null); setSuccess(null); }}
            className={`px-3 py-2 text-xs font-semibold border-b-2 transition-colors cursor-pointer ${activeTab === 'ntcs' ? 'border-violet-500 text-violet-400' : 'border-transparent text-slate-400 hover:text-slate-200'}`}
          >
            NTC Thermistors
          </button>
          <button 
            onClick={() => { setActiveTab('materials'); setError(null); setSuccess(null); }}
            className={`px-3 py-2 text-xs font-semibold border-b-2 transition-colors cursor-pointer ${activeTab === 'materials' ? 'border-violet-500 text-violet-400' : 'border-transparent text-slate-400 hover:text-slate-200'}`}
          >
            Core Materials
          </button>
          <button 
            onClick={() => { setActiveTab('cores'); setError(null); setSuccess(null); }}
            className={`px-3 py-2 text-xs font-semibold border-b-2 transition-colors cursor-pointer ${activeTab === 'cores' ? 'border-violet-500 text-violet-400' : 'border-transparent text-slate-400 hover:text-slate-200'}`}
          >
            Core Geometries
          </button>
        </div>

        {/* AI Datasheet Import Guide */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 flex flex-col md:flex-row md:items-center justify-between gap-4 backdrop-blur-md mb-4 mt-2">
          <div className="space-y-1">
            <h4 className="text-xs font-bold text-cyan-400 flex items-center gap-1.5">
              <span>🤖 AI Assistant Datasheet Import Guide</span>
              <span className="text-[10px] bg-cyan-950/40 text-cyan-300 px-2 py-0.5 rounded-full border border-cyan-800/30">Human-AI Collab</span>
            </h4>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              Place component datasheet PDFs into the <code className="bg-slate-950 px-1 py-0.5 rounded text-slate-200">Datasheets_Import</code> folder in the repository root, then copy the prompt on the right into chat.
              <span className="text-violet-400 font-medium ml-1">For new component types (opamps, crystals, transformers), AI will automatically extract parameters and expand tables dynamically.</span>
            </p>
          </div>
          <div className="flex items-center gap-2">
            <input 
              type="text" 
              readOnly 
              value="Extract parameters from datasheets in Datasheets_Import using AI, synchronize and insert them into the local SQLite database, and remove processed PDFs."
              className="bg-slate-950 border border-slate-850 text-slate-350 rounded px-2.5 py-1.5 text-[10px] font-mono w-full md:w-[380px] focus:outline-none border-dashed"
            />
            <button 
              onClick={() => {
                navigator.clipboard.writeText("Extract parameters from datasheets in Datasheets_Import using AI, synchronize and insert them into the local SQLite database, and remove processed PDFs.");
                setSuccess("Prompt copied to clipboard! Paste and send to Antigravity.");
              }}
              className="px-3 py-1.5 text-xs font-bold bg-cyan-600 hover:bg-cyan-500 text-white rounded transition-colors border border-cyan-500/20 whitespace-nowrap cursor-pointer"
            >
              Copy Prompt
            </button>
          </div>
        </div>

        {/* DragDeck area */}
        <DragDeck
          isDesktop={isDesktop}
          leftSpan={leftSpan}
          rightSpan={rightSpan}
          leftCards={leftCards}
          rightCards={rightCards}
          draggedKey={draggedKey}
          renderCard={(key) => (
            <DragCard
              cardKey={key}
              height={cardHeights[key]}
              onDragStart={(e) => handleDragStart(e, key)}
              onDragEnter={(e) => handleDragEnter(e, key)}
              onDragEnd={handleDragEnd}
              onResizeStart={handleResizeStart}
              onHeightResizeStart={handleHeightResizeStart}
              onResetLayout={handleResetLayout}
            >
              {key === 'input' && (
                <div className="flex-1 overflow-y-auto scrollbar-thin p-4 bg-slate-900/40 border border-slate-800/80 rounded-xl backdrop-blur-md space-y-5">
                  <h3 className="text-sm font-bold text-white flex items-center gap-2">
                    <Plus size={16} className="text-violet-400" />
                    <span>Add New Component Specification</span>
                  </h3>

                  {activeTab === 'switches' && (
                    <form onSubmit={handleAddSwitch} className="space-y-4">
                      <div>
                        <label className="block text-xs text-slate-400 mb-1">Part Number <span className="text-red-500">*</span></label>
                        <input 
                          type="text" 
                          value={newSwitch.name}
                          onChange={(e) => setNewSwitch(prev => ({ ...prev, name: e.target.value }))}
                          placeholder="e.g. IMW65R048M1H"
                          className="w-full bg-slate-950 border border-slate-800 text-slate-200 rounded-lg px-3 py-2 text-xs focus:outline-none focus:border-violet-500"
                          required
                        />
                      </div>

                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <label className="block text-xs text-slate-400 mb-1">Manufacturer</label>
                          <select 
                            value={newSwitch.manufacturer_id}
                            onChange={(e) => setNewSwitch(prev => ({ ...prev, manufacturer_id: parseInt(e.target.value) }))}
                            className="w-full bg-slate-950 border border-slate-800 text-slate-200 rounded-lg px-3 py-2 text-xs focus:outline-none focus:border-violet-500"
                          >
                            {manufacturers.map(m => <option key={m.id} value={m.id}>{m.name}</option>)}
                          </select>
                        </div>
                        <div>
                          <label className="block text-xs text-slate-400 mb-1">Device Type</label>
                          <select 
                            value={newSwitch.type}
                            onChange={(e) => setNewSwitch(prev => ({ ...prev, type: e.target.value }))}
                            className="w-full bg-slate-950 border border-slate-800 text-slate-200 rounded-lg px-3 py-2 text-xs focus:outline-none focus:border-violet-500"
                          >
                            <option value="MOSFET">MOSFET (Si)</option>
                            <option value="SiC MOSFET">SiC MOSFET</option>
                            <option value="GaN HEMT">GaN HEMT</option>
                            <option value="IGBT">IGBT</option>
                          </select>
                        </div>
                      </div>

                      <div className="grid grid-cols-3 gap-2">
                        <div>
                          <label className="block text-[10px] text-slate-400 mb-1">Vds Max (V)</label>
                          <input 
                            type="number" step="any"
                            value={newSwitch.v_ds_max}
                            onChange={(e) => setNewSwitch(prev => ({ ...prev, v_ds_max: parseFloat(e.target.value) || 0 }))}
                            className="w-full bg-slate-950 border border-slate-800 text-slate-200 rounded-lg px-2 py-1.5 text-xs focus:outline-none focus:border-violet-500"
                          />
                        </div>
                        <div>
                          <label className="block text-[10px] text-slate-400 mb-1">Id Max (A)</label>
                          <input 
                            type="number" step="any"
                            value={newSwitch.i_d_max}
                            onChange={(e) => setNewSwitch(prev => ({ ...prev, i_d_max: parseFloat(e.target.value) || 0 }))}
                            className="w-full bg-slate-950 border border-slate-800 text-slate-200 rounded-lg px-2 py-1.5 text-xs focus:outline-none focus:border-violet-500"
                          />
                        </div>
                        <div>
                          <label className="block text-[10px] text-slate-400 mb-1">Rds(on) (Ω)</label>
                          <input 
                            type="number" step="any"
                            value={newSwitch.r_ds_on}
                            onChange={(e) => setNewSwitch(prev => ({ ...prev, r_ds_on: parseFloat(e.target.value) || 0 }))}
                            className="w-full bg-slate-950 border border-slate-800 text-slate-200 rounded-lg px-2 py-1.5 text-xs focus:outline-none focus:border-violet-500"
                          />
                        </div>
                      </div>

                      <div className="grid grid-cols-3 gap-2">
                        <div>
                          <label className="block text-[10px] text-slate-400 mb-1">Qg (nC)</label>
                          <input 
                            type="number" step="any"
                            value={newSwitch.q_g || ''}
                            onChange={(e) => setNewSwitch(prev => ({ ...prev, q_g: parseFloat(e.target.value) || 0 }))}
                            className="w-full bg-slate-950 border border-slate-800 text-slate-200 rounded-lg px-2 py-1.5 text-xs focus:outline-none focus:border-violet-500"
                          />
                        </div>
                        <div>
                          <label className="block text-[10px] text-slate-400 mb-1">Coss (pF)</label>
                          <input 
                            type="number" step="any"
                            value={newSwitch.c_oss || ''}
                            onChange={(e) => setNewSwitch(prev => ({ ...prev, c_oss: parseFloat(e.target.value) || 0 }))}
                            className="w-full bg-slate-950 border border-slate-800 text-slate-200 rounded-lg px-2 py-1.5 text-xs focus:outline-none focus:border-violet-500"
                          />
                        </div>
                        <div>
                          <label className="block text-[10px] text-slate-400 mb-1">Rth(j-c) (°C/W)</label>
                          <input 
                            type="number" step="any"
                            value={newSwitch.r_jc || ''}
                            onChange={(e) => setNewSwitch(prev => ({ ...prev, r_jc: parseFloat(e.target.value) || 0 }))}
                            className="w-full bg-slate-950 border border-slate-800 text-slate-200 rounded-lg px-2 py-1.5 text-xs focus:outline-none focus:border-violet-500"
                          />
                        </div>
                      </div>

                      <div>
                        <label className="block text-xs text-slate-400 mb-1">Package</label>
                        <input 
                          type="text" 
                          value={newSwitch.package}
                          onChange={(e) => setNewSwitch(prev => ({ ...prev, package: e.target.value }))}
                          placeholder="e.g. TO-247, TO-263"
                          className="w-full bg-slate-950 border border-slate-800 text-slate-200 rounded-lg px-3 py-2 text-xs focus:outline-none focus:border-violet-500"
                        />
                      </div>

                      <button type="submit" className="w-full text-xs font-semibold py-2 bg-violet-600 hover:bg-violet-500 text-white rounded-lg transition-colors border border-violet-500/20 cursor-pointer">
                        Add Switch Device
                      </button>
                    </form>
                  )}

                  {activeTab === 'diodes' && (
                    <form onSubmit={handleAddDiode} className="space-y-4">
                      <div>
                        <label className="block text-xs text-slate-400 mb-1">Diode Part Number <span className="text-red-500">*</span></label>
                        <input 
                          type="text" 
                          value={newDiode.name}
                          onChange={(e) => setNewDiode(prev => ({ ...prev, name: e.target.value }))}
                          placeholder="e.g. IDG10G65C5"
                          className="w-full bg-slate-950 border border-slate-800 text-slate-200 rounded-lg px-3 py-2 text-xs focus:outline-none focus:border-violet-500"
                          required
                        />
                      </div>

                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <label className="block text-xs text-slate-400 mb-1">Manufacturer</label>
                          <select 
                            value={newDiode.manufacturer_id}
                            onChange={(e) => setNewDiode(prev => ({ ...prev, manufacturer_id: parseInt(e.target.value) }))}
                            className="w-full bg-slate-950 border border-slate-800 text-slate-200 rounded-lg px-3 py-2 text-xs focus:outline-none focus:border-violet-500"
                          >
                            {manufacturers.map(m => <option key={m.id} value={m.id}>{m.name}</option>)}
                          </select>
                        </div>
                        <div>
                          <label className="block text-xs text-slate-400 mb-1">Device Type</label>
                          <select 
                            value={newDiode.type}
                            onChange={(e) => setNewDiode(prev => ({ ...prev, type: e.target.value }))}
                            className="w-full bg-slate-950 border border-slate-800 text-slate-200 rounded-lg px-3 py-2 text-xs focus:outline-none focus:border-violet-500"
                          >
                            <option value="Schottky">Schottky Diode</option>
                            <option value="SiC Schottky">SiC Schottky Diode</option>
                            <option value="FRD">Fast Recovery Diode (FRD)</option>
                            <option value="Standard">Standard Rectifier</option>
                          </select>
                        </div>
                      </div>

                      <div className="grid grid-cols-3 gap-2">
                        <div>
                          <label className="block text-[10px] text-slate-400 mb-1">Reverse Vr (V)</label>
                          <input 
                            type="number" step="any"
                            value={newDiode.v_r_max}
                            onChange={(e) => setNewDiode(prev => ({ ...prev, v_r_max: parseFloat(e.target.value) || 0 }))}
                            className="w-full bg-slate-950 border border-slate-800 text-slate-200 rounded-lg px-2 py-1.5 text-xs focus:outline-none focus:border-violet-500"
                          />
                        </div>
                        <div>
                          <label className="block text-[10px] text-slate-400 mb-1">Forward If (A)</label>
                          <input 
                            type="number" step="any"
                            value={newDiode.i_f_max}
                            onChange={(e) => setNewDiode(prev => ({ ...prev, i_f_max: parseFloat(e.target.value) || 0 }))}
                            className="w-full bg-slate-950 border border-slate-800 text-slate-200 rounded-lg px-2 py-1.5 text-xs focus:outline-none focus:border-violet-500"
                          />
                        </div>
                        <div>
                          <label className="block text-[10px] text-slate-400 mb-1">Forward Drop Vf (V)</label>
                          <input 
                            type="number" step="any"
                            value={newDiode.v_f}
                            onChange={(e) => setNewDiode(prev => ({ ...prev, v_f: parseFloat(e.target.value) || 0 }))}
                            className="w-full bg-slate-950 border border-slate-800 text-slate-200 rounded-lg px-2 py-1.5 text-xs focus:outline-none focus:border-violet-500"
                          />
                        </div>
                      </div>

                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <label className="block text-xs text-slate-400 mb-1">Thermal Rth(j-c) (°C/W)</label>
                          <input 
                            type="number" step="any"
                            value={newDiode.r_jc || ''}
                            onChange={(e) => setNewDiode(prev => ({ ...prev, r_jc: parseFloat(e.target.value) || 0 }))}
                            className="w-full bg-slate-950 border border-slate-800 text-slate-200 rounded-lg px-3 py-2 text-xs focus:outline-none focus:border-violet-500"
                          />
                        </div>
                        <div>
                          <label className="block text-xs text-slate-400 mb-1">Package</label>
                          <input 
                            type="text" 
                            value={newDiode.package}
                            onChange={(e) => setNewDiode(prev => ({ ...prev, package: e.target.value }))}
                            className="w-full bg-slate-950 border border-slate-800 text-slate-200 rounded-lg px-3 py-2 text-xs focus:outline-none focus:border-violet-500"
                          />
                        </div>
                      </div>

                      <button type="submit" className="w-full text-xs font-semibold py-2 bg-violet-600 hover:bg-violet-500 text-white rounded-lg transition-colors border border-violet-500/20 cursor-pointer">
                        Add Diode Device
                      </button>
                    </form>
                  )}

                  {activeTab === 'zeners' && (
                    <form onSubmit={handleAddZener} className="space-y-4">
                      <div>
                        <label className="block text-xs text-slate-400 mb-1">Zener Part Number <span className="text-red-500">*</span></label>
                        <input 
                          type="text" 
                          value={newZener.name}
                          onChange={(e) => setNewZener(prev => ({ ...prev, name: e.target.value }))}
                          placeholder="e.g. BZX84C-5V1"
                          className="w-full bg-slate-950 border border-slate-800 text-slate-200 rounded-lg px-3 py-2 text-xs focus:outline-none"
                          required
                        />
                      </div>
                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <label className="block text-xs text-slate-400 mb-1">Manufacturer</label>
                          <select 
                            value={newZener.manufacturer_id}
                            onChange={(e) => setNewZener(prev => ({ ...prev, manufacturer_id: parseInt(e.target.value) }))}
                            className="w-full bg-slate-950 border border-slate-800 text-slate-200 rounded-lg px-3 py-2 text-xs"
                          >
                            {manufacturers.map(m => <option key={m.id} value={m.id}>{m.name}</option>)}
                          </select>
                        </div>
                        <div>
                          <label className="block text-xs text-slate-400 mb-1">Zener Voltage Vz (V)</label>
                          <input 
                            type="number" step="any"
                            value={newZener.vz}
                            onChange={(e) => setNewZener(prev => ({ ...prev, vz: parseFloat(e.target.value) || 0 }))}
                            className="w-full bg-slate-950 border border-slate-800 text-slate-200 rounded-lg px-3 py-2 text-xs"
                          />
                        </div>
                      </div>
                      <div className="grid grid-cols-3 gap-2">
                        <div>
                          <label className="block text-[10px] text-slate-400 mb-1">Test Current Izt (mA)</label>
                          <input 
                            type="number" step="any"
                            value={newZener.izt}
                            onChange={(e) => setNewZener(prev => ({ ...prev, izt: parseFloat(e.target.value) || 0 }))}
                            className="w-full bg-slate-950 border border-slate-800 text-slate-200 rounded-lg px-2 py-1.5 text-xs"
                          />
                        </div>
                        <div>
                          <label className="block text-[10px] text-slate-400 mb-1">Knee Current Izk (mA)</label>
                          <input 
                            type="number" step="any"
                            value={newZener.izk}
                            onChange={(e) => setNewZener(prev => ({ ...prev, izk: parseFloat(e.target.value) || 0 }))}
                            className="w-full bg-slate-950 border border-slate-800 text-slate-200 rounded-lg px-2 py-1.5 text-xs"
                          />
                        </div>
                        <div>
                          <label className="block text-[10px] text-slate-400 mb-1">Impedance Zzt (Ω)</label>
                          <input 
                            type="number" step="any"
                            value={newZener.zzt}
                            onChange={(e) => setNewZener(prev => ({ ...prev, zzt: parseFloat(e.target.value) || 0 }))}
                            className="w-full bg-slate-950 border border-slate-800 text-slate-200 rounded-lg px-2 py-1.5 text-xs"
                          />
                        </div>
                      </div>
                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <label className="block text-xs text-slate-400 mb-1">Rated Power Pd (W)</label>
                          <input 
                            type="number" step="any"
                            value={newZener.p_d}
                            onChange={(e) => setNewZener(prev => ({ ...prev, p_d: parseFloat(e.target.value) || 0 }))}
                            className="w-full bg-slate-950 border border-slate-800 text-slate-200 rounded-lg px-3 py-2 text-xs"
                          />
                        </div>
                        <div>
                          <label className="block text-xs text-slate-400 mb-1">Package</label>
                          <input 
                            type="text" 
                            value={newZener.package}
                            onChange={(e) => setNewZener(prev => ({ ...prev, package: e.target.value }))}
                            className="w-full bg-slate-950 border border-slate-800 text-slate-200 rounded-lg px-3 py-2 text-xs"
                          />
                        </div>
                      </div>
                      <button type="submit" className="w-full text-xs font-semibold py-2 bg-violet-600 hover:bg-violet-500 text-white rounded-lg border border-violet-500/20 cursor-pointer">
                        Add Zener Diode
                      </button>
                    </form>
                  )}

                  {activeTab === 'tvs' && (
                    <form onSubmit={handleAddTvs} className="space-y-4">
                      <div>
                        <label className="block text-xs text-slate-400 mb-1">TVS Part Number <span className="text-red-500">*</span></label>
                        <input 
                          type="text" 
                          value={newTvs.name}
                          onChange={(e) => setNewTvs(prev => ({ ...prev, name: e.target.value }))}
                          placeholder="e.g. SMAJ24CA"
                          className="w-full bg-slate-950 border border-slate-800 text-slate-200 rounded-lg px-3 py-2 text-xs"
                          required
                        />
                      </div>
                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <label className="block text-xs text-slate-400 mb-1">Manufacturer</label>
                          <select 
                            value={newTvs.manufacturer_id}
                            onChange={(e) => setNewTvs(prev => ({ ...prev, manufacturer_id: parseInt(e.target.value) }))}
                            className="w-full bg-slate-950 border border-slate-800 text-slate-200 rounded-lg px-3 py-2 text-xs"
                          >
                            {manufacturers.map(m => <option key={m.id} value={m.id}>{m.name}</option>)}
                          </select>
                        </div>
                        <div>
                          <label className="block text-xs text-slate-400 mb-1">Standoff VRWM (V)</label>
                          <input 
                            type="number" step="any"
                            value={newTvs.vrwm}
                            onChange={(e) => setNewTvs(prev => ({ ...prev, vrwm: parseFloat(e.target.value) || 0 }))}
                            className="w-full bg-slate-950 border border-slate-800 text-slate-200 rounded-lg px-3 py-2 text-xs"
                          />
                        </div>
                      </div>
                      <div className="grid grid-cols-3 gap-2">
                        <div>
                          <label className="block text-[10px] text-slate-400 mb-1">Breakdown Vbr (V)</label>
                          <input 
                            type="number" step="any"
                            value={newTvs.vbr}
                            onChange={(e) => setNewTvs(prev => ({ ...prev, vbr: parseFloat(e.target.value) || 0 }))}
                            className="w-full bg-slate-950 border border-slate-800 text-slate-200 rounded-lg px-2 py-1.5 text-xs"
                          />
                        </div>
                        <div>
                          <label className="block text-[10px] text-slate-400 mb-1">Clamping Vc (V)</label>
                          <input 
                            type="number" step="any"
                            value={newTvs.vc}
                            onChange={(e) => setNewTvs(prev => ({ ...prev, vc: parseFloat(e.target.value) || 0 }))}
                            className="w-full bg-slate-950 border border-slate-800 text-slate-200 rounded-lg px-2 py-1.5 text-xs"
                          />
                        </div>
                        <div>
                          <label className="block text-[10px] text-slate-400 mb-1">Pulse Current Ipp (A)</label>
                          <input 
                            type="number" step="any"
                            value={newTvs.ipp}
                            onChange={(e) => setNewTvs(prev => ({ ...prev, ipp: parseFloat(e.target.value) || 0 }))}
                            className="w-full bg-slate-950 border border-slate-800 text-slate-200 rounded-lg px-2 py-1.5 text-xs"
                          />
                        </div>
                      </div>
                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <label className="block text-xs text-slate-400 mb-1">Pulse Power Pppm (W)</label>
                          <input 
                            type="number" step="any"
                            value={newTvs.pppm}
                            onChange={(e) => setNewTvs(prev => ({ ...prev, pppm: parseFloat(e.target.value) || 0 }))}
                            className="w-full bg-slate-950 border border-slate-800 text-slate-200 rounded-lg px-3 py-2 text-xs"
                          />
                        </div>
                        <div>
                          <label className="block text-xs text-slate-400 mb-1">Package</label>
                          <input 
                            type="text" 
                            value={newTvs.package}
                            onChange={(e) => setNewTvs(prev => ({ ...prev, package: e.target.value }))}
                            className="w-full bg-slate-950 border border-slate-800 text-slate-200 rounded-lg px-3 py-2 text-xs"
                          />
                        </div>
                      </div>
                      <button type="submit" className="w-full text-xs font-semibold py-2 bg-violet-600 hover:bg-violet-500 text-white rounded-lg border border-violet-500/20 cursor-pointer">
                        Add TVS Diode
                      </button>
                    </form>
                  )}

                  {activeTab === 'capacitors' && (
                    <form onSubmit={handleAddCapacitor} className="space-y-4">
                      <div>
                        <label className="block text-xs text-slate-400 mb-1">Capacitor Part Number <span className="text-red-500">*</span></label>
                        <input 
                          type="text" 
                          value={newCap.name}
                          onChange={(e) => setNewCap(prev => ({ ...prev, name: e.target.value }))}
                          placeholder="e.g. EKY-500ELL471MJ20S"
                          className="w-full bg-slate-950 border border-slate-800 text-slate-200 rounded-lg px-3 py-2 text-xs"
                          required
                        />
                      </div>
                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <label className="block text-xs text-slate-400 mb-1">Manufacturer</label>
                          <select 
                            value={newCap.manufacturer_id}
                            onChange={(e) => setNewCap(prev => ({ ...prev, manufacturer_id: parseInt(e.target.value) }))}
                            className="w-full bg-slate-950 border border-slate-800 text-slate-200 rounded-lg px-3 py-2 text-xs"
                          >
                            {manufacturers.map(m => <option key={m.id} value={m.id}>{m.name}</option>)}
                          </select>
                        </div>
                        <div>
                          <label className="block text-xs text-slate-400 mb-1">Capacitor Type</label>
                          <select 
                            value={newCap.type}
                            onChange={(e) => setNewCap(prev => ({ ...prev, type: e.target.value }))}
                            className="w-full bg-slate-950 border border-slate-800 text-slate-200 rounded-lg px-3 py-2 text-xs"
                          >
                            <option value="Electrolytic">Aluminum Electrolytic</option>
                            <option value="Film">Film Capacitor</option>
                            <option value="MLCC">MLCC Ceramic</option>
                          </select>
                        </div>
                      </div>
                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <label className="block text-xs text-slate-400 mb-1">Capacitance (F)</label>
                          <input 
                            type="number" step="any"
                            value={newCap.capacitance}
                            onChange={(e) => setNewCap(prev => ({ ...prev, capacitance: parseFloat(e.target.value) || 0 }))}
                            className="w-full bg-slate-950 border border-slate-800 text-slate-200 rounded-lg px-3 py-2 text-xs"
                          />
                        </div>
                        <div>
                          <label className="block text-xs text-slate-400 mb-1">Voltage Rating (V)</label>
                          <input 
                            type="number" step="any"
                            value={newCap.voltage_rating}
                            onChange={(e) => setNewCap(prev => ({ ...prev, voltage_rating: parseFloat(e.target.value) || 0 }))}
                            className="w-full bg-slate-950 border border-slate-800 text-slate-200 rounded-lg px-3 py-2 text-xs"
                          />
                        </div>
                      </div>
                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <label className="block text-xs text-slate-400 mb-1">Equivalent ESR (Ω)</label>
                          <input 
                            type="number" step="any"
                            value={newCap.esr}
                            onChange={(e) => setNewCap(prev => ({ ...prev, esr: parseFloat(e.target.value) || 0 }))}
                            className="w-full bg-slate-950 border border-slate-800 text-slate-200 rounded-lg px-3 py-2 text-xs"
                          />
                        </div>
                        <div>
                          <label className="block text-xs text-slate-400 mb-1">Ripple Current (A)</label>
                          <input 
                            type="number" step="any"
                            value={newCap.ripple_current}
                            onChange={(e) => setNewCap(prev => ({ ...prev, ripple_current: parseFloat(e.target.value) || 0 }))}
                            className="w-full bg-slate-950 border border-slate-800 text-slate-200 rounded-lg px-3 py-2 text-xs"
                          />
                        </div>
                      </div>
                      <button type="submit" className="w-full text-xs font-semibold py-2 bg-violet-600 hover:bg-violet-500 text-white rounded-lg border border-violet-500/20 cursor-pointer">
                        Add Capacitor
                      </button>
                    </form>
                  )}

                  {activeTab === 'fuses' && (
                    <form onSubmit={handleAddFuse} className="space-y-4">
                      <div>
                        <label className="block text-xs text-slate-400 mb-1">Fuse Part Number <span className="text-red-500">*</span></label>
                        <input 
                          type="text" 
                          value={newFuse.name}
                          onChange={(e) => setNewFuse(prev => ({ ...prev, name: e.target.value }))}
                          placeholder="e.g. 0451005.MRL"
                          className="w-full bg-slate-950 border border-slate-800 text-slate-200 rounded-lg px-3 py-2 text-xs"
                          required
                        />
                      </div>
                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <label className="block text-xs text-slate-400 mb-1">Manufacturer</label>
                          <select 
                            value={newFuse.manufacturer_id}
                            onChange={(e) => setNewFuse(prev => ({ ...prev, manufacturer_id: parseInt(e.target.value) }))}
                            className="w-full bg-slate-950 border border-slate-800 text-slate-200 rounded-lg px-3 py-2 text-xs"
                          >
                            {manufacturers.map(m => <option key={m.id} value={m.id}>{m.name}</option>)}
                          </select>
                        </div>
                        <div>
                          <label className="block text-xs text-slate-400 mb-1">Rated Current (A)</label>
                          <input 
                            type="number" step="any"
                            value={newFuse.i_rated}
                            onChange={(e) => setNewFuse(prev => ({ ...prev, i_rated: parseFloat(e.target.value) || 0 }))}
                            className="w-full bg-slate-950 border border-slate-800 text-slate-200 rounded-lg px-3 py-2 text-xs"
                          />
                        </div>
                      </div>
                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <label className="block text-xs text-slate-400 mb-1">Melting I²t (A²s)</label>
                          <input 
                            type="number" step="any"
                            value={newFuse.i2t}
                            onChange={(e) => setNewFuse(prev => ({ ...prev, i2t: parseFloat(e.target.value) || 0 }))}
                            className="w-full bg-slate-950 border border-slate-800 text-slate-200 rounded-lg px-3 py-2 text-xs"
                          />
                        </div>
                        <div>
                          <label className="block text-xs text-slate-400 mb-1">Rated Voltage (V)</label>
                          <input 
                            type="number" step="any"
                            value={newFuse.v_rated}
                            onChange={(e) => setNewFuse(prev => ({ ...prev, v_rated: parseFloat(e.target.value) || 0 }))}
                            className="w-full bg-slate-950 border border-slate-800 text-slate-200 rounded-lg px-3 py-2 text-xs"
                          />
                        </div>
                      </div>
                      <button type="submit" className="w-full text-xs font-semibold py-2 bg-violet-600 hover:bg-violet-500 text-white rounded-lg border border-violet-500/20 cursor-pointer">
                        Add Fuse
                      </button>
                    </form>
                  )}

                  {activeTab === 'ntcs' && (
                    <form onSubmit={handleAddNtc} className="space-y-4">
                      <div>
                        <label className="block text-xs text-slate-400 mb-1">NTC Thermistor Part Number <span className="text-red-500">*</span></label>
                        <input 
                          type="text" 
                          value={newNtc.name}
                          onChange={(e) => setNewNtc(prev => ({ ...prev, name: e.target.value }))}
                          placeholder="e.g. MF72-10D11"
                          className="w-full bg-slate-950 border border-slate-800 text-slate-200 rounded-lg px-3 py-2 text-xs"
                          required
                        />
                      </div>
                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <label className="block text-xs text-slate-400 mb-1">Manufacturer</label>
                          <select 
                            value={newNtc.manufacturer_id}
                            onChange={(e) => setNewNtc(prev => ({ ...prev, manufacturer_id: parseInt(e.target.value) }))}
                            className="w-full bg-slate-950 border border-slate-800 text-slate-200 rounded-lg px-3 py-2 text-xs"
                          >
                            {manufacturers.map(m => <option key={m.id} value={m.id}>{m.name}</option>)}
                          </select>
                        </div>
                        <div>
                          <label className="block text-xs text-slate-400 mb-1">Zero-Power Res R25 (Ω)</label>
                          <input 
                            type="number" step="any"
                            value={newNtc.r25}
                            onChange={(e) => setNewNtc(prev => ({ ...prev, r25: parseFloat(e.target.value) || 0 }))}
                            className="w-full bg-slate-950 border border-slate-800 text-slate-200 rounded-lg px-3 py-2 text-xs"
                          />
                        </div>
                      </div>
                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <label className="block text-xs text-slate-400 mb-1">Max Current Imax (A)</label>
                          <input 
                            type="number" step="any"
                            value={newNtc.i_max}
                            onChange={(e) => setNewNtc(prev => ({ ...prev, i_max: parseFloat(e.target.value) || 0 }))}
                            className="w-full bg-slate-950 border border-slate-800 text-slate-200 rounded-lg px-3 py-2 text-xs"
                          />
                        </div>
                        <div>
                          <label className="block text-xs text-slate-400 mb-1">Max Energy Joule (J)</label>
                          <input 
                            type="number" step="any"
                            value={newNtc.joule_rating}
                            onChange={(e) => setNewNtc(prev => ({ ...prev, joule_rating: parseFloat(e.target.value) || 0 }))}
                            className="w-full bg-slate-950 border border-slate-800 text-slate-200 rounded-lg px-3 py-2 text-xs"
                          />
                        </div>
                      </div>
                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <label className="block text-xs text-slate-400 mb-1">Dissipation Constant (mW/°C)</label>
                          <input 
                            type="number" step="any"
                            value={newNtc.dissipation}
                            onChange={(e) => setNewNtc(prev => ({ ...prev, dissipation: parseFloat(e.target.value) || 0 }))}
                            className="w-full bg-slate-950 border border-slate-800 text-slate-200 rounded-lg px-3 py-2 text-xs"
                          />
                        </div>
                        <div>
                          <label className="block text-xs text-slate-400 mb-1">Package</label>
                          <input 
                            type="text" 
                            value={newNtc.package}
                            onChange={(e) => setNewNtc(prev => ({ ...prev, package: e.target.value }))}
                            className="w-full bg-slate-950 border border-slate-800 text-slate-200 rounded-lg px-3 py-2 text-xs"
                          />
                        </div>
                      </div>
                      <button type="submit" className="w-full text-xs font-semibold py-2 bg-violet-600 hover:bg-violet-500 text-white rounded-lg border border-violet-500/20 cursor-pointer">
                        Add NTC Thermistor
                      </button>
                    </form>
                  )}

                  {activeTab === 'materials' && (
                    <form onSubmit={handleAddMaterial} className="space-y-4">
                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <label className="block text-xs text-slate-400 mb-1">Material Name <span className="text-red-500">*</span></label>
                          <input 
                            type="text" 
                            value={newMaterial.name}
                            onChange={(e) => setNewMaterial(prev => ({ ...prev, name: e.target.value }))}
                            placeholder="e.g. PC40, N87"
                            className="w-full bg-slate-950 border border-slate-800 text-slate-200 rounded-lg px-3 py-2 text-xs focus:outline-none focus:border-violet-500"
                            required
                          />
                        </div>
                        <div>
                          <label className="block text-xs text-slate-400 mb-1">Material Family</label>
                          <select 
                            value={newMaterial.type}
                            onChange={(e) => setNewMaterial(prev => ({ ...prev, type: e.target.value }))}
                            className="w-full bg-slate-950 border border-slate-800 text-slate-200 rounded-lg px-3 py-2 text-xs focus:outline-none focus:border-violet-500"
                          >
                            <option value="Ferrite">MnZn Ferrite</option>
                            <option value="Metal Dust">Metal Powder Core</option>
                            <option value="Amorphous">Amorphous / Nanocrystalline</option>
                          </select>
                        </div>
                      </div>

                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <label className="block text-xs text-slate-400 mb-1">Permeability μi</label>
                          <input 
                            type="number" step="any"
                            value={newMaterial.permeability}
                            onChange={(e) => setNewMaterial(prev => ({ ...prev, permeability: parseFloat(e.target.value) || 0 }))}
                            className="w-full bg-slate-950 border border-slate-800 text-slate-200 rounded-lg px-3 py-2 text-xs focus:outline-none focus:border-violet-500"
                          />
                        </div>
                      </div>

                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <label className="block text-xs text-slate-400 mb-1">Bsat @25°C (T)</label>
                          <input 
                            type="number" step="any"
                            value={newMaterial.b_sat_25}
                            onChange={(e) => setNewMaterial(prev => ({ ...prev, b_sat_25: parseFloat(e.target.value) || 0 }))}
                            className="w-full bg-slate-950 border border-slate-800 text-slate-200 rounded-lg px-3 py-2 text-xs focus:outline-none focus:border-violet-500"
                          />
                        </div>
                        <div>
                          <label className="block text-xs text-slate-400 mb-1">Bsat @100°C (T)</label>
                          <input 
                            type="number" step="any"
                            value={newMaterial.b_sat_100}
                            onChange={(e) => setNewMaterial(prev => ({ ...prev, b_sat_100: parseFloat(e.target.value) || 0 }))}
                            className="w-full bg-slate-950 border border-slate-800 text-slate-200 rounded-lg px-3 py-2 text-xs focus:outline-none focus:border-violet-500"
                          />
                        </div>
                      </div>

                      {/* Steinmetz parameters */}
                      <div className="p-3 bg-slate-950/60 border border-slate-850 rounded-lg space-y-3">
                        <div className="text-[10px] font-bold text-violet-400 tracking-wider">STEINMETZ LOSS PARAMETERS @100°C</div>
                        <div className="grid grid-cols-3 gap-2">
                          <div>
                            <label className="block text-[9px] text-slate-500 mb-0.5">Cm</label>
                            <input 
                              type="number" step="any"
                              value={newMaterial.steinmetz_cm_100}
                              onChange={(e) => setNewMaterial(prev => ({ ...prev, steinmetz_cm_100: parseFloat(e.target.value) || 0 }))}
                              className="w-full bg-slate-900 border border-slate-800 text-slate-200 rounded px-1.5 py-1 text-xs focus:outline-none"
                            />
                          </div>
                          <div>
                            <label className="block text-[9px] text-slate-500 mb-0.5">x (Freq Exponent)</label>
                            <input 
                              type="number" step="any"
                              value={newMaterial.steinmetz_x_100}
                              onChange={(e) => setNewMaterial(prev => ({ ...prev, steinmetz_x_100: parseFloat(e.target.value) || 0 }))}
                              className="w-full bg-slate-900 border border-slate-800 text-slate-200 rounded px-1.5 py-1 text-xs focus:outline-none"
                            />
                          </div>
                          <div>
                            <label className="block text-[9px] text-slate-500 mb-0.5">y (Flux Exponent)</label>
                            <input 
                              type="number" step="any"
                              value={newMaterial.steinmetz_y_100}
                              onChange={(e) => setNewMaterial(prev => ({ ...prev, steinmetz_y_100: parseFloat(e.target.value) || 0 }))}
                              className="w-full bg-slate-900 border border-slate-800 text-slate-200 rounded px-1.5 py-1 text-xs focus:outline-none"
                            />
                          </div>
                        </div>
                      </div>

                      <button type="submit" className="w-full text-xs font-semibold py-2 bg-violet-600 hover:bg-violet-500 text-white rounded-lg transition-colors border border-violet-500/20 cursor-pointer">
                        Add Material
                      </button>
                    </form>
                  )}

                  {activeTab === 'cores' && (
                    <form onSubmit={handleAddCore} className="space-y-4">
                      <div>
                        <label className="block text-xs text-slate-400 mb-1">Core Name <span className="text-red-500">*</span></label>
                        <input 
                          type="text" 
                          value={newCore.name}
                          onChange={(e) => setNewCore(prev => ({ ...prev, name: e.target.value }))}
                          placeholder="e.g. PQ32/30, EE25/13/7"
                          className="w-full bg-slate-950 border border-slate-800 text-slate-200 rounded-lg px-3 py-2 text-xs focus:outline-none focus:border-violet-500"
                          required
                        />
                      </div>

                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <label className="block text-xs text-slate-400 mb-1">Shape Category</label>
                          <select 
                            value={newCore.shape}
                            onChange={(e) => setNewCore(prev => ({ ...prev, shape: e.target.value }))}
                            className="w-full bg-slate-950 border border-slate-800 text-slate-200 rounded-lg px-3 py-2 text-xs focus:outline-none focus:border-violet-500"
                          >
                            <option value="EE">EE Core</option>
                            <option value="PQ">PQ Core</option>
                            <option value="RM">RM Core</option>
                            <option value="EFD">EFD Core</option>
                            <option value="EI">EI Core</option>
                            <option value="Toroid">Toroid Core</option>
                          </select>
                        </div>
                        <div>
                          <label className="block text-xs text-slate-400 mb-1">Linked Material</label>
                          <select 
                            value={newCore.material_id}
                            onChange={(e) => setNewCore(prev => ({ ...prev, material_id: parseInt(e.target.value) }))}
                            className="w-full bg-slate-950 border border-slate-800 text-slate-200 rounded-lg px-3 py-2 text-xs focus:outline-none focus:border-violet-500"
                          >
                            {materials.map(m => <option key={m.id} value={m.id}>{m.name}</option>)}
                          </select>
                        </div>
                      </div>

                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <label className="block text-xs text-slate-400 mb-1">Effective Area Ae (mm²)</label>
                          <input 
                            type="number" step="any"
                            value={newCore.ae}
                            onChange={(e) => setNewCore(prev => ({ ...prev, ae: parseFloat(e.target.value) || 0 }))}
                            className="w-full bg-slate-950 border border-slate-800 text-slate-200 rounded-lg px-3 py-2 text-xs focus:outline-none focus:border-violet-500"
                          />
                        </div>
                        <div>
                          <label className="block text-xs text-slate-400 mb-1">Path Length Le (mm)</label>
                          <input 
                            type="number" step="any"
                            value={newCore.le}
                            onChange={(e) => setNewCore(prev => ({ ...prev, le: parseFloat(e.target.value) || 0 }))}
                            className="w-full bg-slate-950 border border-slate-800 text-slate-200 rounded-lg px-3 py-2 text-xs focus:outline-none focus:border-violet-500"
                          />
                        </div>
                      </div>

                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <label className="block text-xs text-slate-400 mb-1">Effective Volume Ve (mm³)</label>
                          <input 
                            type="number" step="any"
                            value={newCore.ve}
                            onChange={(e) => setNewCore(prev => ({ ...prev, ve: parseFloat(e.target.value) || 0 }))}
                            className="w-full bg-slate-950 border border-slate-800 text-slate-200 rounded-lg px-3 py-2 text-xs focus:outline-none focus:border-violet-500"
                          />
                        </div>
                        <div>
                          <label className="block text-xs text-slate-400 mb-1">Window Area Wa (mm²)</label>
                          <input 
                            type="number" step="any"
                            value={newCore.wa}
                            onChange={(e) => setNewCore(prev => ({ ...prev, wa: parseFloat(e.target.value) || 0 }))}
                            className="w-full bg-slate-950 border border-slate-800 text-slate-200 rounded-lg px-3 py-2 text-xs focus:outline-none focus:border-violet-500"
                          />
                        </div>
                      </div>

                      <div>
                        <label className="block text-xs text-slate-400 mb-1">Inductance Factor Al (nH/N²)</label>
                        <input 
                          type="number" step="any"
                          value={newCore.al || ''}
                          onChange={(e) => setNewCore(prev => ({ ...prev, al: parseFloat(e.target.value) || 0 }))}
                          placeholder="Optional"
                          className="w-full bg-slate-950 border border-slate-800 text-slate-200 rounded-lg px-3 py-2 text-xs focus:outline-none focus:border-violet-500"
                        />
                      </div>

                      <button type="submit" className="w-full text-xs font-semibold py-2 bg-violet-600 hover:bg-violet-500 text-white rounded-lg transition-colors border border-violet-500/20 cursor-pointer">
                        Add Core Geometry
                      </button>
                    </form>
                  )}
                </div>
              )}

              {key === 'results' && (
                <div className="flex-1 overflow-y-auto scrollbar-thin p-4 bg-slate-900/40 border border-slate-800/80 rounded-xl backdrop-blur-md flex flex-col gap-4">
                  <div className="flex items-center justify-between">
                    <h3 className="text-sm font-bold text-white flex items-center gap-2">
                      <span>Database Component Catalog</span>
                    </h3>
                  </div>

                  <div className="flex-1 overflow-auto rounded-lg border border-slate-850 bg-slate-950/20">
                    {loading ? (
                      <div className="p-12 text-center text-slate-500 text-xs">Loading...</div>
                    ) : (
                      <table className="w-full text-left border-collapse text-xs">
                        {activeTab === 'switches' && (
                          <>
                            <thead className="bg-slate-900 text-slate-400 font-semibold sticky top-0">
                              <tr>
                                <th className="p-3">Part Number</th>
                                <th className="p-3">Manufacturer</th>
                                <th className="p-3">Type</th>
                                <th className="p-3">Vds Max</th>
                                <th className="p-3">Id Max</th>
                                <th className="p-3">Rds(on)</th>
                                <th className="p-3">Qg</th>
                                <th className="p-3">Coss</th>
                                <th className="p-3">Package</th>
                                <th className="p-3 text-center">Actions</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-850 text-slate-350">
                              {switches.map((item, index) => (
                                <tr key={index} onClick={() => setSelectedSwitch(item)} className={`cursor-pointer transition-colors ${selectedSwitch?.name === item.name ? 'bg-violet-600/30 hover:bg-violet-600/40' : 'hover:bg-slate-900/40'}`}>
                                  <td className="p-3 font-semibold text-white">{item.name}</td>
                                  <td className="p-3">{item.manufacturer}</td>
                                  <td className="p-3 font-mono text-violet-300">{item.type}</td>
                                  <td className="p-3 font-mono text-emerald-300">{item.v_ds_max}V</td>
                                  <td className="p-3 font-mono text-emerald-300">{item.i_d_max}A</td>
                                  <td className="p-3 font-mono text-amber-300">{item.r_ds_on}Ω</td>
                                  <td className="p-3 font-mono">{item.q_g ? item.q_g + 'nC' : '-'}</td>
                                  <td className="p-3 font-mono">{item.c_oss ? item.c_oss + 'pF' : '-'}</td>
                                  <td className="p-3">{item.package || '-'}</td>
                                  <td className="p-3 text-center">
                                    <button 
                                      onClick={() => handleDeleteSwitch(item.name)}
                                      className="p-1 rounded text-red-400 hover:text-red-300 hover:bg-red-950/20 border-0 cursor-pointer"
                                    >
                                      <Trash2 size={14} />
                                    </button>
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </>
                        )}

                        {activeTab === 'diodes' && (
                          <>
                            <thead className="bg-slate-900 text-slate-400 font-semibold sticky top-0">
                              <tr>
                                <th className="p-3">Part Number</th>
                                <th className="p-3">Manufacturer</th>
                                <th className="p-3">Type</th>
                                <th className="p-3">Vr Max</th>
                                <th className="p-3">If Max</th>
                                <th className="p-3">Vf</th>
                                <th className="p-3">Package</th>
                                <th className="p-3 text-center">Actions</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-850 text-slate-350">
                              {diodes.map((item, index) => (
                                <tr key={index} onClick={() => setSelectedDiode(item)} className={`cursor-pointer transition-colors ${selectedDiode?.name === item.name ? 'bg-violet-600/30 hover:bg-violet-600/40' : 'hover:bg-slate-900/40'}`}>
                                  <td className="p-3 font-semibold text-white">{item.name}</td>
                                  <td className="p-3">{item.manufacturer}</td>
                                  <td className="p-3 font-mono text-violet-300">{item.type}</td>
                                  <td className="p-3 font-mono text-emerald-300">{item.v_r_max}V</td>
                                  <td className="p-3 font-mono text-emerald-300">{item.i_f_max}A</td>
                                  <td className="p-3 font-mono text-amber-300">{item.v_f}V</td>
                                  <td className="p-3">{item.package || '-'}</td>
                                  <td className="p-3 text-center">
                                    <button 
                                      onClick={() => handleDeleteDiode(item.name)}
                                      className="p-1 rounded text-red-400 hover:text-red-300 hover:bg-red-950/20 border-0 cursor-pointer"
                                    >
                                      <Trash2 size={14} />
                                    </button>
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </>
                        )}

                        {activeTab === 'zeners' && (
                          <>
                            <thead className="bg-slate-900 text-slate-400 font-semibold sticky top-0">
                              <tr>
                                <th className="p-3">Part Number</th>
                                <th className="p-3">Manufacturer</th>
                                <th className="p-3">Vz</th>
                                <th className="p-3">Izt</th>
                                <th className="p-3">Izk</th>
                                <th className="p-3">Zzt</th>
                                <th className="p-3">Pd</th>
                                <th className="p-3">Package</th>
                                <th className="p-3 text-center">Actions</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-850 text-slate-350">
                              {zeners.map((item, index) => (
                                <tr key={index} onClick={() => setSelectedZener(item)} className={`cursor-pointer transition-colors ${selectedZener?.name === item.name ? 'bg-violet-600/30 hover:bg-violet-600/40' : 'hover:bg-slate-900/40'}`}>
                                  <td className="p-3 font-semibold text-white">{item.name}</td>
                                  <td className="p-3">{item.manufacturer}</td>
                                  <td className="p-3 font-mono text-emerald-300">{item.vz}V</td>
                                  <td className="p-3 font-mono">{item.izt}mA</td>
                                  <td className="p-3 font-mono">{item.izk}mA</td>
                                  <td className="p-3 font-mono text-amber-300">{item.zzt}Ω</td>
                                  <td className="p-3 font-mono">{item.p_d}W</td>
                                  <td className="p-3">{item.package || '-'}</td>
                                  <td className="p-3 text-center">
                                    <button 
                                      onClick={(e) => { e.stopPropagation(); handleDeleteZener(item.name); }}
                                      className="p-1 rounded text-red-400 hover:text-red-300 hover:bg-red-950/20 border-0 cursor-pointer"
                                    >
                                      <Trash2 size={14} />
                                    </button>
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </>
                        )}

                        {activeTab === 'tvs' && (
                          <>
                            <thead className="bg-slate-900 text-slate-400 font-semibold sticky top-0">
                              <tr>
                                <th className="p-3">Part Number</th>
                                <th className="p-3">Manufacturer</th>
                                <th className="p-3">VRWM</th>
                                <th className="p-3">Vbr</th>
                                <th className="p-3">Vc</th>
                                <th className="p-3">Ipp</th>
                                <th className="p-3">Pppm</th>
                                <th className="p-3">Package</th>
                                <th className="p-3 text-center">Actions</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-850 text-slate-350">
                              {tvsList.map((item, index) => (
                                <tr key={index} onClick={() => setSelectedTvs(item)} className={`cursor-pointer transition-colors ${selectedTvs?.name === item.name ? 'bg-violet-600/30 hover:bg-violet-600/40' : 'hover:bg-slate-900/40'}`}>
                                  <td className="p-3 font-semibold text-white">{item.name}</td>
                                  <td className="p-3">{item.manufacturer}</td>
                                  <td className="p-3 font-mono text-emerald-300">{item.vrwm}V</td>
                                  <td className="p-3 font-mono text-emerald-300">{item.vbr}V</td>
                                  <td className="p-3 font-mono text-amber-300">{item.vc}V</td>
                                  <td className="p-3 font-mono">{item.ipp}A</td>
                                  <td className="p-3 font-mono text-cyan-300">{item.pppm}W</td>
                                  <td className="p-3">{item.package || '-'}</td>
                                  <td className="p-3 text-center">
                                    <button 
                                      onClick={(e) => { e.stopPropagation(); handleDeleteTvs(item.name); }}
                                      className="p-1 rounded text-red-400 hover:text-red-300 hover:bg-red-950/20 border-0 cursor-pointer"
                                    >
                                      <Trash2 size={14} />
                                    </button>
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </>
                        )}

                        {activeTab === 'capacitors' && (
                          <>
                            <thead className="bg-slate-900 text-slate-400 font-semibold sticky top-0">
                              <tr>
                                <th className="p-3">Part Number</th>
                                <th className="p-3">Manufacturer</th>
                                <th className="p-3">Type</th>
                                <th className="p-3">Capacitance</th>
                                <th className="p-3">Voltage</th>
                                <th className="p-3">ESR</th>
                                <th className="p-3">Ripple Current</th>
                                <th className="p-3">Lifetime (hr)</th>
                                <th className="p-3 text-center">Actions</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-850 text-slate-350">
                              {caps.map((item, index) => (
                                <tr key={index} onClick={() => setSelectedCap(item)} className={`cursor-pointer transition-colors ${selectedCap?.name === item.name ? 'bg-violet-600/30 hover:bg-violet-600/40' : 'hover:bg-slate-900/40'}`}>
                                  <td className="p-3 font-semibold text-white">{item.name}</td>
                                  <td className="p-3">{item.manufacturer}</td>
                                  <td className="p-3 text-violet-300">{item.type}</td>
                                  <td className="p-3 font-mono text-emerald-300">{(item.capacitance * 1e6).toFixed(1)}μF</td>
                                  <td className="p-3 font-mono text-emerald-300">{item.voltage_rating}V</td>
                                  <td className="p-3 font-mono text-amber-300">{item.esr ? item.esr + 'Ω' : '-'}</td>
                                  <td className="p-3 font-mono">{item.ripple_current ? item.ripple_current + 'A' : '-'}</td>
                                  <td className="p-3 font-mono">{item.lifetime_hours ? item.lifetime_hours + 'h' : '-'}</td>
                                  <td className="p-3 text-center">
                                    <button 
                                      onClick={(e) => { e.stopPropagation(); handleDeleteCapacitor(item.name); }}
                                      className="p-1 rounded text-red-400 hover:text-red-300 hover:bg-red-950/20 border-0 cursor-pointer"
                                    >
                                      <Trash2 size={14} />
                                    </button>
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </>
                        )}

                        {activeTab === 'fuses' && (
                          <>
                            <thead className="bg-slate-900 text-slate-400 font-semibold sticky top-0">
                              <tr>
                                <th className="p-3">Part Number</th>
                                <th className="p-3">Manufacturer</th>
                                <th className="p-3">Rated Current</th>
                                <th className="p-3">Rated Voltage</th>
                                <th className="p-3">Melting I²t</th>
                                <th className="p-3">Package</th>
                                <th className="p-3 text-center">Actions</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-850 text-slate-350">
                              {fuses.map((item, index) => (
                                <tr key={index} onClick={() => setSelectedFuse(item)} className={`cursor-pointer transition-colors ${selectedFuse?.name === item.name ? 'bg-violet-600/30 hover:bg-violet-600/40' : 'hover:bg-slate-900/40'}`}>
                                  <td className="p-3 font-semibold text-white">{item.name}</td>
                                  <td className="p-3">{item.manufacturer}</td>
                                  <td className="p-3 font-mono text-emerald-300">{item.i_rated}A</td>
                                  <td className="p-3 font-mono text-emerald-300">{item.v_rated}V</td>
                                  <td className="p-3 font-mono text-amber-300">{item.i2t}A²s</td>
                                  <td className="p-3">{item.package || '-'}</td>
                                  <td className="p-3 text-center">
                                    <button 
                                      onClick={(e) => { e.stopPropagation(); handleDeleteFuse(item.name); }}
                                      className="p-1 rounded text-red-400 hover:text-red-300 hover:bg-red-950/20 border-0 cursor-pointer"
                                    >
                                      <Trash2 size={14} />
                                    </button>
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </>
                        )}

                        {activeTab === 'ntcs' && (
                          <>
                            <thead className="bg-slate-900 text-slate-400 font-semibold sticky top-0">
                              <tr>
                                <th className="p-3">Part Number</th>
                                <th className="p-3">Manufacturer</th>
                                <th className="p-3">R25</th>
                                <th className="p-3">Imax</th>
                                <th className="p-3">Joule Rating</th>
                                <th className="p-3">Dissipation</th>
                                <th className="p-3">Package</th>
                                <th className="p-3 text-center">Actions</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-850 text-slate-350">
                              {ntcs.map((item, index) => (
                                <tr key={index} onClick={() => setSelectedNtc(item)} className={`cursor-pointer transition-colors ${selectedNtc?.name === item.name ? 'bg-violet-600/30 hover:bg-violet-600/40' : 'hover:bg-slate-900/40'}`}>
                                  <td className="p-3 font-semibold text-white">{item.name}</td>
                                  <td className="p-3">{item.manufacturer}</td>
                                  <td className="p-3 font-mono text-emerald-300">{item.r25}Ω</td>
                                  <td className="p-3 font-mono text-emerald-300">{item.i_max}A</td>
                                  <td className="p-3 font-mono text-amber-300">{item.joule_rating}J</td>
                                  <td className="p-3 font-mono text-cyan-300">{item.dissipation}mW/°C</td>
                                  <td className="p-3">{item.package || '-'}</td>
                                  <td className="p-3 text-center">
                                    <button 
                                      onClick={(e) => { e.stopPropagation(); handleDeleteNtc(item.name); }}
                                      className="p-1 rounded text-red-400 hover:text-red-300 hover:bg-red-950/20 border-0 cursor-pointer"
                                    >
                                      <Trash2 size={14} />
                                    </button>
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </>
                        )}

                        {activeTab === 'materials' && (
                          <>
                            <thead className="bg-slate-900 text-slate-400 font-semibold sticky top-0">
                              <tr>
                                <th className="p-3">Material</th>
                                <th className="p-3">Type</th>
                                <th className="p-3">Permeability μi</th>
                                <th className="p-3">Bsat@25°C</th>
                                <th className="p-3">Bsat@100°C</th>
                                <th className="p-3">Cm (100°C)</th>
                                <th className="p-3">x (100°C)</th>
                                <th className="p-3">y (100°C)</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-850 text-slate-300">
                              {materials.map((item, index) => (
                                <tr key={index} onClick={() => setSelectedMaterial(item)} className={`cursor-pointer transition-colors ${selectedMaterial?.name === item.name ? 'bg-violet-600/30 hover:bg-violet-600/40' : 'hover:bg-slate-900/40'}`}>
                                  <td className="p-3 font-semibold text-white">{item.name}</td>
                                  <td className="p-3">{item.type}</td>
                                  <td className="p-3 font-mono text-violet-300">{item.permeability}</td>
                                  <td className="p-3 font-mono text-amber-300">{item.b_sat_25}T</td>
                                  <td className="p-3 font-mono text-amber-300">{item.b_sat_100}T</td>
                                  <td className="p-3 font-mono text-emerald-300">{item.steinmetz_cm_100}</td>
                                  <td className="p-3 font-mono">{item.steinmetz_x_100}</td>
                                  <td className="p-3 font-mono">{item.steinmetz_y_100}</td>
                                </tr>
                              ))}
                            </tbody>
                          </>
                        )}

                        {activeTab === 'cores' && (
                          <>
                            <thead className="bg-slate-900 text-slate-400 font-semibold sticky top-0">
                              <tr>
                                <th className="p-3">Core Name</th>
                                <th className="p-3">Shape</th>
                                <th className="p-3">Material</th>
                                <th className="p-3">Ae (mm²)</th>
                                <th className="p-3">Le (mm)</th>
                                <th className="p-3">Ve (mm³)</th>
                                <th className="p-3">Wa (mm²)</th>
                                <th className="p-3">Al (nH)</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-850 text-slate-300">
                              {cores.map((item, index) => (
                                <tr key={index} onClick={() => setSelectedCore(item)} className={`cursor-pointer transition-colors ${selectedCore?.name === item.name ? 'bg-violet-600/30 hover:bg-violet-600/40' : 'hover:bg-slate-900/40'}`}>
                                  <td className="p-3 font-semibold text-white">{item.name}</td>
                                  <td className="p-3 font-mono text-violet-300">{item.shape}</td>
                                  <td className="p-3">{item.material}</td>
                                  <td className="p-3 font-mono text-emerald-300">{item.ae}</td>
                                  <td className="p-3 font-mono">{item.le}</td>
                                  <td className="p-3 font-mono">{item.ve}</td>
                                  <td className="p-3 font-mono">{item.wa}</td>
                                  <td className="p-3 font-mono text-amber-300">{item.al}</td>
                                </tr>
                              ))}
                            </tbody>
                          </>
                        )}
                      </table>
                    )}
                  </div>
                </div>
              )}

              {key === 'detail' && (
                <div className="flex-1 overflow-y-auto scrollbar-thin p-4 space-y-4 bg-slate-900/40 border border-slate-800/80 rounded-xl backdrop-blur-md">
                  <div className="flex items-center gap-2 border-b border-slate-800 pb-2 mb-3">
                    <span className="text-xs font-bold text-white">Physical Package & Frequency Analysis</span>
                  </div>

                  {activeTab === 'switches' && (
                    selectedSwitch ? (
                      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                        <div className="space-y-3">
                          <div className="p-3 rounded-lg border border-slate-850 bg-slate-950/40 space-y-1">
                            <span className="text-[9px] text-slate-400 block">Part Number: <strong className="text-white text-xs">{selectedSwitch.name}</strong> ({selectedSwitch.type})</span>
                            <div className="grid grid-cols-2 gap-2 text-[10px] font-mono mt-1 text-slate-350">
                              <div>Vds Max: <span className="text-emerald-400 font-bold">{selectedSwitch.v_ds_max}V</span></div>
                              <div>Id Max: <span className="text-emerald-400 font-bold">{selectedSwitch.i_d_max}A</span></div>
                              <div>Rds(on): <span className="text-amber-400 font-bold">{selectedSwitch.r_ds_on}Ω</span></div>
                              <div>Rth(j-c): <span className="text-cyan-400">{selectedSwitch.r_jc ?? 0.8}°C/W</span></div>
                            </div>
                          </div>
                          <div className="flex justify-center bg-slate-950/30 p-2 rounded-lg border border-slate-850">
                            <svg width="100%" height="100%" viewBox="0 0 160 110" className="max-w-[150px] max-h-[100px]">
                              <rect x="50" y="10" width="60" height="40" rx="3" fill="#64748b" />
                              <circle cx="80" cy="20" r="5" fill="#0f172a" />
                              <rect x="52" y="24" width="56" height="46" rx="2" fill="#1e293b" stroke="#475569" strokeWidth="1" />
                              <path d="M 52 30 L 60 24 L 100 24 L 108 30" fill="none" stroke="#475569" strokeWidth="1" />
                              <line x1="62" y1="70" x2="62" y2="105" stroke="#cbd5e1" strokeWidth="2.5" />
                              <line x1="80" y1="70" x2="80" y2="105" stroke="#cbd5e1" strokeWidth="2.5" />
                              <line x1="98" y1="70" x2="98" y2="105" stroke="#cbd5e1" strokeWidth="2.5" />
                              <text x="62" y="102" textAnchor="middle" fill="#f43f5e" className="text-[7px] font-bold">1:G</text>
                              <text x="80" y="102" textAnchor="middle" fill="#0ea5e9" className="text-[7px] font-bold">2:D</text>
                              <text x="98" y="102" textAnchor="middle" fill="#10b981" className="text-[7px] font-bold">3:S</text>
                              <text x="80" y="55" textAnchor="middle" fill="#94a3b8" className="text-[7.5px] font-bold">{selectedSwitch.package || 'TO-247'}</text>
                            </svg>
                          </div>
                        </div>
                        <div className="space-y-3 flex flex-col justify-between">
                          <div className="text-[10px] text-slate-400 leading-relaxed space-y-1">
                            <span className="font-bold text-slate-300 block">Junction-to-Case Foster Thermal RC Network:</span>
                            <p>Semiconductor transient junction temperature depends on the internal RC ladder network from die to case.</p>
                          </div>
                          <div className="flex justify-center p-2 rounded-lg bg-slate-950/20 border border-slate-850">
                            <svg width="100%" height="100%" viewBox="0 0 160 80" className="max-w-[180px] max-h-[80px]">
                              <circle cx="15" cy="40" r="3" fill="#f43f5e" />
                              <text x="15" y="32" textAnchor="middle" fill="#f43f5e" className="text-[6.5px] font-bold">Tj</text>
                              <line x1="18" y1="40" x2="35" y2="40" stroke="#64748b" strokeWidth="1.2" />
                              <rect x="35" y="35" width="20" height="10" fill="none" stroke="#38bdf8" strokeWidth="1.2" />
                              <text x="45" y="30" textAnchor="middle" fill="#38bdf8" className="text-[6px] font-mono">Rjc</text>
                              <line x1="26" y1="40" x2="26" y2="55" stroke="#64748b" strokeWidth="1.2" />
                              <line x1="21" y1="55" x2="31" y2="55" stroke="#0ea5e9" strokeWidth="1.2" />
                              <line x1="21" y1="58" x2="31" y2="58" stroke="#0ea5e9" strokeWidth="1.2" />
                              <line x1="26" y1="58" x2="26" y2="68" stroke="#64748b" strokeWidth="1.2" />
                              <line x1="26" y1="68" x2="115" y2="68" stroke="#64748b" strokeWidth="1" />
                              <line x1="70" y1="68" x2="70" y2="73" stroke="#475569" strokeWidth="1" />
                              <line x1="66" y1="73" x2="74" y2="73" stroke="#475569" strokeWidth="1" />
                              <line x1="55" y1="40" x2="105" y2="40" stroke="#64748b" strokeWidth="1.2" />
                              <circle cx="105" cy="40" r="3" fill="#10b981" />
                              <text x="105" y="32" textAnchor="middle" fill="#10b981" className="text-[6.5px] font-bold">Tc (Case)</text>
                            </svg>
                          </div>
                        </div>
                      </div>
                    ) : (
                      <div className="text-xs text-slate-500 text-center py-10">Select a switch from the catalog to inspect package pinout and thermal network</div>
                    )
                  )}

                  {activeTab === 'diodes' && (
                    selectedDiode ? (
                      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                        <div className="space-y-3">
                          <div className="p-3 rounded-lg border border-slate-850 bg-slate-950/40 space-y-1">
                            <span className="text-[9px] text-slate-400 block">Part Number: <strong className="text-white text-xs">{selectedDiode.name}</strong> ({selectedDiode.type})</span>
                            <div className="grid grid-cols-2 gap-2 text-[10px] font-mono mt-1 text-slate-350">
                              <div>Reverse Vr: <span className="text-emerald-400 font-bold">{selectedDiode.v_r_max}V</span></div>
                              <div>Forward If: <span className="text-emerald-400 font-bold">{selectedDiode.i_f_max}A</span></div>
                              <div>Forward Drop Vf: <span className="text-amber-400 font-bold">{selectedDiode.v_f}V</span></div>
                              <div>Thermal Rjc: <span className="text-cyan-400">{selectedDiode.r_jc ?? 1.5}°C/W</span></div>
                            </div>
                          </div>
                          <div className="flex justify-center bg-slate-950/30 p-2 rounded-lg border border-slate-850">
                            <svg width="100%" height="100%" viewBox="0 0 160 110" className="max-w-[150px] max-h-[100px]">
                              <rect x="55" y="12" width="50" height="30" rx="2" fill="#64748b" />
                              <circle cx="80" cy="20" r="4" fill="#0f172a" />
                              <rect x="57" y="28" width="46" height="40" rx="1.5" fill="#1e293b" stroke="#475569" strokeWidth="1" />
                              <line x1="70" y1="68" x2="70" y2="105" stroke="#cbd5e1" strokeWidth="2.5" />
                              <line x1="90" y1="68" x2="90" y2="105" stroke="#cbd5e1" strokeWidth="2.5" />
                              <text x="70" y="102" textAnchor="middle" fill="#f43f5e" className="text-[7px] font-bold">1:K (Cathode)</text>
                              <text x="90" y="102" textAnchor="middle" fill="#10b981" className="text-[7px] font-bold">2:A (Anode)</text>
                              <text x="80" y="52" textAnchor="middle" fill="#94a3b8" className="text-[7.5px] font-bold">{selectedDiode.package || 'TO-220'}</text>
                            </svg>
                          </div>
                        </div>

                        <div className="space-y-3 flex flex-col justify-between">
                          <div className="text-[10px] text-slate-400 leading-relaxed space-y-1">
                            <span className="font-bold text-slate-300 block">Diode Conduction Physics Equation:</span>
                            <p>Forward voltage drop increases with current. Conduction loss calculation:</p>
                            <div className="p-2 rounded bg-slate-950/40 border border-slate-850 font-mono text-[9px] text-emerald-300 mt-1">
                              P_loss = V_f * I_f
                            </div>
                          </div>
                          <div className="flex justify-center p-2 rounded-lg bg-slate-950/20 border border-slate-850">
                            <svg width="100%" height="100%" viewBox="0 0 160 60" className="max-w-[160px] max-h-[60px]">
                              <line x1="20" y1="30" x2="60" y2="30" stroke="#64748b" strokeWidth="1.5" />
                              <polygon points="60,20 60,40 75,30" fill="#10b981" stroke="#10b981" />
                              <line x1="75" y1="20" x2="75" y2="40" stroke="#f43f5e" strokeWidth="2" />
                              <line x1="75" y1="30" x2="140" y2="30" stroke="#64748b" strokeWidth="1.5" />
                              <text x="40" y="18" fill="#10b981" className="text-[8px] font-bold">A (Anode)</text>
                              <text x="95" y="18" fill="#f43f5e" className="text-[8px] font-bold">K (Cathode)</text>
                            </svg>
                          </div>
                        </div>
                      </div>
                    ) : (
                      <div className="text-xs text-slate-500 text-center py-10">Select a diode from the catalog to inspect package pinout and model</div>
                    )
                  )}

                  {activeTab === 'zeners' && (
                    selectedZener ? (
                      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                        <div className="space-y-3">
                          <div className="p-3 rounded-lg border border-slate-850 bg-slate-950/40 space-y-1">
                            <span className="text-[10px] text-slate-350 block font-bold">Zener Diode: {selectedZener.name}</span>
                            <div className="grid grid-cols-2 gap-2 text-[10px] font-mono mt-1 text-slate-300">
                              <div>Nominal Vz: <span className="text-emerald-400 font-bold">{selectedZener.vz}V</span></div>
                              <div>Test Current Izt: <span className="text-emerald-400">{selectedZener.izt ?? 5}mA</span></div>
                              <div>Knee Current Izk: <span className="text-amber-400">{selectedZener.izk ?? 1}mA</span></div>
                              <div>Dynamic Res Zzt: <span className="text-amber-400 font-bold">{selectedZener.zzt ?? 10}Ω</span></div>
                              <div>Rated Power Pd: <span className="text-cyan-400 font-bold">{selectedZener.p_d ?? 1}W</span></div>
                              <div>Package: <span className="text-slate-400">{selectedZener.package || 'SOD-123'}</span></div>
                            </div>
                          </div>
                        </div>
                        <div className="space-y-3 flex flex-col justify-between">
                          <div className="text-[10px] text-slate-400 leading-relaxed">
                            <span className="font-bold text-slate-300 block">Zener Diode IEC Schematic Symbol:</span>
                            <p>Operates in reverse breakdown to regulate voltage across dynamic impedance.</p>
                          </div>
                          <div className="flex justify-center p-2 rounded-lg bg-slate-950/20 border border-slate-850">
                            <svg width="100%" height="100%" viewBox="0 0 160 60" className="max-w-[160px] max-h-[60px]">
                              <line x1="20" y1="30" x2="65" y2="30" stroke="#64748b" strokeWidth="1.5" />
                              <polygon points="65,20 65,40 80,30" fill="#10b981" stroke="#10b981" />
                              <path d="M 80 18 L 80 42 M 80 18 L 76 18 M 80 42 L 84 42" stroke="#f43f5e" strokeWidth="2.2" fill="none" />
                              <line x1="80" y1="30" x2="140" y2="30" stroke="#64748b" strokeWidth="1.5" />
                              <text x="40" y="16" fill="#10b981" className="text-[8px] font-bold">A (Anode)</text>
                              <text x="95" y="16" fill="#f43f5e" className="text-[8px] font-bold">K (Cathode)</text>
                            </svg>
                          </div>
                        </div>
                      </div>
                    ) : (
                      <div className="text-xs text-slate-500 text-center py-10">Select a zener diode from the catalog to inspect parameters and symbol</div>
                    )
                  )}

                  {activeTab === 'tvs' && (
                    selectedTvs ? (
                      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                        <div className="space-y-3">
                          <div className="p-3 rounded-lg border border-slate-850 bg-slate-950/40 space-y-1">
                            <span className="text-[10px] text-slate-350 block font-bold">Transient Voltage Suppressor (TVS): {selectedTvs.name}</span>
                            <div className="grid grid-cols-2 gap-2 text-[10px] font-mono mt-1 text-slate-300">
                              <div>Standoff VRWM: <span className="text-emerald-400 font-bold">{selectedTvs.vrwm}V</span></div>
                              <div>Breakdown Vbr: <span className="text-emerald-400">{selectedTvs.vbr}V</span></div>
                              <div>Clamping Vc: <span className="text-red-400 font-bold">{selectedTvs.vc}V</span></div>
                              <div>Pulse Current Ipp: <span className="text-amber-400 font-bold">{selectedTvs.ipp}A</span></div>
                              <div>Surge Power Pppm: <span className="text-cyan-400 font-bold">{selectedTvs.pppm}W</span></div>
                              <div>Package Type: <span className="text-slate-400">{selectedTvs.package || 'SMB'}</span></div>
                            </div>
                          </div>
                        </div>
                        <div className="space-y-3 flex flex-col justify-between">
                          <div className="text-[10px] text-slate-400 leading-relaxed">
                            <span className="font-bold text-slate-300 block">Bidirectional TVS Diode Schematic Symbol:</span>
                            <p>Symmetric avalanche breakdown clamps overvoltage transients in both polarities.</p>
                          </div>
                          <div className="flex justify-center p-2 rounded-lg bg-slate-950/20 border border-slate-850">
                            <svg width="100%" height="100%" viewBox="0 0 160 60" className="max-w-[160px] max-h-[60px]">
                              <line x1="20" y1="30" x2="60" y2="30" stroke="#64748b" strokeWidth="1.5" />
                              <polygon points="60,20 60,40 70,30" fill="none" stroke="#10b981" strokeWidth="1.2" />
                              <polygon points="80,20 80,40 70,30" fill="none" stroke="#10b981" strokeWidth="1.2" />
                              <path d="M 70 18 L 70 42 M 70 18 L 66 22 M 70 42 L 74 38" stroke="#f43f5e" strokeWidth="2.2" fill="none" />
                              <line x1="80" y1="30" x2="140" y2="30" stroke="#64748b" strokeWidth="1.5" />
                            </svg>
                          </div>
                        </div>
                      </div>
                    ) : (
                      <div className="text-xs text-slate-500 text-center py-10">Select a TVS diode from the catalog to inspect specifications and schematic</div>
                    )
                  )}

                  {activeTab === 'capacitors' && (
                    selectedCap ? (
                      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                        <div className="space-y-3">
                          <div className="p-3 rounded-lg border border-slate-850 bg-slate-950/40 space-y-1">
                            <span className="text-[10px] text-slate-350 block font-bold">Capacitor Details: {selectedCap.name}</span>
                            <div className="grid grid-cols-2 gap-2 text-[10px] font-mono mt-1 text-slate-300">
                              <div>Capacitance C: <span className="text-emerald-400 font-bold">{(selectedCap.capacitance * 1e6).toFixed(1)}μF</span></div>
                              <div>Rated Voltage Vr: <span className="text-emerald-400 font-bold">{selectedCap.voltage_rating}V</span></div>
                              <div>Equivalent ESR: <span className="text-amber-400 font-bold">{selectedCap.esr ?? 0.1}Ω</span></div>
                              <div>Equivalent ESL: <span className="text-slate-400">{selectedCap.esl ?? 0} nH</span></div>
                              <div>Rated Ripple Current: <span className="text-cyan-400">{selectedCap.ripple_current ?? 1.5}A</span></div>
                              <div>Max Temp: <span className="text-amber-300">{selectedCap.temp_max ?? 105}°C</span></div>
                              <div>Expected Lifetime: <span className="text-violet-400">{selectedCap.lifetime_hours ?? 5000}h</span></div>
                              <div>Capacitor Type: <span className="text-slate-400">{selectedCap.type}</span></div>
                            </div>
                          </div>
                        </div>
                        <div className="space-y-3 flex flex-col justify-between">
                          <div className="text-[10px] text-slate-400 leading-relaxed">
                            <span className="font-bold text-slate-300 block">Polarized Electrolytic Capacitor Schematic Symbol:</span>
                            <p>Used for DC bus filtering; strictly observe voltage polarity.</p>
                          </div>
                          <div className="flex justify-center p-2 rounded-lg bg-slate-950/20 border border-slate-850">
                            <svg width="100%" height="100%" viewBox="0 0 160 60" className="max-w-[160px] max-h-[60px]">
                              <line x1="20" y1="30" x2="68" y2="30" stroke="#64748b" strokeWidth="1.5" />
                              <line x1="68" y1="18" x2="68" y2="42" stroke="#10b981" strokeWidth="3" />
                              <line x1="76" y1="18" x2="76" y2="42" stroke="#f43f5e" strokeWidth="3" />
                              <line x1="76" y1="30" x2="140" y2="30" stroke="#64748b" strokeWidth="1.5" />
                              <text x="60" y="16" fill="#10b981" className="text-[10px] font-bold">+</text>
                            </svg>
                          </div>
                        </div>
                      </div>
                    ) : (
                      <div className="text-xs text-slate-500 text-center py-10">Select a capacitor from the catalog to inspect ESR and lifetime specs</div>
                    )
                  )}

                  {activeTab === 'fuses' && (
                    selectedFuse ? (
                      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                        <div className="space-y-3">
                          <div className="p-3 rounded-lg border border-slate-850 bg-slate-950/40 space-y-1">
                            <span className="text-[10px] text-slate-350 block font-bold">Fuse Specifications: {selectedFuse.name}</span>
                            <div className="grid grid-cols-2 gap-2 text-[10px] font-mono mt-1 text-slate-300">
                              <div>Rated Current Ir: <span className="text-emerald-400 font-bold">{selectedFuse.i_rated}A</span></div>
                              <div>Rated Voltage Vr: <span className="text-emerald-400">{selectedFuse.v_rated}V</span></div>
                              <div>Melting I²t: <span className="text-amber-400 font-bold">{selectedFuse.i2t}A²s</span></div>
                              <div>Package: <span className="text-slate-400">{selectedFuse.package || '0603'}</span></div>
                            </div>
                          </div>
                        </div>
                        <div className="space-y-3 flex flex-col justify-between">
                          <div className="text-[10px] text-slate-400 leading-relaxed">
                            <span className="font-bold text-slate-300 block">IEC Standard Fuse Schematic Symbol:</span>
                            <p>Standard IEC rectangular body with central horizontal connecting lead.</p>
                          </div>
                          <div className="flex justify-center p-2 rounded-lg bg-slate-950/20 border border-slate-850">
                            <svg width="100%" height="100%" viewBox="0 0 160 60" className="max-w-[160px] max-h-[60px]">
                              <line x1="20" y1="30" x2="140" y2="30" stroke="#10b981" strokeWidth="1.5" />
                              <rect x="55" y="18" width="50" height="24" fill="none" stroke="#f43f5e" strokeWidth="2" />
                            </svg>
                          </div>
                        </div>
                      </div>
                    ) : (
                      <div className="text-xs text-slate-500 text-center py-10">Select a fuse from the catalog to inspect I²t and electrical stresses</div>
                    )
                  )}

                  {activeTab === 'ntcs' && (
                    selectedNtc ? (
                      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                        <div className="space-y-3">
                          <div className="p-3 rounded-lg border border-slate-850 bg-slate-950/40 space-y-1">
                            <span className="text-[10px] text-slate-350 block font-bold">NTC Thermistor: {selectedNtc.name}</span>
                            <div className="grid grid-cols-2 gap-2 text-[10px] font-mono mt-1 text-slate-300">
                              <div>Zero-Power Res R25: <span className="text-emerald-400 font-bold">{selectedNtc.r25}Ω</span></div>
                              <div>Max Continuous Current: <span className="text-emerald-400">{selectedNtc.i_max}A</span></div>
                              <div>Max Absorbed Energy: <span className="text-amber-400 font-bold">{selectedNtc.joule_rating}J</span></div>
                              <div>Dissipation Factor δ: <span className="text-cyan-400">{selectedNtc.dissipation}mW/°C</span></div>
                              <div>Package: <span className="text-slate-400">{selectedNtc.package || 'Radial'}</span></div>
                            </div>
                          </div>
                        </div>
                        <div className="space-y-3 flex flex-col justify-between">
                          <div className="text-[10px] text-slate-400 leading-relaxed">
                            <span className="font-bold text-slate-300 block">NTC Thermistor Schematic Symbol:</span>
                            <p>Resistor body traversed by diagonal line with -t° temperature coefficient.</p>
                          </div>
                          <div className="flex justify-center p-2 rounded-lg bg-slate-950/20 border border-slate-850">
                            <svg width="100%" height="100%" viewBox="0 0 160 60" className="max-w-[160px] max-h-[60px]">
                              <line x1="20" y1="30" x2="55" y2="30" stroke="#64748b" strokeWidth="1.5" />
                              <rect x="55" y="20" width="50" height="20" fill="none" stroke="#10b981" strokeWidth="1.5" />
                              <line x1="105" y1="30" x2="140" y2="30" stroke="#64748b" strokeWidth="1.5" />
                              <path d="M 46 48 L 52 48 L 112 12" stroke="#f43f5e" strokeWidth="1.5" fill="none" />
                              <text x="115" y="16" fill="#f43f5e" className="text-[7.5px] font-bold">-t°</text>
                            </svg>
                          </div>
                        </div>
                      </div>
                    ) : (
                      <div className="text-xs text-slate-500 text-center py-10">Select an NTC from the catalog to inspect inrush suppression ratings</div>
                    )
                  )}

                  {activeTab === 'materials' && (
                    selectedMaterial ? (
                      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 h-full">
                        <div className="lg:col-span-4 space-y-3">
                          <div className="p-3 rounded-lg border border-slate-850 bg-slate-950/40 space-y-1">
                            <span className="text-[10px] text-slate-300 block font-bold">Core Material: {selectedMaterial.name}</span>
                            <span className="text-[8.5px] text-slate-400 block">Type: {selectedMaterial.type}</span>
                            <div className="text-[9px] font-mono text-slate-350 space-y-0.5 mt-2">
                              <div>Initial Permeability μi: <span className="text-violet-400">{selectedMaterial.permeability}</span></div>
                              <div>Bsat@25°C: <span className="text-amber-400">{selectedMaterial.b_sat_25} T</span></div>
                              <div>Bsat@100°C: <span className="text-amber-400">{selectedMaterial.b_sat_100} T</span></div>
                              <div className="border-t border-slate-800/80 pt-1 mt-1 font-bold">Steinmetz Parameters @100°C:</div>
                              <div className="text-cyan-400">Cm = {selectedMaterial.steinmetz_cm_100 || 12.0}</div>
                              <div className="text-cyan-400">x = {selectedMaterial.steinmetz_x_100 || 1.6} (Freq Exponent)</div>
                              <div className="text-cyan-400">y = {selectedMaterial.steinmetz_y_100 || 2.5} (Flux Exponent)</div>
                            </div>
                          </div>
                        </div>
                        <div className="lg:col-span-8 flex flex-col h-[200px]">
                          <span className="text-[9.5px] font-bold text-slate-350 block mb-1">Steinmetz Core Loss Frequency Sweep (Pv vs Bac)</span>
                          <div className="w-full h-full min-h-[170px] bg-slate-950/30 border border-slate-850/80 rounded-lg p-2">
                            <ReactECharts option={getSteinmetzChartOption(selectedMaterial)} notMerge={true} style={{ width: '100%', height: '100%' }} />
                          </div>
                        </div>
                      </div>
                    ) : (
                      <div className="text-xs text-slate-500 text-center py-10">Select a core material from the catalog to inspect log-log Steinmetz loss curves</div>
                    )
                  )}

                  {activeTab === 'cores' && (
                    selectedCore ? (
                      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                        <div className="space-y-3">
                          <div className="p-3 rounded-lg border border-slate-850 bg-slate-950/40 space-y-1">
                            <span className="text-[10px] text-slate-300 block font-bold">Core Geometry: {selectedCore.name}</span>
                            <div className="grid grid-cols-2 gap-2 text-[9px] font-mono mt-1 text-slate-350">
                              <div>Core Shape: <span className="text-violet-400">{selectedCore.shape}</span></div>
                              <div>Linked Material: <span className="text-cyan-400">{selectedCore.material}</span></div>
                              <div>Cross Section Ae: <span className="text-emerald-400">{selectedCore.ae} mm²</span></div>
                              <div>Path Length Le: <span className="text-emerald-400">{selectedCore.le} mm</span></div>
                              <div>Effective Volume Ve: <span className="text-amber-400">{selectedCore.ve} mm³</span></div>
                              <div>Window Area Wa: <span className="text-amber-400">{selectedCore.wa} mm²</span></div>
                              <div>Inductance Factor Al: <span className="text-teal-400">{selectedCore.al ?? '-'} nH</span></div>
                            </div>
                          </div>
                        </div>

                        <div className="space-y-3 flex flex-col justify-between">
                          <div className="text-[10px] text-slate-400 leading-relaxed">
                            <span className="font-bold text-slate-300 block">3D Core Dimensional Drawing (EE-Type):</span>
                          </div>
                          <div className="flex justify-center p-2 rounded-lg bg-slate-950/30 border border-slate-850">
                            <svg width="100%" height="100%" viewBox="0 0 160 90" className="max-w-[160px] max-h-[90px]">
                              <rect x="25" y="15" width="10" height="60" fill="#334155" stroke="#475569" strokeWidth="0.8" />
                              <rect x="35" y="15" width="25" height="12" fill="#334155" stroke="#475569" strokeWidth="0.8" />
                              <rect x="35" y="38" width="22" height="14" fill="#334155" stroke="#475569" strokeWidth="0.8" />
                              <rect x="35" y="63" width="25" height="12" fill="#334155" stroke="#475569" strokeWidth="0.8" />
                              <rect x="125" y="15" width="10" height="60" fill="#1e293b" stroke="#334155" strokeWidth="0.8" />
                              <rect x="100" y="15" width="25" height="12" fill="#1e293b" stroke="#334155" strokeWidth="0.8" />
                              <rect x="103" y="38" width="22" height="14" fill="#1e293b" stroke="#334155" strokeWidth="0.8" />
                              <rect x="100" y="63" width="25" height="12" fill="#1e293b" stroke="#334155" strokeWidth="0.8" />
                              <line x1="80" y1="36" x2="80" y2="54" stroke="#f43f5e" strokeWidth="1.5" strokeDasharray="2,2" />
                              <text x="80" y="30" textAnchor="middle" fill="#f43f5e" className="text-[6px] font-mono font-bold">Air Gap</text>
                              <line x1="25" y1="80" x2="135" y2="80" stroke="#94a3b8" strokeWidth="0.5" />
                              <text x="80" y="87" textAnchor="middle" fill="#94a3b8" className="text-[5.5px]">A (Width)</text>
                            </svg>
                          </div>
                        </div>
                      </div>
                    ) : (
                      <div className="text-xs text-slate-500 text-center py-10">Select a core geometry from the catalog to inspect physical dimensions</div>
                    )
                  )}
                </div>
              )}
            </DragCard>
          )}
          onDropOnColumn={handleDropOnColumn}
        />
      </div>
    </div>
  );
}
