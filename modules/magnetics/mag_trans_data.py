# mag_trans_data.py

from PyQt5.QtWidgets import QComboBox

# 定义磁材 Steinmetz 系数 (Approx @ 100°C)
# Pv [mW/cm^3] = k * f(kHz)^alpha * B(mT)^beta
MATERIALS_DB = {
    "PC40 (TDK)":  {'k': 0.0350, 'a': 1.63, 'b': 2.68},
    "PC95 (TDK)":  {'k': 0.3500, 'a': 1.45, 'b': 2.45}, # 宽温/低损耗
    "3C90 (Ferroxcube)": {'k': 0.0320, 'a': 1.46, 'b': 2.75},
    "3C94 (Ferroxcube)": {'k': 0.0280, 'a': 1.50, 'b': 2.70},
    "N87 (Epcos)": {'k': 0.0270, 'a': 1.60, 'b': 2.70},
    "Custom (自定义)": {'k': 0.0, 'a': 0.0, 'b': 0.0}
}

# 统一磁芯数据库 (Name, Ae mm^2, Aw mm^2, Ve mm^3)
# AP = Ae * Aw / 100 (cm^4)
CORE_DB = [
    ("EE13", 17.1, 28.0, 764), ("EE16", 19.0, 34.0, 954), ("EE19", 23.0, 38.0, 1150),
    ("EE25", 41.0, 78.0, 2350), ("EE28", 86.0, 137.0, 5260), ("EE30", 109.0, 150.0, 6800),
    ("EI28", 86.0, 137.0, 5260), ("EI33", 119.0, 175.0, 9680),
    ("RM8", 64.0, 42.0, 2440), ("RM10", 98.0, 45.0, 4310),
    ("PQ2016", 62.0, 26.0, 2310), ("PQ2020", 62.0, 48.0, 3030),
    ("PQ2620", 119.0, 43.0, 5350), ("PQ2625", 118.0, 45.0, 6530),
    ("PQ3220", 170.0, 56.0, 9360), ("PQ3230", 161.0, 93.0, 11970),
    ("PQ3535", 196.0, 115.0, 22400), ("PQ4040", 201.0, 148.0, 33200)
]

def create_core_selector(ae_widget, aw_widget, ve_widget=None):
    """
    创建一个通用的磁芯选择下拉框，并绑定到对应的 QLineEdit 上
    """
    combo = QComboBox()
    combo.addItem("自定义磁芯 (手动输入)", (0, 0, 0))
    
    for name, ae, aw, ve in CORE_DB:
        combo.addItem(f"{name} (Ae={ae}, Ve={ve})", (ae, aw, ve))
        
    def on_change():
        data = combo.currentData()
        if data != (0, 0, 0):
            if ae_widget: ae_widget.setText(str(data[0]))
            if aw_widget: aw_widget.setText(str(data[1]))
            if ve_widget: ve_widget.setText(str(data[2]))
            
    combo.currentIndexChanged.connect(on_change)
    return combo