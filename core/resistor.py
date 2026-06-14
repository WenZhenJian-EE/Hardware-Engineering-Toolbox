# core/resistor.py

import math

class ResistorDividerCalculator:
    """
    一个通用的分压电阻计算器和标准电阻值数据库。
    (无 GUI 依赖，供核心算法与测试使用)
    """
    def __init__(self):
        self.e96_series = [
            1.00, 1.02, 1.05, 1.07, 1.10, 1.13, 1.15, 1.18, 1.21, 1.24,
            1.27, 1.30, 1.33, 1.37, 1.40, 1.43, 1.47, 1.50, 1.54, 1.58,
            1.62, 1.65, 1.69, 1.74, 1.78, 1.82, 1.87, 1.91, 1.96, 2.00,
            2.05, 2.10, 2.15, 2.21, 2.26, 2.32, 2.37, 2.43, 2.49, 2.55,
            2.61, 2.67, 2.74, 2.80, 2.87, 2.94, 3.01, 3.09, 3.16, 3.24,
            3.32, 3.40, 3.48, 3.57, 3.65, 3.74, 3.83, 3.92, 4.02, 4.12,
            4.22, 4.32, 4.42, 4.53, 4.64, 4.75, 4.87, 4.99, 5.11, 5.23,
            5.36, 5.49, 5.62, 5.76, 5.90, 6.04, 6.19, 6.34, 6.49, 6.65,
            6.81, 6.98, 7.15, 7.32, 7.50, 7.68, 7.87, 8.06, 8.25, 8.45,
            8.66, 8.87, 9.09, 9.31, 9.53, 9.76
        ]
        self.e192_series = [
            1.00, 1.01, 1.02, 1.04, 1.05, 1.06, 1.07, 1.09, 1.10, 1.11, 1.13, 1.14, 1.15, 1.17, 1.18, 1.20,
            1.21, 1.23, 1.24, 1.26, 1.27, 1.29, 1.30, 1.32, 1.33, 1.35, 1.37, 1.38, 1.40, 1.42, 1.43, 1.45,
            1.47, 1.49, 1.50, 1.52, 1.54, 1.56, 1.58, 1.60, 1.62, 1.64, 1.65, 1.67, 1.69, 1.72, 1.74, 1.76,
            1.78, 1.80, 1.82, 1.84, 1.87, 1.89, 1.91, 1.93, 1.96, 1.98, 2.00, 2.03, 2.05, 2.08, 2.10, 2.13,
            2.15, 2.18, 2.21, 2.23, 2.26, 2.29, 2.32, 2.34, 2.37, 2.40, 2.43, 2.46, 2.49, 2.52, 2.55, 2.58,
            2.61, 2.64, 2.67, 2.71, 2.74, 2.77, 2.80, 2.84, 2.87, 2.91, 2.94, 2.98, 3.01, 3.05, 3.09, 3.12,
            3.16, 3.20, 3.24, 3.28, 3.32, 3.36, 3.40, 3.44, 3.48, 3.52, 3.57, 3.61, 3.65, 3.70, 3.74, 3.79,
            3.83, 3.88, 3.92, 3.97, 4.02, 4.07, 4.12, 4.17, 4.22, 4.27, 4.32, 4.37, 4.42, 4.48, 4.53, 4.59,
            4.64, 4.70, 4.75, 4.81, 4.87, 4.93, 4.99, 5.05, 5.11, 5.17, 5.23, 5.30, 5.36, 5.42, 5.49, 5.56,
            5.62, 5.69, 5.76, 5.83, 5.90, 5.97, 6.04, 6.12, 6.19, 6.26, 6.34, 6.42, 6.49, 6.57, 6.65, 6.73,
            6.81, 6.90, 6.98, 7.06, 7.15, 7.23, 7.32, 7.41, 7.50, 7.59, 7.68, 7.77, 7.87, 7.96, 8.06, 8.16,
            8.25, 8.35, 8.45, 8.56, 8.66, 8.76, 8.87, 8.98, 9.09, 9.20, 9.31, 9.42, 9.53, 9.65, 9.76, 9.88
        ]
        self.multipliers = [1, 10, 100, 1000, 10000, 100000, 1000000]
        self.full_e96_resistors = self._generate_full_series(self.e96_series)
        self.full_e192_resistors = self._generate_full_series(self.e192_series)

    def _generate_full_series(self, base_series):
        full_series = set()
        for m in self.multipliers:
            for r in base_series:
                full_series.add(round(r * m, 9))
        return sorted(list(full_series))

    def find_resistors(self, v_in, v_out_target, max_error=0.01):
        if v_in <= v_out_target or v_out_target <= 0:
            raise ValueError("输入错误: 源电压必须大于目标电压，且目标电压必须大于0。")
        target_ratio = (v_in / v_out_target) - 1
        resistor_list = self.full_e96_resistors
        results = []
        for r1 in resistor_list:
            for r2 in resistor_list:
                if not (1000 <= r1 + r2 <= 2000000):
                    continue
                actual_ratio = r1 / r2
                if target_ratio == 0:
                    error = abs(actual_ratio)
                else:
                    error = abs(actual_ratio - target_ratio) / target_ratio
                if error < max_error:
                    v_out_actual = v_in * r2 / (r1 + r2)
                    results.append({
                        'R1': r1,
                        'R2': r2,
                        'V_out_actual': v_out_actual,
                        'error_percent': error * 100
                    })
        return sorted(results, key=lambda x: x['error_percent'])

    @staticmethod
    def format_resistor_value(r_val):
        if r_val >= 1_000_000:
            return f"{r_val / 1_000_000:g} MΩ"
        elif r_val >= 1_000:
            return f"{r_val / 1_000:g} kΩ"
        else:
            return f"{r_val:g} Ω"
