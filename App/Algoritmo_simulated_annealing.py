import pandas as pd
import os
from pyproj import Proj, transform
from scipy.spatial.distance import euclidean
import warnings
import time
import random
import math
from tqdm import tqdm

# removendo futurewarning
warnings.simplefilter(action='ignore', category=FutureWarning)

# Função para converter coordenadas para UTM
def converter_para_utm(lat, lon):
    x, y = transform(wgs84_proj, utm_proj, lon, lat)
    return x, y

# Função para calcular a distância total de uma alocação
def calcular_distancia_total(alocacao):
    distancia_total = sum([a['Distancia_km'] for a in alocacao])
    return distancia_total

# Função de alocação inicial (baseada na menor distância para cada candidato)
def alocacao_inicial():
    alocacao = []
    for i, candidato in candidatos_df.iterrows():
        menor_distancia = float('inf')
        melhor_escola = None
        for j, escola in escolas_df.iterrows():
            distancia = euclidean((candidato['UTM_X'], candidato['UTM_Y']), (escola['UTM_X'], escola['UTM_Y'])) / 1000
            if distancia < menor_distancia:
                menor_distancia = distancia
                melhor_escola = j
        alocacao.append({'Nome_Candidato': i, 'Escola_Alocada': melhor_escola, 'Distancia_km': menor_distancia})
    return alocacao

# Função de busca Simulated Annealing
def simulated_annealing_search(
    temperatura_inicial=temperatura_inicial, 
    taxa_resfriamento=taxa_resfriamento, 
    max_iter=max_iter
):
    # Iniciando a alocação inicial e a melhor distância total
    alocacao = alocacao_inicial()
    melhor_distancia_total = calcular_distancia_total(alocacao)
    temperatura = temperatura_inicial

    # Loop principal do Simulated Annealing
    for _ in range(max_iter):
        # Faz uma cópia da alocação atual e realiza uma troca aleatória
        nova_alocacao = alocacao[:]
        i = random.randint(0, len(alocacao) - 1)
        nova_alocacao[i]['Escola_Alocada'] = random.randint(0, len(escolas_df) - 1)
        
        # Recalcula a distância para o candidato modificado
        candidato_i = candidatos_df.iloc[nova_alocacao[i]['Nome_Candidato']]
        # print(candidato_i)
        escola_i = escolas_df.iloc[nova_alocacao[i]['Escola_Alocada']]
        nova_alocacao[i]['Distancia_km'] = euclidean((candidato_i['UTM_X'], candidato_i['UTM_Y']), (escola_i['UTM_X'], escola_i['UTM_Y'])) / 1000
        
        nova_distancia_total = calcular_distancia_total(nova_alocacao)
        
        # Critério de aceitação com Simulated Annealing
        delta = nova_distancia_total - melhor_distancia_total
        # se a diferença for negativa ou se a probabilidade for maior que um número aleatório entre 0 e 1
        if delta < 0 or random.uniform(0, 1) < math.exp(-delta / temperatura):
            # Aceitamos a nova alocação
            alocacao = nova_alocacao
            # Atualizamos a melhor distância total
            melhor_distancia_total = nova_distancia_total
        
        # Reduz a temperatura após cada iteração
        temperatura *= taxa_resfriamento
        # print("Temperatura:",temperatura)
        # Condição de término se a temperatura for muito baixa
        if temperatura < 0.1:  
            break

    return alocacao, melhor_distancia_total


if __name__ == '__main__':
    
    # tempo inicial
    start_time = time.time()

    # Caminho relativo ao diretório do script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # setando o numero de candidatos pelo nome do dataset
    n_candidatos = 30000
    escolas_df = pd.read_csv(os.path.join(script_dir, 'escolas_204.csv'), encoding='latin1')
    candidatos_df = pd.read_csv(os.path.join(script_dir, f'candidatos_{n_candidatos}.csv'), encoding='latin1')

    # Configurar a projeção UTM para a zona 23S (apropriada para o Rio de Janeiro e região)
    utm_proj = Proj(proj="utm", zone=23, south=True, ellps="WGS84")
    wgs84_proj = Proj(proj="latlong", datum="WGS84")

    # Converter coordenadas dos candidatos e das escolas para UTM
    candidatos_df[['UTM_X', 'UTM_Y']] = candidatos_df.apply(lambda row: converter_para_utm(row['Latitude'], row['Longitude']), axis=1, result_type="expand")
    escolas_df[['UTM_X', 'UTM_Y']] = escolas_df.apply(lambda row: converter_para_utm(row['Latitude'], row['Longitude']), axis=1, result_type="expand")

    # trabalhando com 80% do limite total de iterações, resultando um numero inteiro
    max_iter = int((candidatos_df.shape[0] * escolas_df.shape[0]) * 0.8)
    temperatura_inicial = 1000
    taxa_resfriamento = 0.9

    # Executar o algoritmo e exibir o resultado
    melhor_alocacao, melhor_distancia_total = simulated_annealing_search()

    print(f"Distância total Simulated Annealing: {round(melhor_distancia_total,0)} km")
    print("Máx iterações:",max_iter)
    print("Temperatura inicial:",temperatura_inicial)
    print("Taxa de resfriamento:",taxa_resfriamento)

    # Salvar a melhor alocação em um arquivo CSV
    melhor_alocacao_df = pd.DataFrame(melhor_alocacao)

    # Map do nome do candidato com o indice
    dict_nome_candidato = candidatos_df['Nome'].to_dict()
    melhor_alocacao_df['Nome_Candidato'] = melhor_alocacao_df['Nome_Candidato'].map(dict_nome_candidato)

    # Map do nome da escola com o indice
    dict_nome_escola = escolas_df['Nome_Escola'].to_dict()
    melhor_alocacao_df['Escola_Alocada'] = melhor_alocacao_df['Escola_Alocada'].map(dict_nome_escola)

    melhor_alocacao_df.to_csv(os.path.join(script_dir, f'melhor_alocacao_simulated_annealing_{n_candidatos}.csv'), index=False)
    print(f"Arquivo 'melhor_alocacao_simulated_annealing_{n_candidatos}.csv' gerado com sucesso.")

    # tempo final
    tempo_final = time.time()
    t_min = (tempo_final - start_time) // 60
    t_sec = (tempo_final - start_time) % 60
    print(f"Tempo total de processamento: {t_min:.0f} minuto(s) e {t_sec:.2f} segundo(s).")
