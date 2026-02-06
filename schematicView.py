from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QPen, QColor
from PyQt6.QtCore import Qt, QRect, QTimer, QPointF

class CircuitSchematic(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumHeight(200)
        
        # Variáveis de Estado
        self.cable_type = "Coaxial" 
        self.full_cable_name = "RG-58 (Coaxial)" # Nome para exibição
        self.length = 2.0
        self.load_type = "Z"
        self.gamma = 0.0 
        
        # Variáveis de Animação
        self.anim_offset = 0.0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(50) 

    def update_animation(self):
        self.anim_offset += 2.0 
        if self.anim_offset > 40: 
            self.anim_offset = 0
        self.update()

    def update_schematic(self, cable_name, length, load_type, gamma_mag):
        is_power = "Linha Aérea" in cable_name
        self.cable_type = "Power" if is_power else "Coaxial"
        self.full_cable_name = cable_name # Guarda o nome completo para a legenda
        self.length = length
        self.load_type = load_type
        self.gamma = gamma_mag 
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w = self.width()
        h = self.height()
        cy = h // 2 

        # 1. Background
        self.draw_blueprint_background(painter, w, h)

        # 2. Componentes Principais
        self.draw_source(painter, 60, cy)

        start_x = 100
        end_x = w - 100
        
        if self.cable_type == "Power":
            self.draw_power_line(painter, start_x, end_x, cy)
        else:
            self.draw_coaxial(painter, start_x, end_x, cy)

        # 3. Fluxo de Energia
        self.draw_energy_flow(painter, start_x, end_x, cy)

        # 4. Carga
        self.draw_load(painter, end_x, cy)
        
        # 5. Legenda (NOVO)
        self.draw_legend(painter)

    def draw_legend(self, p):
        """ Desenha a caixa de legenda no canto superior esquerdo """
        # Configurações da caixa
        x, y = 10, 10
        w, h = 260, 85
        
        # Fundo semitransparente para leitura fácil
        p.setPen(QPen(QColor(255, 255, 255, 50), 1))
        p.setBrush(QColor(0, 0, 0, 150)) # Preto transparente
        p.drawRoundedRect(x, y, w, h, 5, 5)
        
        # Fonte para a legenda
        font = p.font()
        font.setPointSize(9)
        p.setFont(font)
        
        # 1. Nome do Cabo
        p.setPen(QColor("white"))
        font.setBold(True); p.setFont(font)
        p.drawText(x + 10, y + 20, "Configuração Atual:")
        font.setBold(False); p.setFont(font)
        # Corta o texto se for muito longo
        display_name = (self.full_cable_name[:35] + '..') if len(self.full_cable_name) > 35 else self.full_cable_name
        p.drawText(x + 10, y + 38, display_name)
        
        # 2. Onda Incidente (Azul/Ciano)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor("#7FDBFF")) # Ciano
        p.drawEllipse(x + 15, y + 50, 6, 6) # Bolinha
        
        p.setPen(QColor("#DDDDDD")) # Texto cinza claro
        p.drawText(x + 30, y + 58, "Onda Transmitida (Incidente)")
        
        # 3. Onda Refletida (Vermelha)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor("#FF4136")) # Vermelho
        p.drawEllipse(x + 15, y + 68, 6, 6) # Bolinha
        
        p.setPen(QColor("#DDDDDD"))
        p.drawText(x + 30, y + 76, "Onda Refletida (Se houver)")

    def draw_blueprint_background(self, p, w, h):
        p.fillRect(0, 0, w, h, QColor("#001f3f"))
        p.setPen(QPen(QColor(255, 255, 255, 30), 1, Qt.PenStyle.DotLine))
        grid_size = 40
        for x in range(0, w, grid_size): p.drawLine(x, 0, x, h)
        for y in range(0, h, grid_size): p.drawLine(0, y, w, y)

    def draw_source(self, p, x, cy):
        p.setPen(QPen(QColor("#FFD700"), 2))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QPointF(x, cy), 30, 30)
        p.drawText(QRect(int(x-20), int(cy-15), 40, 30), Qt.AlignmentFlag.AlignCenter, "~")
        p.drawLine(int(x), int(cy-30), int(x), int(cy-40))
        p.drawLine(int(x), int(cy+30), int(x), int(cy+40))
        p.setPen(QColor("white"))
        p.drawText(int(x-25), int(cy+60), "FONTE")

    def draw_load(self, p, x, cy):
        rect = QRect(int(x), int(cy-30), 50, 60)
        p.setPen(QPen(QColor("#FF4136"), 2))
        p.setBrush(QColor(0, 0, 0, 100))
        p.drawRect(rect)
        p.setPen(QColor("white"))
        font = p.font(); font.setBold(True); p.setFont(font)
        p.drawText(rect, Qt.AlignmentFlag.AlignCenter, "ZL")
        font.setBold(False); font.setPointSize(8); p.setFont(font)
        p.drawText(int(x), int(cy+50), self.load_type)

    def draw_coaxial(self, p, x1, x2, cy):
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(255, 255, 255, 20))
        p.drawRect(x1, cy-20, x2-x1, 40)
        p.setPen(QPen(QColor("#AAAAAA"), 2))
        p.drawLine(x1, cy-20, x2, cy-20)
        p.drawLine(x1, cy+20, x2, cy+20)
        p.setPen(QPen(QColor("#0074D9"), 4))
        p.drawLine(x1, cy, x2, cy)
        p.setPen(QPen(QColor("#FFD700"), 2))
        p.drawLine(60, cy-40, x1, cy-20)
        p.drawLine(60, cy+40, x1, cy+20)

    def draw_power_line(self, p, x1, x2, cy):
        p.setPen(QPen(QColor("#000000"), 3))
        off = 40
        p.setPen(QPen(QColor("#DDDDDD"), 2))
        p.drawLine(x1, cy-off, x2, cy-off)
        p.drawLine(x1, cy,     x2, cy)
        p.drawLine(x1, cy+off, x2, cy+off)
        
        dist = x2 - x1
        num_towers = int(dist / 150)
        step = dist / (num_towers + 1)
        for i in range(1, num_towers + 1):
            self.draw_tower_icon(p, x1 + i * step, cy)
            
        p.setPen(QPen(QColor("#FFD700"), 1, Qt.PenStyle.DashLine))
        p.drawLine(60, cy-40, x1, cy-off)
        p.drawLine(60, cy+40, x1, cy+off)

    def draw_tower_icon(self, p, x, cy):
        p.setPen(QPen(QColor("#888888"), 2))
        p.drawLine(int(x), int(cy-60), int(x-20), int(cy+80))
        p.drawLine(int(x), int(cy-60), int(x+20), int(cy+80))
        p.drawLine(int(x-30), int(cy-40), int(x+30), int(cy-40))
        p.drawLine(int(x-30), int(cy),     int(x+30), int(cy))
        p.drawLine(int(x-30), int(cy+40), int(x+30), int(cy+40))

    def draw_energy_flow(self, p, x1, x2, cy):
        if self.cable_type == "Power": y_offsets = [-40, 0, 40]
        else: y_offsets = [0]
            
        spacing = 40 
        
        # --- ONDA INCIDENTE ---
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor("#7FDBFF")) 
        
        curr_x = x1 + (self.anim_offset % spacing)
        while curr_x < x2:
            for y_off in y_offsets:
                p.drawEllipse(QPointF(curr_x, cy + y_off), 4, 4)
            curr_x += spacing

        # --- ONDA REFLETIDA ---
        if self.gamma > 0.01:
            alpha = int(min(255, self.gamma * 255))
            p.setBrush(QColor(255, 65, 54, alpha)) 
            
            rev_x = x2 - (self.anim_offset % spacing)
            while rev_x > x1:
                for y_off in y_offsets:
                    p.drawEllipse(QPointF(rev_x, cy + y_off + 3), 4, 4)
                rev_x -= spacing