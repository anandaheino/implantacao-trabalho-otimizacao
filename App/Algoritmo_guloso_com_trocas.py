import pandas as pd
import os
from pyproj import Proj, transform
from scipy.spatial.distance import euclidean
# removendo futurewarning
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
import time


# tempo inicial
start_time = time.time()

# Caminho relativo ao diretório do script
script_dir = os.path.dirname(os.path.abspath(__file__))

# # dataset 1
path_candidatos = '1_candidatos_10'
path_escolas = '1_escolas_5'
# # dataset 2 
path_candidatos = '2_candidatos_100'
path_escolas = '2_escolas_25'
# # dataset 3
path_candidatos = '3_candidatos_1000'
path_escolas = '3_escolas_50'
# # dataset 4
path_candidatos = '4_candidatos_10000'
path_escolas = '4_escolas_100'

# Carregar os dados de escolas e candidatos
escolas_df = pd.read_csv(os.path.join(script_dir, f'../dados/{path_escolas}.csv'), encoding='latin1')
candidatos_df = pd.read_csv(os.path.join(script_dir, f'../dados/{path_candidatos}.csv'), encoding='latin1')

# Configurar a projeção UTM para a zona 23S (apropriada para o Rio de Janeiro e região)
utm_proj = Proj(proj="utm", zone=23, south=True, ellps="WGS84")
wgs84_proj = Proj(proj="latlong", datum="WGS84")

# Função para converter coordenadas para UTM
def converter_para_utm(lat, lon):
    x, y = transform(wgs84_proj, utm_proj, lon, lat)
    return x, y

# Converter coordenadas dos candidatos e das escolas para UTM
candidatos_df[['UTM_X', 'UTM_Y']] = candidatos_df.apply(lambda row: converter_para_utm(row['Latitude'], row['Longitude']), axis=1, result_type="expand")
escolas_df[['UTM_X', 'UTM_Y']] = escolas_df.apply(lambda row: converter_para_utm(row['Latitude'], row['Longitude']), axis=1, result_type="expand")

# Função para calcular a distância total de uma alocação
def calcular_distancia_total(alocacao):
    distancia_total = sum([a['Distancia_km'] for a in alocacao])
    return distancia_total

# Função de alocação inicial com restrição de vagas
def alocacao_inicial():
    alocacao = []
    vagas_restantes = escolas_df['Vagas'].to_dict()  # Controle de vagas por escola
    # para cada candidato, alocar na escola mais próxima com vagas
    for i, candidato in candidatos_df.iterrows():
        menor_distancia = float('inf')
        melhor_escola = None
        
        for j, escola in escolas_df.iterrows():
            # Verifica se a escola ainda tem vagas
            if vagas_restantes[j] > 0:
                distancia = euclidean(
                    (candidato['UTM_X'], candidato['UTM_Y']),
                    (escola['UTM_X'], escola['UTM_Y'])
                ) / 1000
                if distancia < menor_distancia:
                    menor_distancia = distancia
                    melhor_escola = j
        
        # Aloca o candidato à melhor escola disponível
        if melhor_escola is not None:
            alocacao.append({'Nome_Candidato': i, 'Escola_Alocada': melhor_escola, 'Distancia_km': menor_distancia})
            vagas_restantes[melhor_escola] -= 1  # Atualiza as vagas restantes

    return alocacao

def swap_based_greedy():
    # Alocação inicial
    alocacao = alocacao_inicial()
    melhor_distancia_total = calcular_distancia_total(alocacao)

    # Copiar a alocação inicial para preservá-la
    alocacao_atual = alocacao[:]
    melhoria = True  # Controla se ainda há melhorias possíveis

    iteracoes = 0  # Contador de iterações
    trocas_realizadas = 0  # Contador de trocas feitas

    while melhoria:
        melhoria = False  # Assume que não há melhoria até encontrar uma troca válida

        for i in range(len(alocacao_atual)):
            for j in range(i + 1, len(alocacao_atual)):
                # Pega os candidatos e escolas da alocação atual
                candidato1 = alocacao_atual[i]
                candidato2 = alocacao_atual[j]
                escola1 = candidato1['Escola_Alocada']
                escola2 = candidato2['Escola_Alocada']

                # Calcula as novas distâncias se trocarmos os candidatos de escolas
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

                # Calcula o impacto da troca
                distancia_atual = candidato1['Distancia_km'] + candidato2['Distancia_km']
                distancia_nova = nova_distancia_candidato1 + nova_distancia_candidato2

                # Se a troca reduz a distância total, aplica a troca
                if distancia_nova < distancia_atual:
                    alocacao_atual[i]['Escola_Alocada'] = escola2
                    alocacao_atual[i]['Distancia_km'] = nova_distancia_candidato1
                    alocacao_atual[j]['Escola_Alocada'] = escola1
                    alocacao_atual[j]['Distancia_km'] = nova_distancia_candidato2

                    melhor_distancia_total -= (distancia_atual - distancia_nova)  # Atualiza a melhor distância
                    melhoria = True  # Marcamos que houve melhoria
                    trocas_realizadas += 1  # Incrementa o contador de trocas
                    break  # Quebra para verificar novamente o processo de otimização
            if melhoria:
                break  # Sai do laço externo se houve melhoria

        iteracoes += 1  # Incrementa o número de iterações

    # Métricas de desempenho
    print(f"Iterações: {iteracoes}")
    print(f"Trocas realizadas: {trocas_realizadas}")
    print(f"Melhor distância total encontrada: {melhor_distancia_total:.2f} km")

    return alocacao_atual, melhor_distancia_total


# Executar o algoritmo
melhor_alocacao, melhor_distancia_total = swap_based_greedy()

# Salvar a melhor alocação em um arquivo CSV
melhor_alocacao_df = pd.DataFrame(melhor_alocacao)

# Map do nome do candidato com o índice
dict_nome_candidato = candidatos_df['Nome'].to_dict()
melhor_alocacao_df['Nome_Candidato'] = melhor_alocacao_df['Nome_Candidato'].map(dict_nome_candidato)

# Map do nome da escola com o índice
dict_nome_escola = escolas_df['Nome_Escola'].to_dict()
melhor_alocacao_df['Escola_Alocada'] = melhor_alocacao_df['Escola_Alocada'].map(dict_nome_escola)

# ordenando pelo nome da escola
melhor_alocacao_df = melhor_alocacao_df.sort_values(by='Escola_Alocada')

melhor_alocacao_df.to_csv(os.path.join(script_dir, f'../dados/saidas/{path_candidatos}_swap_based_greedy.csv'), index=False, sep=';', decimal=',')

tempo_final = time.time() - start_time

print(f"Distância total Swap Based Greedy {path_candidatos}: {round(melhor_distancia_total, 2)} km")
print(f"Tempo de execução: {tempo_final:.2f} segundos")
