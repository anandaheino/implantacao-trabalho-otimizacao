import pandas as pd
import os
import numpy as np
from pyproj import Proj, Transformer
from scipy.spatial.distance import euclidean
from scipy.optimize import linear_sum_assignment
from tqdm import tqdm
import matplotlib.pyplot as plt
import time

# Caminho relativo ao diretório do script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Carregar os dados de escolas e candidatos
escolas_df = pd.read_csv(os.path.join(script_dir, 'escolas_50_gps.csv'))
candidatos_df = pd.read_csv(os.path.join(script_dir, 'candidatos_1000_gps.csv'))

# Configurar as projeções e o transformador UTM para a zona 23S (Rio de Janeiro e região)
utm_proj = Proj(proj="utm", zone=23, south=True, ellps="WGS84")
wgs84_proj = Proj(proj="latlong", datum="WGS84")
transformer = Transformer.from_proj(wgs84_proj, utm_proj)

# Converter coordenadas para UTM usando Transformer e aplicar no DataFrame
def converter_para_utm(lat, lon):
    return transformer.transform(lat, lon)

candidatos_df[['UTM_X', 'UTM_Y']] = candidatos_df.apply(
    lambda row: converter_para_utm(row['Latitude'], row['Longitude']), axis=1, result_type="expand"
)
escolas_df[['UTM_X', 'UTM_Y']] = escolas_df.apply(
    lambda row: converter_para_utm(row['Latitude'], row['Longitude']), axis=1, result_type="expand"
)

# Função para calcular a distância entre candidato e escola
def calcular_distancia(candidato, escola):
    return euclidean((candidato['UTM_X'], candidato['UTM_Y']), (escola['UTM_X'], escola['UTM_Y'])) / 1000

# Função para calcular a distância total de uma alocação
def calcular_distancia_total(alocacao):
    return sum(candidato['Distancia_km'] for candidato in alocacao)

# Função para construir a matriz expandida de custos
def construir_matriz_expandida(candidatos_df, escolas_df):
    matriz_distancias_expandida = []
    escolas_expandida = []

    for _, candidato in tqdm(candidatos_df.iterrows(), total=len(candidatos_df), desc="Calculando ..."):
        distancias_candidato = []
        for escola_idx, escola in escolas_df.iterrows():
            num_vagas = escola['Vagas']
            distancia = calcular_distancia(candidato, escola)
            distancias_candidato.extend([distancia] * num_vagas)
            escolas_expandida.extend([escola_idx] * num_vagas)
        matriz_distancias_expandida.append(distancias_candidato)
    
    return np.array(matriz_distancias_expandida), escolas_expandida

# Algoritmo Húngaro
def algoritmo_hungaro(candidatos_df, escolas_df):
    start_time = time.time()
    matriz_distancias_expandida, escolas_expandida = construir_matriz_expandida(candidatos_df, escolas_df)
    linhas, colunas = linear_sum_assignment(matriz_distancias_expandida)

    alocacao_resultado = []
    distancia_total = 0
    distancias_por_tempo = []
    contagem_vagas = {escola: 0 for escola in escolas_df.index}

    for candidato_idx, escola_expandidx in zip(linhas, colunas):
        escola_idx = escolas_expandida[escola_expandidx]
        if contagem_vagas[escola_idx] < escolas_df.loc[escola_idx, 'Vagas']:
            distancia = matriz_distancias_expandida[candidato_idx][escola_expandidx]
            distancia_total += distancia
            distancias_por_tempo.append((time.time() - start_time, distancia_total))
            contagem_vagas[escola_idx] += 1

    execution_time = time.time() - start_time
    return distancias_por_tempo, execution_time

# Algoritmo Guloso
def algoritmo_guloso(candidatos_df, escolas_df):
    start_time = time.time()
    distancia_total = 0
    distancias_por_tempo = []
    vagas_ocupadas = {escola_idx: 0 for escola_idx in escolas_df.index}

    for _, candidato in candidatos_df.iterrows():
        melhor_escola = None
        menor_distancia = float('inf')
        for escola_idx, escola in escolas_df.iterrows():
            if vagas_ocupadas[escola_idx] < escola['Vagas']:
                distancia = calcular_distancia(candidato, escola)
                if distancia < menor_distancia:
                    menor_distancia = distancia
                    melhor_escola = escola_idx

        if melhor_escola is not None:
            vagas_ocupadas[melhor_escola] += 1
            distancia_total += menor_distancia
            distancias_por_tempo.append((time.time() - start_time, distancia_total))

    total_time = time.time() - start_time
    return distancias_por_tempo, total_time

