import type { ModuleTranslation } from './types';

export const zhDict: Record<string, string> = {
  // Navigation & Shell
  'app.title': 'HW ToolBox 硬件设计平台',
  'app.navTitle': '导航索引',
  'app.allModules': '工作台主页',
  'app.dashboard': '主仪表盘 (Dashboard)',
  'app.author': '开发者: WenZhenJian-EE',
  'app.github': 'GitHub 开源仓库',
  'app.all': '全部',
  'app.addGroup': '添加分组',
  'app.arch': '系统架构',
  'app.archValue': 'Hybrid Desktop (React 19 + Python)',
  'app.switchLang': '切换语言',
  'app.backendConnected': '计算引擎就绪',
  'app.backendConnecting': '引擎连接中...',

  // Dashboard Welcome Card
  'app.welcomeTitle': '电力电子一体化协同设计平台',
  'app.welcomeDesc': '深度集成高阶物理方程解算器、拓扑仿真、时频域分析与器件数据库选型。请从下方选择或搜索专业设计模块开始工作。',
  'app.totalModules': '可用模块',
  'app.verifiedModels': '通过率',
  'app.activeTopologies': '原生英文基线',

  // Controls & Toolbar
  'app.searchPlaceholder': '搜索模块名称、英文或物理术语...',
  'app.resetLayout': '重置默认布局',
  'app.columns': '列布局',
  'app.uncategorized': '未分类',

  // Module Badges & Status
  'app.badgeTemplate': '模板',
  'app.badgeDev': '已就绪',

  // Error Boundary
  'app.errorTitle': '模块渲染异常',
  'app.errorDesc': '该功能模块在渲染过程中抛出了未捕获的运行时异常。',
  'app.errorRetry': '重试当前模块',

  // Categories
  'cat.all': '全部',
  'cat.co_design': '⚡ 协同电源设计 (Co-Design)',
  'cat.magnetics': '🧲 磁件与拓扑基础',
  'cat.power_thermal': '🔥 功率器件与热力',
  'cat.loop_signal': '📈 环路控制与信号',
  'cat.passives_safety': '🛡️ 无源元器件与安规',

  // Common Engineering Terms
  'common.calculate': '解算 / 仿真',
  'common.reset': '重置默认值',
  'common.export': '导出数据',
  'common.schematic': '交互原理图设计',
  'common.specs': '系统工况与物理规格',
  'common.bom': '商业 BOM 选型',
  'common.waveforms': '时频域分析',
  'common.drc': '安全 DRC 规则检查',
  'common.results': '设计核算结果',
  'common.parameters': '设计工况参数',
  'common.theory': '物理公式与理论推导',
};

