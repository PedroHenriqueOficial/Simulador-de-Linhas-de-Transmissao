import sys
import numpy as np
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget, 
                             QFormLayout, QLineEdit, QPushButton, 
                             QHBoxLayout, QComboBox, QSlider, QLabel, QGroupBox, 
                             QMessageBox, QStackedWidget, QListWidget, QFileDialog)
from PyQt6.QtCore import Qt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# --- IMPORTS DOS NOSSOS MÓDULOS ---
from physicsEngine import AdvancedTransmissionLine
from smithChart import draw_smith_chart_background
from schematicView import CircuitSchematic

# --- BIBLIOTECA DE CABOS ---
CABLE_LIBRARY = {
    "Personalizado": {"R_dc": 0.01, "L": 250e-9, "G": 0, "C": 100e-12, "k_skin": 0},
    "RG-58 (Coaxial 50 Ohms)": {"R_dc": 0.03, "L": 250e-9, "G": 0, "C": 100e-12, "k_skin": 1.5e-4},
    "RG-59 (Coaxial 75 Ohms)": {"R_dc": 0.05, "L": 370e-9, "G": 0, "C": 67e-12, "k_skin": 1.8e-4},
    "CAT-5 (Par Trançado)":    {"R_dc": 0.18, "L": 520e-9, "G": 0, "C": 52e-12,  "k_skin": 3.0e-4},
    "Microstrip (PCB Típico)": {"R_dc": 0.50, "L": 350e-9, "G": 0, "C": 130e-12, "k_skin": 5.0e-4},
    "Linha Aérea (Alta Tensão)": {"R_dc": 0.05, "L": 1.3e-6, "G": 0, "C": 9e-12, "k_skin": 2.0e-4},
}

