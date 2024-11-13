import pandas as pd
import os
from pyproj import Proj, transform
from scipy.spatial.distance import euclidean

# Caminho relativo ao diretório do script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Carregar os dados de escolas e candidatos
escolas_df = pd.read_csv(os.path.join(script_dir, 'escolas_gps.csv'))
candidatos_df = pd.read_csv(os.path.join(script_dir, 'candidatos_gps.csv'))

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

# Criar uma lista de arestas com as distâncias entre cada candidato e cada escola
arestas = []
for i, candidato in candidatos_df.iterrows():
    for j, escola in escolas_df.iterrows():
        # Calcular a distância euclidiana entre o candidato e a escola no sistema UTM e converter para km
        distancia = euclidean((candidato['UTM_X'], candidato['UTM_Y']), (escola['UTM_X'], escola['UTM_Y'])) / 1000  # em km
        arestas.append({'candidato': i, 'escola': j, 'distancia': distancia})

# Ordenar as arestas pela menor distância para aplicar o algoritmo de Kruskal
arestas = sorted(arestas, key=lambda x: x['distancia'])

# Inicializar a capacidade das escolas com base na coluna "Vagas"
capacidade_restante = escolas_df['Vagas'].to_dict()

# Estrutura para armazenar a AGM final e pai para união
agm = []
pai = list(range(len(candidatos_df) + len(escolas_df)))
distancia_total = 0  # Variável para acumular a distância total

# Funções para encontrar e unir (usado em Kruskal)
def find(v):
    if pai[v] != v:
        pai[v] = find(pai[v])
    return pai[v]

def union(u, v):
    raiz_u = find(u)
    raiz_v = find(v)
    if raiz_u != raiz_v:
        pai[raiz_u] = raiz_v

# Construir a AGM respeitando a capacidade das escolas
for aresta in arestas:
    candidato = aresta['candidato']
    escola = aresta['escola'] + len(candidatos_df)  # Índice ajustado para escola
    distancia = aresta['distancia']
    
    # Verificar se a escola ainda tem capacidade e se o candidato e a escola não estão na mesma componente
    if capacidade_restante[aresta['escola']] > 0 and find(candidato) != find(escola):
        union(candidato, escola)
        agm.append({
            'Nome_Candidato': candidatos_df.iloc[candidato]['Nome'],
            'Escola_Alocada': escolas_df.iloc[aresta['escola']]['Nome_Escola'],
            'distancia': distancia
        })
        capacidade_restante[aresta['escola']] -= 1  # Reduz a capacidade do local
        distancia_total += distancia  # Acumula a distância total em km

# Criar o DataFrame e adicionar a linha de total usando pd.concat()
agm_df = pd.DataFrame(agm)
total_df = pd.DataFrame([{'Nome_Candidato': 'TOTAL', 'Escola_Alocada': '', 'distancia': distancia_total}])
agm_df = pd.concat([agm_df, total_df], ignore_index=True)

# Salvar o resultado em um arquivo CSV
agm_df_path = os.path.join(script_dir, 'alocacao_candidatos_escolas.csv')
agm_df.to_csv(agm_df_path, index=False)
print("Arquivo 'alocacao_candidatos_escolas.csv' gerado com sucesso.")
print(f"Distância total: {distancia_total} km")