export const zhModules: Record<string, ModuleTranslation> = {
  buck: {
    name: '降压变换器 (Buck)',
    description: '降压变换器稳态分析。支持 CCM/DCM 电感电流时域仿真、控制环路 Bode 扫频、输出电容纹波应力评估与 BOM 选型。'
  },
  flyback: {
    name: '隔离反激变换器 (Flyback)',
    description: '隔离反激变换器分析设计。支持 AP法变压器磁选型、副边同步整流损耗核算、RCD 钳位计算与双环控制时频域仿真。'
  },
  mag_inductor: {
    name: '功率电感磁选型设计',
    description: '计算功率电感磁芯、气隙与绕组规格，支持 Dowell 高频损耗、边缘磁通修正与直流偏置软饱和校核。'
  },
  mag_transformer: {
    name: '高频集成变压器设计',
    description: '设计正激、反激与 LLC 级联变压器，计算 AP 法规格、高频绕组交流电阻系数及等效漏感。'
  },
  mag_core_loss: {
    name: '磁芯高频损耗评估',
    description: '基于改进 Steinmetz 公式 (iGSE) 计算非正弦激磁下的铁氧体与金属磁粉芯损耗，耦合稳态温升模型。'
  },
  snubber: {
    name: '开关管缓冲与吸收设计',
    description: '基于振铃频率偏移实测法或反激 RCD 钳位模型，设计开关管关断过冲 RC 缓冲与吸收参数。'
  },
  power_dclink: {
    name: '母线电容纹波与寿命分析',
    description: '分析交错并联及三相逆变器直流母线电容的 RMS 纹波电流、ESR 损耗与使用寿命预测。'
  },
  power_ac_3ph: {
    name: '三相交流电与坐标变换',
    description: '计算三相 Y-Delta 阻抗变换、Clarke/Park 坐标变换、功率因数补偿与三相锁相环参数。'
  },
  power_foster_thermal: {
    name: '瞬态热网络与结温仿真',
    description: '使用 Foster 阻容热网络状态方程，仿真并预测半导体开关管在瞬态脉冲过载下的动态结温。'
  },
  gate_drive_miller: {
    name: '门极驱动与米勒校验',
    description: '校验高频开关管 (SiC/GaN) 门极 dv/dt 米勒误开通，评估死区损耗与 ZVS 软开关条件。'
  },
  heatsink: {
    name: '散热片结构与热阻计算',
    description: '计算散热片自然对流与强迫风冷等效热阻，建立功率半导体多节点一维与三维热网络模型。'
  },
  ldo_thermal: {
    name: 'LDO 稳压与热耗计算',
    description: '计算 LDO 线性电源热损耗，核算 PCB 铜箔散热面积限制并提供极限结温 DRC 校核。'
  },
  power_device: {
    name: '开关器件损耗与热校核',
    description: '核算 MOSFET/IGBT 半导体损耗与温升，评估驱动功率、米勒效应及等效结温。'
  },
  power_dpt: {
    name: '双脉冲测试参数计算',
    description: '计算双脉冲测试 (DPT) 回路充电脉宽、续流时序，并校核开通与关断交叠损耗 (Eon/Eoff)。'
  },
  battery_pack: {
    name: '电池包与 BMS 选型计算',
    description: '核算锂电芯串并联参数、放电温升损耗与被动均衡泄放阻容匹配。'
  },
  power_budget: {
    name: '变换器损耗与效率预算',
    description: '汇总分析变换器有源开关、磁性元件、缓冲阻抗与控制电路等多子项的损耗分布及整机效率。'
  },
  loop_compensation: {
    name: '控制环路补偿设计',
    description: '设计 Type II/III 补偿器与 TL431-光耦隔离反馈参数，通过零极点配置优化系统截止频率与相位裕度。'
  },
  digital_pid: {
    name: '数字 PID 与离散化计算',
    description: '将控制传递函数进行离散化转换 (S 域至 Z 域)，并核算巴特沃斯数字滤波器系数与 PID 差分方程。'
  },
  filter_passive: {
    name: '无源与有源滤波器设计',
    description: '设计信号调理滤波器与共/差模 EMI 滤波器，核算去耦网络阻抗与 Middlebrook 稳定性阻抗判据。'
  },
  emc_toolbox: {
    name: 'EMC 滤波器与阻尼设计',
    description: '换算 EMC 单位并评估滤波器插损、缝隙屏蔽与共差模阻尼，设计传导整改与吸收网络。'
  },
  adc_conditioning: {
    name: 'ADC 调理与信号链标定',
    description: '设计 ADC 采样前级 RC 滤波器，核算信号调理放大倍数、阻抗匹配、通道噪声与两点标定。'
  },
  current_shunt: {
    name: '电流分流器与互感器校核',
    description: '校核电流互感器 (CT) 磁饱和与 Burden 电阻，评估分流器自热温漂与非开尔文走线带来的采样误差。'
  },
  ntc: {
    name: 'NTC 阻温计算与曲线拟合',
    description: '通过 B 值或 Steinhart-Hart 三点方程拟合 NTC 阻温曲线，设计线性化电路并生成查表 C 代码。'
  },
  pwm_mcu_ic: {
    name: 'PWM 定时器与控制 IC 外围',
    description: '计算 RC 低通 DAC 滤波纹波；反解 MCU 寄存器死区时间值；设计 UC3842 等模拟控制器 RT/CT 振荡阻容。'
  },
  tvs_zener: {
    name: 'TVS/Zener 过压防护选型',
    description: '核算稳压管极值功耗与限流电阻；计算 TVS 瞬态浪涌峰值功率、钳位电压与结温升。'
  },
  input_protection: {
    name: '输入保护与泄放设计',
    description: '校验保险丝 $I^2t$ 开机脉冲熔断应力；核算功率型 NTC 浪涌热容与安规放电 RC 阻容参数。'
  },
  pcb_toolbox: {
    name: 'PCB 电磁与载流设计',
    description: '计算走线载流温升、过孔寄生参数与热阻；设计微带线与共面波导等阻抗控制。'
  },
  wire_copper_bar: {
    name: '绕组导线与大电流铜排选型',
    description: '分析高频利兹线趋肤与邻近效应损耗，核算圆铜线 AWG 载流与大电流铜排稳态温升。'
  },
  capacitor_toolbox: {
    name: '电容寿命与降额核算',
    description: '预测铝电解电容阿伦尼乌斯温升寿命，核算多频 RMS 电流叠加损耗与 MLCC 直流偏置电压降额。'
  },
  db_manager: {
    name: '器件与材质规格数据库',
    description: '管理和维护开关管、续流二极管、磁芯材质特性与几何规格本地 SQLite 数据库。'
  }
};
