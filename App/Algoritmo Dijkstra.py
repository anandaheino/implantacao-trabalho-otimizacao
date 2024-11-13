import pandas as pd
import os
from geopy.distance import geodesic
import heapq
from collections import defaultdict

# Caminho relativo ao diretório do script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Carregar os dados de escolas e candidatos
escolas_df = pd.read_csv(os.path.join(script_dir, 'escolas_gps.csv'))
candidatos_df = pd.read_csv(os.path.join(script_dir, 'candidatos_gps.csv'))

# Função para calcular a distância entre duas coordenadas geográficas
def calcular_distancia(coord1, coord2):
    return geodesic(coord1, coord2).kilometers

# Criar um grafo completo com distâncias entre cada candidato e cada escola
grafo = defaultdict(list)
for _, candidato in candidatos_df.iterrows():
    coord_candidato = (candidato['Latitude'], candidato['Longitude'])
    for idx, escola in escolas_df.iterrows():
        coord_escola = (escola['Latitude'], escola['Longitude'])
        distancia = calcular_distancia(coord_candidato, coord_escola)
        grafo[candidato['Nome']].append((distancia, idx, escola['Nome_Escola']))

# Função para o algoritmo de Dijkstra com atualizações de capacidade
def dijkstra_completo(grafo, candidatos_df, escolas_df):
    alocacoes = []
    distancia_total = 0

    # Min-heap para processar nós pela menor distância acumulada
    heap = []
    
    # Inicializa o heap com todos os candidatos, distância inicial 0
    for _, candidato in candidatos_df.iterrows():
        candidato_nome = candidato['Nome']
        for distancia, idx_escola, nome_escola in grafo[candidato_nome]:
            heapq.heappush(heap, (distancia, candidato_nome, idx_escola, nome_escola))
    
    # Dicionário para verificar se o candidato já foi alocado
    candidatos_alocados = set()

    # Executa o Dijkstra
    while heap and len(candidatos_alocados) < len(candidatos_df):
        distancia, candidato_nome, idx_escola, nome_escola = heapq.heappop(heap)
        
        # Se o candidato já foi alocado, pula para o próximo
        if candidato_nome in candidatos_alocados:
            continue

        # Verifica se a escola ainda tem vagas
        if escolas_df.loc[idx_escola, 'Vagas'] > 0:
            # Registra a alocação
            alocacoes.append({
                'Nome_Candidato': candidato_nome,
                'Escola_Alocada': nome_escola,
                'Distancia_km': distancia
            })
            distancia_total += distancia

            # Atualiza o estado
            escolas_df.at[idx_escola, 'Vagas'] -= 1
            candidatos_alocados.add(candidato_nome)
    
    return alocacoes, distancia_total

# Executa o Dijkstra e obtém as alocações e a distância total
alocacoes, distancia_total = dijkstra_completo(grafo, candidatos_df, escolas_df)

# Salvar as alocações em um arquivo CSV
alocacoes_df = pd.DataFrame(alocacoes)
alocacoes_path = os.path.join(script_dir, 'alocacao_candidatos_escolas.csv')
alocacoes_df.to_csv(alocacoes_path, index=False)

# Exibir a distância total
print(f"Alocações registradas em '{alocacoes_path}'")
print(f"Distância total: {distancia_total} km")
