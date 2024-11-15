import pandas as pd
import os
from pyproj import Proj, Transformer
from scipy.spatial.distance import euclidean
from scipy.optimize import linear_sum_assignment
from tqdm import tqdm
import numpy as np

# Caminho relativo ao diretório do script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Carregar os dados de escolas e candidatos
escolas_df = pd.read_csv(os.path.join(script_dir, 'escolas_150_gps.csv'))
candidatos_df = pd.read_csv(os.path.join(script_dir, 'candidatos_3000_gps.csv'))

# Configurar as projeções e o transformador UTM para a zona 23S (Rio de Janeiro e região)
utm_proj = Proj(proj="utm", zone=23, south=True, ellps="WGS84")
wgs84_proj = Proj(proj="latlong", datum="WGS84")
transformer = Transformer.from_proj(wgs84_proj, utm_proj)

# Converter coordenadas para UTM usando Transformer e aplicar no DataFrame
def converter_para_utm(lat, lon):
    return transformer.transform(lat, lon)

# Aplicar a conversão para UTM nos candidatos e escolas
candidatos_df[['UTM_X', 'UTM_Y']] = candidatos_df.apply(lambda row: converter_para_utm(row['Latitude'], row['Longitude']), axis=1, result_type="expand")
escolas_df[['UTM_X', 'UTM_Y']] = escolas_df.apply(lambda row: converter_para_utm(row['Latitude'], row['Longitude']), axis=1, result_type="expand")

# Função para calcular a distância entre candidato e escola
def calcular_distancia(candidato, escola):
    return euclidean((candidato['UTM_X'], candidato['UTM_Y']), (escola['UTM_X'], escola['UTM_Y'])) / 1000

# Expandir a matriz de custos considerando o limite de vagas por escola
def construir_matriz_expandida(candidatos_df, escolas_df):
    matriz_distancias_expandida = []
    escolas_expandida = []

    for _, candidato in tqdm(candidatos_df.iterrows(), total=len(candidatos_df), desc="Calculando matriz expandida de distâncias"):
        distancias_candidato = []
        for escola_idx, escola in escolas_df.iterrows():
            num_vagas = escola['Vagas']
            # Replicar a distância conforme o número de vagas da escola
            distancia = calcular_distancia(candidato, escola)
            distancias_candidato.extend([distancia] * num_vagas)
            escolas_expandida.extend([escola_idx] * num_vagas)
        matriz_distancias_expandida.append(distancias_candidato)
    
    return np.array(matriz_distancias_expandida), escolas_expandida

# Construir a matriz expandida e aplicar o Algoritmo Húngaro
matriz_distancias_expandida, escolas_expandida = construir_matriz_expandida(candidatos_df, escolas_df)
linhas, colunas = linear_sum_assignment(matriz_distancias_expandida)

# Criar DataFrame com os resultados da alocação
alocacao_resultado = []
distancia_total = 0

# Contar quantas alocações foram feitas para cada escola e respeitar o limite de vagas
contagem_vagas = {escola: 0 for escola in escolas_df.index}

for candidato_idx, escola_expandidx in zip(linhas, colunas):
    escola_idx = escolas_expandida[escola_expandidx]
    if contagem_vagas[escola_idx] < escolas_df.loc[escola_idx, 'Vagas']:
        distancia = matriz_distancias_expandida[candidato_idx][escola_expandidx]
        distancia_total += distancia
        alocacao_resultado.append({
            'Escola_Alocada': escolas_df.loc[escola_idx, 'Nome_Escola'],
            'Nome_Candidato': candidatos_df.loc[candidato_idx, 'Nome'],
            'Distancia': distancia
        })
        contagem_vagas[escola_idx] += 1

# Salvar o resultado em um arquivo CSV
alocacao_df = pd.DataFrame(alocacao_resultado)
alocacao_df_path = os.path.join(script_dir, 'alocacao_candidatos_escolas_otimizado_distancia_total.csv')
alocacao_df.to_csv(alocacao_df_path, index=False)

# Exibir a distância total
print(f"Distância total de alocação: {distancia_total:.2f} km")
print("Arquivo 'alocacao_candidatos_escolas_otimizado_distancia_total.csv' gerado com sucesso.")