# Algoritmo Swap-Based Greedy
def alocacao_inicial():
    alocacao = []
    vagas_restantes = escolas_df['Vagas'].to_dict()
    for i, candidato in candidatos_df.iterrows():
        menor_distancia = float('inf')
        melhor_escola = None
        for j, escola in escolas_df.iterrows():
            if vagas_restantes[j] > 0:
                distancia = euclidean(
                    (candidato['UTM_X'], candidato['UTM_Y']),
                    (escola['UTM_X'], escola['UTM_Y'])
                ) / 1000
                if distancia < menor_distancia:
                    menor_distancia = distancia
                    melhor_escola = j

        if melhor_escola is not None:
            alocacao.append({'Nome_Candidato': i, 'Escola_Alocada': melhor_escola, 'Distancia_km': menor_distancia})
            vagas_restantes[melhor_escola] -= 1
    return alocacao

def swap_based_greedy():
    alocacao = alocacao_inicial()
    melhor_distancia_total = calcular_distancia_total(alocacao)
    alocacao_atual = alocacao[:]
    melhoria = True
    distancias_por_tempo = []
    start_time = time.time()

    while melhoria:
        melhoria = False
        for i in range(len(alocacao_atual)):
            for j in range(i + 1, len(alocacao_atual)):
                candidato1 = alocacao_atual[i]
                candidato2 = alocacao_atual[j]
                escola1 = candidato1['Escola_Alocada']
                escola2 = candidato2['Escola_Alocada']

                nova_distancia_candidato1 = euclidean(
                    (candidatos_df.loc[candidato1['Nome_Candidato'], 'UTM_X'],
                     candidatos_df.loc[candidato1['Nome_Candidato'], 'UTM_Y']),
                    (escolas_df.loc[escola2, 'UTM_X'],
                     escolas_df.loc[escola2, 'UTM_Y'])
                ) / 1000

                nova_distancia_candidato2 = euclidean(
                    (candidatos_df.loc[candidato2['Nome_Candidato'], 'UTM_X'],
                     candidatos_df.loc[candidato2['Nome_Candidato'], 'UTM_Y']),
                    (escolas_df.loc[escola1, 'UTM_X'],
                     escolas_df.loc[escola1, 'UTM_Y'])
                ) / 1000

                distancia_atual = candidato1['Distancia_km'] + candidato2['Distancia_km']
                distancia_nova = nova_distancia_candidato1 + nova_distancia_candidato2

                if distancia_nova < distancia_atual:
                    alocacao_atual[i]['Escola_Alocada'] = escola2
                    alocacao_atual[i]['Distancia_km'] = nova_distancia_candidato1
                    alocacao_atual[j]['Escola_Alocada'] = escola1
                    alocacao_atual[j]['Distancia_km'] = nova_distancia_candidato2
                    melhor_distancia_total -= (distancia_atual - distancia_nova)
                    melhoria = True
                    break
            if melhoria:
                break

        distancias_por_tempo.append((time.time() - start_time, melhor_distancia_total))
    total_time = time.time() - start_time  # Fim do cálculo de tempo
    return alocacao_atual, melhor_distancia_total, distancias_por_tempo, total_time

# Executar os algoritmos
distancias_hungaro, tempo_hungaro = algoritmo_hungaro(candidatos_df, escolas_df)
distancias_guloso, tempo_guloso = algoritmo_guloso(candidatos_df, escolas_df)
melhor_alocacao, melhor_distancia_total, distancias_greedy, tempo_swap = swap_based_greedy()

# Resultados
print(f"Algoritmo Húngaro:\n  Distância Total (km): {distancias_hungaro[-1][1]:.2f}\n  Tempo de Execução (s): {tempo_hungaro:.2f}")
print(f"Algoritmo Guloso:\n  Distância Total (km): {distancias_guloso[-1][1]:.2f}\n  Tempo de Execução (s): {tempo_guloso:.2f}")
print(f"Swap-Based Greedy:\n  Distância Total (km): {melhor_distancia_total:.2f}\n  Tempo de Execução (s): {tempo_swap:.2f}")

# Gráfico comparando os algoritmos
plt.figure(figsize=(12, 8))

# Adicionar as curvas de evolução da distância total para cada algoritmo
plt.plot(*zip(*distancias_hungaro), label="Algoritmo Húngaro", color='blue', linewidth=2)
plt.plot(*zip(*distancias_guloso), label="Algoritmo Guloso", color='green', linewidth=2)
plt.plot(*zip(*distancias_greedy), label="Swap-Based Greedy", color='orange', linewidth=2)

# Configurações do gráfico
plt.title("Comparação: Distância Total vs Tempo de Execução")
plt.xlabel("Tempo de Execução (segundos)")
plt.ylabel("Distância Total (km)")
plt.legend()
plt.grid(True)
plt.tight_layout()

# Mostrar o gráfico
plt.show()

