export type MainTabType = 'driver' | 'physics';
export type DriverSubTabType = 'gate' | 'desat' | 'bootstrap' | 'gdt' | 'compare';
export type PhysicsSubTabType = 'loss' | 'deadtime' | 'miller' | 'zth' | 'diode' | 'soa' | 'coupled';

export interface Candidate {
  id: number;
  name: string;
  tech: string;
  vds: number;
  id_max: number;
  rds: number;
  qg: number;
  eon: number;
  eoff: number;
  eoss: number;
  qrr: number;
  rthjc: number;
  tcase: string;
  result?: string;
  p_cond?: number;
  p_sw?: number;
  p_gate?: number;
  p_qrr?: number;
  p_total?: number;
  tj?: number;
}

export interface ZthRcElement {
  r: number;
  tau: number;
}