class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simulador de Linhas de Transmissão")
        self.resize(1300, 850)
        
        # Estado Inicial
        self.current_freq = 100e6    
        self.current_len = 2.0       
        self.cable_params = CABLE_LIBRARY["RG-58 (Coaxial 50 Ohms)"]
        self.load_type = "Constante (Z)"
        self.zl_const = 100 - 50j
        self.rlc_params = {"R": 50.0, "L": 100e-9, "C": 10e-12}

        # --- LAYOUT PRINCIPAL ---
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # ==========================================
        # PAINEL ESQUERDO (CONTROLES + NAVEGAÇÃO)
        # ==========================================
        panel_left = QWidget()
        panel_left.setFixedWidth(320)
        layout_left = QVBoxLayout(panel_left)
        layout_left.setSpacing(8)
        
        # --- 0. NAVEGAÇÃO & AÇÕES (Padronizado) ---
        group_nav = QGroupBox("0. Visualização / Ações")
        layout_nav = QVBoxLayout()
        layout_nav.setContentsMargins(0, 12, 0, 0)
        
        self.list_nav = QListWidget()
        self.list_nav.addItems([
            "Desenho Esquemático",    # Index 0
            "Ondas Estacionárias",    # Index 1
            "Carta de Smith",         # Index 2
            "Análise Espectral",      # Index 3
            "Exportar Imagem (PNG)"   # Index 4 (Ação)
        ])
        self.list_nav.setCurrentRow(0)
        
        # Aumentei altura para caber 5 itens sem scroll (35px * 5 ≈ 175)
        self.list_nav.setFixedHeight(180) 
        self.list_nav.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.list_nav.setStyleSheet("""
            QListWidget { 
                font-size: 14px; 
                font-weight: bold; 
                background-color: transparent;
                border: none; 
            }
            QListWidget::item { 
                padding: 8px 5px; 
                margin-bottom: 2px;
                border-radius: 4px;
            }
            QListWidget::item:selected { 
                background-color: #0074D9; 
                color: white; 
            }
            QListWidget::item:hover { 
                background-color: #E0E0E0; 
                color: black; 
            }
        """)
        self.list_nav.currentRowChanged.connect(self.change_view)
        layout_nav.addWidget(self.list_nav)
        group_nav.setLayout(layout_nav)
        layout_left.addWidget(group_nav)

        # 1. Seleção de Cabo
        group_cables = QGroupBox("1. Cabo / Linha")
        layout_cables = QVBoxLayout()
        self.combo_cables = QComboBox()
        self.combo_cables.addItems(CABLE_LIBRARY.keys())
        self.combo_cables.setCurrentText("RG-58 (Coaxial 50 Ohms)")
        self.combo_cables.currentTextChanged.connect(self.on_cable_changed)
        layout_cables.addWidget(self.combo_cables)
        group_cables.setLayout(layout_cables)
        layout_left.addWidget(group_cables)

        # 2. Configuração de Carga
        group_load = QGroupBox("2. Carga (Load)")
        layout_load = QVBoxLayout()
        layout_load.setContentsMargins(5, 5, 5, 5)
        
        self.combo_load_type = QComboBox()
        self.combo_load_type.addItems(["Constante (Z)", "RLC Série", "RLC Paralelo"])
        self.combo_load_type.currentTextChanged.connect(self.on_load_type_changed)
        layout_load.addWidget(self.combo_load_type)
        
        self.stack_load_inputs = QStackedWidget()
        # Pág Z
        page_z = QWidget()
        form_z = QFormLayout(page_z)
        form_z.setContentsMargins(0,5,0,0)
        self.in_z_real = QLineEdit("100"); self.in_z_imag = QLineEdit("-50")
        form_z.addRow("Real (Ω):", self.in_z_real)
        form_z.addRow("Imag (Ω):", self.in_z_imag)
        self.stack_load_inputs.addWidget(page_z)
        # Pág RLC
        page_rlc = QWidget()
        form_rlc = QFormLayout(page_rlc)
        form_rlc.setContentsMargins(0,5,0,0)
        self.in_r = QLineEdit("50"); self.in_l = QLineEdit("100e-9"); self.in_c = QLineEdit("10e-12")
        form_rlc.addRow("R (Ω):", self.in_r)
        form_rlc.addRow("L (H):", self.in_l)
        form_rlc.addRow("C (F):", self.in_c)
        self.stack_load_inputs.addWidget(page_rlc)
        
        layout_load.addWidget(self.stack_load_inputs)
        
        btn_update_load = QPushButton("Aplicar Carga")
        btn_update_load.clicked.connect(self.on_load_update)
        layout_load.addWidget(btn_update_load)
        group_load.setLayout(layout_load)
        layout_left.addWidget(group_load)

        # 3. Sliders
        group_params = QGroupBox("3. Ajustes em Tempo Real")
        layout_params = QVBoxLayout()
        
        self.lbl_freq = QLabel(f"Freq: {self.current_freq/1e6:.1f} MHz")
        self.slider_freq = QSlider(Qt.Orientation.Horizontal)
        self.slider_freq.setRange(1, 500)
        self.slider_freq.setValue(100)
        self.slider_freq.valueChanged.connect(self.on_freq_changed)
        layout_params.addWidget(self.lbl_freq); layout_params.addWidget(self.slider_freq)

        self.lbl_len = QLabel(f"Comp: {self.current_len:.2f} m")
        self.slider_len = QSlider(Qt.Orientation.Horizontal)
        self.slider_len.setRange(1, 10000) 
        self.slider_len.setValue(200) 
        self.slider_len.valueChanged.connect(self.on_len_changed)
        layout_params.addWidget(self.lbl_len); layout_params.addWidget(self.slider_len)
        group_params.setLayout(layout_params)
        layout_left.addWidget(group_params)

        # 4. Métricas
        group_metrics = QGroupBox("4. Resultados / Métricas")
        layout_metrics = QFormLayout()
        
        style_val = "color: white; font-weight: bold; background-color: #333; padding: 2px; border-radius: 4px;"
        
        self.lbl_z0 = QLabel("---"); self.lbl_z0.setStyleSheet(style_val)
        self.lbl_zin = QLabel("---"); self.lbl_zin.setStyleSheet(style_val)
        self.lbl_gamma = QLabel("---"); self.lbl_gamma.setStyleSheet(style_val)
        self.lbl_vswr = QLabel("---"); self.lbl_vswr.setStyleSheet(style_val)
        self.lbl_rl = QLabel("---"); self.lbl_rl.setStyleSheet(style_val)
        
        layout_metrics.addRow("Z0 (Linha):", self.lbl_z0)
        layout_metrics.addRow("Zin (Entrada):", self.lbl_zin)
        layout_metrics.addRow("Reflexão (Γ):", self.lbl_gamma)
        layout_metrics.addRow("VSWR:", self.lbl_vswr)
        layout_metrics.addRow("Ret. Loss (dB):", self.lbl_rl)
        
        self.btn_stub = QPushButton("Calcular Stub Casador")
        self.btn_stub.clicked.connect(self.calculate_stub_match)
        layout_metrics.addRow(self.btn_stub)
        
        group_metrics.setLayout(layout_metrics)
        layout_left.addWidget(group_metrics)
        
        main_layout.addWidget(panel_left)

        # ==========================================
        # PAINEL DIREITO (STACKED WIDGET)
        # ==========================================
        
        self.stack_views = QStackedWidget()
        main_layout.addWidget(self.stack_views)
        
        # 1. Desenho Esquemático
        self.view_schematic = QWidget()
        layout_schem = QVBoxLayout(self.view_schematic)
        self.schematic = CircuitSchematic() 
        layout_schem.addWidget(self.schematic)
        
        # 2. Gráficos
        self.view_wave = QWidget(); self.setup_tab(self.view_wave, "Ondas")
        self.view_smith = QWidget(); self.setup_tab(self.view_smith, "Smith")
        self.view_sweep = QWidget(); self.setup_tab(self.view_sweep, "Sweep")
        
        self.stack_views.addWidget(self.view_schematic) # 0
        self.stack_views.addWidget(self.view_wave)      # 1
        self.stack_views.addWidget(self.view_smith)     # 2
        self.stack_views.addWidget(self.view_sweep)     # 3
        
        draw_smith_chart_background(self.ax_smith)
        self.on_load_update() 

    def setup_tab(self, widget, type_name):
        layout = QVBoxLayout(widget)
        fig = Figure()
        canvas = FigureCanvas(fig)
        layout.addWidget(canvas)
        
        if type_name == "Ondas":
            self.fig_wave = fig; self.canvas_wave = canvas; self.ax_wave = fig.add_subplot(111)
        elif type_name == "Smith":
            self.fig_smith = fig; self.canvas_smith = canvas; self.ax_smith = fig.add_subplot(111)
        elif type_name == "Sweep":
            self.fig_sweep = fig; self.canvas_sweep = canvas
            self.ax_sweep_mag = fig.add_subplot(211)
            self.ax_sweep_phase = fig.add_subplot(212)
            fig.subplots_adjust(hspace=0.4)

    # --- LÓGICA DE NAVEGAÇÃO ---
    def change_view(self, row):
        # Indices 0 a 3 são visualizações reais
        if row <= 3:
            self.stack_views.setCurrentIndex(row)
        else:
            # Index 4 é o botão de EXPORTAR
            self.export_current_view()
            
            # Truque de UX: Retorna a seleção para a aba que estava antes
            # para não ficar "preso" no botão de exportar
            current_view_index = self.stack_views.currentIndex()
            # Bloqueia sinais para não chamar change_view recursivamente
            self.list_nav.blockSignals(True) 
            self.list_nav.setCurrentRow(current_view_index)
            self.list_nav.blockSignals(False)

    # --- LÓGICA DE EXPORTAÇÃO ---
    def export_current_view(self):
        current_widget = self.stack_views.currentWidget()
        filename, _ = QFileDialog.getSaveFileName(self, "Salvar Imagem", "simulacao.png", "Images (*.png)")
        if filename:
            pixmap = current_widget.grab()
            pixmap.save(filename)
            QMessageBox.information(self, "Sucesso", f"Imagem salva com sucesso!")

    # --- LÓGICA DE NEGÓCIO ---
    def get_load_impedance(self, freqs):
        omega = 2 * np.pi * freqs
        if self.load_type == "Constante (Z)":
            return np.full_like(freqs, self.zl_const, dtype=complex)
        elif self.load_type == "RLC Série":
            R, L, C = self.rlc_params["R"], self.rlc_params["L"], self.rlc_params["C"]
            Xc = np.divide(1.0, (omega * C), out=np.zeros_like(omega), where=omega!=0)
            return R + 1j * (omega * L - Xc)
        elif self.load_type == "RLC Paralelo":
            R, L, C = self.rlc_params["R"], self.rlc_params["L"], self.rlc_params["C"]
            G = 1.0 / R
            Bl = np.divide(1.0, (omega * L), out=np.zeros_like(omega), where=omega!=0)
            Bc = omega * C
            Y = G + 1j * (Bc - Bl)
            return np.divide(1.0, Y, out=np.full_like(Y, 1e9), where=Y!=0)

    def calculate_physics(self):
        p = self.cable_params
        line = AdvancedTransmissionLine(p['R_dc'], p['L'], p['G'], p['C'], self.current_len, p['k_skin'])
        
        f_arr = np.array([self.current_freq])
        Z0_vec, gamma_vec = line.compute_params(f_arr)
        Z0, gamma = Z0_vec[0], gamma_vec[0]
        ZL = self.get_load_impedance(f_arr)[0]
        
        term = np.tanh(gamma * self.current_len)
        Zin = Z0 * (ZL + Z0 * term) / (Z0 + ZL * term)
        Gamma_L = (ZL - Z0) / (ZL + Z0)
        
        abs_gamma = abs(Gamma_L)
        deg_gamma = np.degrees(np.angle(Gamma_L))
        if abs_gamma >= 1: vswr = 99.9
        else: vswr = (1 + abs_gamma) / (1 - abs_gamma)
        rl_db = -20 * np.log10(abs_gamma) if abs_gamma > 1e-9 else 99.9

        # Atualiza Labels
        self.lbl_z0.setText(f"{Z0.real:.1f} {Z0.imag:+.1f}j Ω")
        self.lbl_zin.setText(f"{Zin.real:.1f} {Zin.imag:+.1f}j Ω")
        self.lbl_gamma.setText(f"{abs_gamma:.3f} ∠ {deg_gamma:.1f}°")
        self.lbl_vswr.setText(f"{vswr:.2f} : 1")
        self.lbl_rl.setText(f"{rl_db:.1f} dB")
        
        # Atualiza o Esquemático 
        self.schematic.update_schematic(self.combo_cables.currentText(), self.current_len, self.load_type, abs_gamma)
        
        # Plot Ondas
        x = np.linspace(0, self.current_len, 200)
        d = self.current_len - x
        V_d = np.exp(gamma * d) + Gamma_L * np.exp(-gamma * d)
        
        self.ax_wave.clear()
        self.ax_wave.plot(x, np.abs(V_d), color='#0055aa', linewidth=2)
        self.ax_wave.set_title(f"Tensão ao longo da linha (f={self.current_freq/1e6:.0f} MHz)")
        self.ax_wave.set_xlabel("Distância da Fonte (m)")
        self.ax_wave.set_ylabel("|V| Normalizado")
        self.ax_wave.grid(True, linestyle='--', alpha=0.5)
        self.canvas_wave.draw()
        
        # Plot Smith
        self.ax_smith.clear()
        draw_smith_chart_background(self.ax_smith)
        dist_sweep = np.linspace(0, self.current_len, 100)
        Gamma_d = Gamma_L * np.exp(-2 * gamma * dist_sweep)
        self.ax_smith.plot(Gamma_d.real, Gamma_d.imag, 'r-', lw=2, label='Trajetória')
        self.ax_smith.plot(Gamma_d[0].real, Gamma_d[0].imag, 'go', label='Carga')
        self.ax_smith.plot(Gamma_d[-1].real, Gamma_d[-1].imag, 'bo', label='Entrada')
        self.ax_smith.legend(fontsize='small')
        self.canvas_smith.draw()
        
        self.update_frequency_sweep()

    def update_frequency_sweep(self):
        freqs = np.linspace(1e6, 500e6, 300)
        p = self.cable_params
        line = AdvancedTransmissionLine(p['R_dc'], p['L'], p['G'], p['C'], self.current_len, p['k_skin'])
        Z0_vec, gamma_vec = line.compute_params(freqs)
        ZL_vec = self.get_load_impedance(freqs)
        
        term = np.tanh(gamma_vec * self.current_len)
        Zin_vec = Z0_vec * (ZL_vec + Z0_vec * term) / (Z0_vec + ZL_vec * term)
        
        mag = np.abs(Zin_vec)
        phase = np.angle(Zin_vec, deg=True)
        
        self.ax_sweep_mag.clear()
        self.ax_sweep_mag.plot(freqs/1e6, mag, 'k-', lw=1.5)
        self.ax_sweep_mag.set_ylabel("|Zin| (Ω)")
        self.ax_sweep_mag.grid(True, alpha=0.5)
        
        self.ax_sweep_phase.clear()
        self.ax_sweep_phase.plot(freqs/1e6, phase, 'r-', lw=1.5)
        self.ax_sweep_phase.set_ylabel("Fase (°)")
        self.ax_sweep_phase.set_xlabel("Freq (MHz)")
        self.ax_sweep_phase.grid(True, alpha=0.5)
        
        self.ax_sweep_mag.axvline(self.current_freq/1e6, color='b', linestyle='--')
        self.canvas_sweep.draw()

    def calculate_stub_match(self):
        freq = self.current_freq
        w_len = 3e8 / freq 
        d_sweep = np.linspace(0, w_len/2, 500)
        p = self.cable_params
        Z0_real = np.sqrt(p['L']/p['C'])
        Y0 = 1/Z0_real
        beta = 2*np.pi * freq * np.sqrt(p['L']*p['C'])
        ZL = self.get_load_impedance(np.array([freq]))[0]
        
        Gamma_L = (ZL - Z0_real) / (ZL + Z0_real)
        Gamma_d = Gamma_L * np.exp(-2j * beta * d_sweep)
        Y_d = 1.0 / (Z0_real * (1 + Gamma_d) / (1 - Gamma_d))
        
        idx_match = np.argmin(np.abs(Y_d.real - Y0))
        d_best = d_sweep[idx_match]
        B_stub_needed = -Y_d[idx_match].imag
        
        if B_stub_needed == 0: val = 0
        else: val = -Y0 / B_stub_needed
        theta = np.arctan(val)
        while theta < 0: theta += np.pi
        l_stub = theta / beta
        
        msg = (f"=== Casamento (Stub em Curto) ===\n\n"
               f"1. Posição (T): {d_best*100:.2f} cm da carga\n"
               f"2. Comprimento Stub: {l_stub*100:.2f} cm")
        QMessageBox.information(self, "Resultado Stub", msg)

    # --- HANDLERS ---
    def on_load_type_changed(self, text):
        self.load_type = text
        idx = 0 if text == "Constante (Z)" else 1
        self.stack_load_inputs.setCurrentIndex(idx)
    def on_load_update(self):
        try:
            if self.load_type == "Constante (Z)":
                self.zl_const = complex(float(self.in_z_real.text()), float(self.in_z_imag.text()))
            else:
                self.rlc_params["R"] = float(self.in_r.text())
                self.rlc_params["L"] = float(self.in_l.text())
                self.rlc_params["C"] = float(self.in_c.text())
            self.calculate_physics()
        except ValueError: pass
    def on_cable_changed(self, text):
        self.cable_params = CABLE_LIBRARY[text]
        self.calculate_physics()
    def on_freq_changed(self):
        self.current_freq = self.slider_freq.value() * 1e6 
        self.lbl_freq.setText(f"Freq: {self.current_freq/1e6:.1f} MHz")
        self.calculate_physics()
    def on_len_changed(self):
        self.current_len = self.slider_len.value() / 100.0
        self.lbl_len.setText(f"Comp: {self.current_len:.2f} m")
        self.calculate_physics()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainApp()
    window.show()
    sys.exit(app.exec())