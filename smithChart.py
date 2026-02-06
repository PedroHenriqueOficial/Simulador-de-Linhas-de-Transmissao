import numpy as np
from matplotlib.patches import Circle

def draw_smith_chart_background(ax):
    """Desenha a grade da Carta de Smith manualmente no eixo fornecido."""
    ax.set_aspect('equal')
    ax.axis('off')
    
    # Círculo unitário (borda externa)
    ax.add_patch(Circle((0, 0), 1, color='k', fill=False, linewidth=2))
    ax.plot([-1, 1], [0, 0], 'k', linewidth=1) # Eixo horizontal
    
    # Círculos de Resistência Constante (r)
    # Centros: (r / (r+1), 0)
    # Raios: 1 / (r+1)
    r_vals = [0.2, 0.5, 1.0, 2.0, 5.0]
    for r in r_vals:
        center = (r / (r + 1), 0)
        radius = 1 / (r + 1)
        ax.add_patch(Circle(center, radius, color='gray', fill=False, linestyle=':', alpha=0.5))

    # Arcos de Reatância Constante (x)
    # Centros: (1, 1/x)
    # Raios: 1/x
    x_vals = [0.2, 0.5, 1.0, 2.0, 5.0]
    for x in x_vals:
        # Reatância indutiva (positiva, parte superior)
        # Precisamos clipar para desenhar apenas dentro do círculo unitário
        # Uma forma rápida é plotar parametricamente a impedância z = r + jx
        # variando r de 0 a infinito para um x fixo.
        
        r_sweep = np.linspace(0, 100, 300)
        z_iso_x = r_sweep + 1j * x
        gamma_iso_x = (z_iso_x - 1) / (z_iso_x + 1)
        ax.plot(gamma_iso_x.real, gamma_iso_x.imag, 'gray', linestyle=':', alpha=0.5)
        
        # Reatância capacitiva (negativa)
        z_iso_neg_x = r_sweep - 1j * x
        gamma_iso_neg_x = (z_iso_neg_x - 1) / (z_iso_neg_x + 1)
        ax.plot(gamma_iso_neg_x.real, gamma_iso_neg_x.imag, 'gray', linestyle=':', alpha=0.5)

    # Marcação de curto e aberto
    ax.text(-1.1, 0, "Curto (0)", fontsize=8, ha='right')
    ax.text(1.1, 0, "Aberto (inf)", fontsize=8, ha='left')