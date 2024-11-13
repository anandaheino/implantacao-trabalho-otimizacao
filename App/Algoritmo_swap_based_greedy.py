import pandas as pd
import os
from pyproj import Proj, transform
from scipy.spatial.distance import euclidean
# removendo futurewarning
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

# alocacoes.append({
#     'Nome_Candidato': candidato_nome,
#     'Escola_Alocada': nome_escola,
#     'Distancia_km': distancia
# })
# Caminho relativo ao diretório do script
script_dir = os.path.dirname(os.path.abspath(__file__))

# for rodada in range(1, 11):
# Carregar os dados de escolas e candidatos
escolas_df = pd.read_csv(os.path.join(script_dir, 'escolas_gps.csv'))
candidatos_df = pd.read_csv(os.path.join(script_dir, 'candidatos_gps.csv'))

# # randomizando o dataframe de candidatos
# candidatos_df = candidatos_df.sample(frac=1).reset_index(drop=True)
# escolas_df = escolas_df.sample(frac=1).reset_index(drop=True)

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

# Implementação do algoritmo Swap-based Greedy
def swap_based_greedy():
    alocacao = alocacao_inicial()
    melhor_distancia_total = calcular_distancia_total(alocacao)
    melhorou = True
    
    while melhorou:
        melhorou = False
        for i in range(len(alocacao)):
            for j in range(i + 1, len(alocacao)):
                # Troca de alocação entre os candidatos i e j
                alocacao_temp = alocacao[:]
                alocacao_temp[i], alocacao_temp[j] = alocacao_temp[j], alocacao_temp[i]

                # Recalcula a distância para os candidatos trocados
                candidato_i = candidatos_df.iloc[alocacao_temp[i]['Nome_Candidato']]
                candidato_j = candidatos_df.iloc[alocacao_temp[j]['Nome_Candidato']]
                
                escola_i = escolas_df.iloc[alocacao_temp[i]['Escola_Alocada']]
                escola_j = escolas_df.iloc[alocacao_temp[j]['Escola_Alocada']]
                
                distancia_i = euclidean((candidato_i['UTM_X'], candidato_i['UTM_Y']), (escola_i['UTM_X'], escola_i['UTM_Y'])) / 1000
                distancia_j = euclidean((candidato_j['UTM_X'], candidato_j['UTM_Y']), (escola_j['UTM_X'], escola_j['UTM_Y'])) / 1000
                
                alocacao_temp[i]['Distancia_km'] = distancia_i
                alocacao_temp[j]['Distancia_km'] = distancia_j

                nova_distancia_total = calcular_distancia_total(alocacao_temp)

                # Se a troca resultou em uma menor distância, aplicar a troca
                if nova_distancia_total < melhor_distancia_total:
                    alocacao = alocacao_temp
                    melhor_distancia_total = nova_distancia_total
                    melhorou = True

    return alocacao, melhor_distancia_total

# Executar o algoritmo e exibir o resultado
melhor_alocacao, melhor_distancia_total = swap_based_greedy()

# print(f"Rodada {rodada}")
print(f"Distância total Swap Based Greedy: {round(melhor_distancia_total,0)} km")
# print("________________________________________")

# Salvar a melhor alocação em um arquivo CSV
melhor_alocacao_df = pd.DataFrame(melhor_alocacao)

# Map do nome do candidato com o indice
dict_nome_candidato = candidatos_df['Nome'].to_dict()
melhor_alocacao_df['Nome_Candidato'] = melhor_alocacao_df['Nome_Candidato'].map(dict_nome_candidato)

# Map do nome da escola com o indice
dict_nome_escola = escolas_df['Nome_Escola'].to_dict()
melhor_alocacao_df['Escola_Alocada'] = melhor_alocacao_df['Escola_Alocada'].map(dict_nome_escola)

melhor_alocacao_df.to_csv(os.path.join(script_dir, 'melhor_alocacao_swap_based_greedy.csv'), index=False)
print("Arquivo 'melhor_alocacao_swap_based_greedy.csv' gerado com sucesso.")
