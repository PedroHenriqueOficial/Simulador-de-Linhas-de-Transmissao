import numpy as np

class AdvancedTransmissionLine:
    def __init__(self, R_dc, L_inf, G, C_inf, length, skin_factor=0):
        """
        R_dc: Resistência DC (Ohms/m)
        skin_factor: Coeficiente k onde R_ac = R_dc + k * sqrt(f)
        """
        self.R_dc = R_dc
        self.L = L_inf
        self.G = G
        self.C = C_inf
        self.len = length
        self.k_skin = skin_factor

    def compute_params(self, frequencies):
        """
        Calcula os parâmetros secundários (Z0, gamma) para um ARRAY de frequências.
        Essencial para TDR.
        """
        omega = 2 * np.pi * frequencies
        
        # Modelo de Efeito Pelicular: R aumenta com a raiz da frequência
        # Nota: L interna também varia ligeiramente, mas R é o dominante.
        R_f = self.R_dc + self.k_skin * np.sqrt(frequencies)
        
        # Parâmetros distribuídos vetoriais
        Z_series = R_f + 1j * omega * self.L
        Y_shunt = self.G + 1j * omega * self.C
        
        # Evitar divisão por zero em DC (f=0)
        # Em DC, Z0 = sqrt(R/G) se G!=0, ou infinito/indefinido se G=0.
        # Tratamento numérico simples: adicionar epsilon pequeno
        with np.errstate(divide='ignore', invalid='ignore'):
            Z0 = np.sqrt(Z_series / Y_shunt)
            gamma = np.sqrt(Z_series * Y_shunt)
        
        # Correção para DC (índice 0 se frequência começar em 0)
        if frequencies[0] == 0:
            if self.G > 0:
                Z0[0] = np.sqrt(self.R_dc / self.G)
            else:
                Z0[0] = 50.0 # Valor padrão resistivo para evitar NaN numérico
            gamma[0] = 0 # DC não propaga fase, apenas atenuação se houver R
            
        return Z0, gamma

    def get_tdr_response(self, V_source_mag, Z_source, Z_load_func, t_max=100e-9, points=1024):
        """
        Simula a TDR injetando um DEGRAU.
        Retorna: tempo (t), tensão na entrada V_in(t)
        
        Z_load_func: Uma função que aceita frequências e retorna Z_load(f)
                     Isso permite cargas reativas (ex: capacitor).
        """
        # 1. Configurar eixo da frequência para FFT
        # df = 1 / T_total. Para ter boa resolução no tempo, precisamos de banda larga.
        f_max = points / t_max / 2
        freqs = np.linspace(0, f_max, points)
        
        # 2. Calcular parâmetros da linha para todas as frequências
        Z0_f, gamma_f = self.compute_params(freqs)
        
        # 3. Calcular Impedância de Entrada (Zin) para todas as frequências
        ZL_f = Z_load_func(freqs)
        tanh_gl = np.tanh(gamma_f * self.len)
        Zin_f = Z0_f * (ZL_f + Z0_f * tanh_gl) / (Z0_f + ZL_f * tanh_gl)
        
        # 4. Função de Transferência na entrada da linha (Divisor de Tensão)
        # V_in(f) = V_source(f) * [Zin / (Zin + Zs)]
        # Para um degrau unitário, V_source(f) ~ 1/(jw), mas usamos abordagem de pulso gaussiano ou similar
        # para evitar singularidades, ou construímos o degrau no tempo depois.
        
        H_input = Zin_f / (Zin_f + Z_source)
        
        # 5. Criar o sinal de estímulo (Degrau) no domínio da frequência
        # Método alternativo robusto: Sintetizar degrau suavizado
        t = np.linspace(0, t_max, 2*points - 2)
        # Usamos irfft (Inverse Real FFT) do numpy
        
        # Estimativa simples: A resposta ao degrau é a integral da resposta ao impulso.
        # Aqui, faremos a IFFT da resposta ao sistema multiplicada pelo espectro do degrau.
        # Para simplificar: aplicamos um degrau filtrado (sigmóide) no tempo e fazemos a convolução via FFT.
        
        # Abordagem simplificada para visualização TDR:
        # V_in(t) é a resposta à reflexão.
        pass # A implementação completa de TDR requer janelamento cuidadoso.
             # Posso fornecer o código completo dessa parte específica se desejar focar aqui.
             # Por ora, focaremos na estrutura.
             
        return freqs, H_input # Retornando H(f) para análise inicial