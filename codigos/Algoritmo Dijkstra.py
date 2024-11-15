import pandas as pd
import os
from geopy.distance import geodesic
import heapq

# Caminho relativo ao diretório do script
script_dir = os.path.dirname(os.path.abspath(__file__))
# Carregar os dados de escolas e candidatos
escolas_df = pd.read_csv(os.path.join(script_dir, 'micro_Escolas_com_vagas_gps.csv'))
candidatos_df = pd.read_csv(os.path.join(script_dir, 'micro_candidatos_concurso_lat_long.csv'))

# Função para calcular a distância entre duas coordenadas geográficas
def calcular_distancia(coord1, coord2):
    return geodesic(coord1, coord2).kilometers

# Pré-computar as distâncias entre cada candidato e cada escola
distancias = []
for _, candidato in candidatos_df.iterrows():
    coord_candidato = (candidato['Latitude'], candidato['Longitude'])
    for idx, escola in escolas_df.iterrows():
        coord_escola = (escola['Latitude'], escola['Longitude'])
        distancia = calcular_distancia(coord_candidato, coord_escola)
        distancias.append({
            'Nome_Candidato': candidato['Nome'],
            'Indice_Escola': idx,
            'Nome_Escola': escola['Nome_Escola'],
            'Distancia_km': distancia
        })

# Converter as distâncias em um DataFrame para melhor manipulação
distancias_df = pd.DataFrame(distancias)

# Função Dijkstra para encontrar a escola mais próxima com vagas para um candidato
def dijkstra_para_candidato(candidato_nome, distancias_df, escolas_df):
    # Filtrar as distâncias para o candidato atual
    distancias_candidato = distancias_df[distancias_df['Nome_Candidato'] == candidato_nome]

    # Min-heap para selecionar a menor distância
    heap = [(row['Distancia_km'], row['Indice_Escola'], row['Nome_Escola']) for _, row in distancias_candidato.iterrows()]
    heapq.heapify(heap)  # Organizar o heap pela menor distância

    # Processar as escolas pela menor distância até encontrar uma com vagas
    while heap:
        distancia, idx_escola, nome_escola = heapq.heappop(heap)
        if escolas_df.loc[idx_escola, 'Vagas'] > 0:
            return distancia, idx_escola, nome_escola  # Retorna a escola mais próxima com vaga

    return None, None, None  # Caso não haja escola com vagas

# Lista para armazenar as alocações e variável para a distância total
alocacoes = []
distancia_total = 0

# Processar cada candidato e alocar na escola mais próxima disponível
for _, candidato in candidatos_df.iterrows():
    distancia_mais_proxima, idx_escola_mais_proxima, nome_escola = dijkstra_para_candidato(candidato['Nome'], distancias_df, escolas_df)

    if idx_escola_mais_proxima is not None:
        # Registrar a alocação
        alocacoes.append({
            'Nome_Candidato': candidato['Nome'],
            'Escola_Alocada': nome_escola,
            'Distancia_km': distancia_mais_proxima
        })
        
        # Incrementar a distância total
        distancia_total += distancia_mais_proxima

        # Reduzir o número de vagas na escola escolhida
        escolas_df.at[idx_escola_mais_proxima, 'Vagas'] -= 1

# Salvar as alocações em um arquivo CSV
alocacoes_df = pd.DataFrame(alocacoes)
alocacoes_path = os.path.join(script_dir, 'alocacao_candidatos_escolas.csv')
alocacoes_df.to_csv(alocacoes_path, index=False)

# Exibir a distância total
print("Alocações registradas em 'C:\\Users\\lukas\\Desktop\\alocacao_candidatos_escolas.csv'")
print(f"Distância total: {distancia_total} km")