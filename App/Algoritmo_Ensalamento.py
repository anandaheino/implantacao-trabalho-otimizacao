
import pandas as pd
import os
from pyproj import Proj
from math import sqrt
from collections import defaultdict

# Caminho relativo ao diretório do script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Carregar os dados de escolas e candidatos
escolas_df = pd.read_csv(os.path.join(script_dir, 'escolas_gps.csv'))
candidatos_df = pd.read_csv(os.path.join(script_dir, 'candidatos_gps.csv'))

# Configuração da projeção UTM (zona 23S, exemplo para Brasil)
proj_utm = Proj(proj="utm", zone=23, ellps="WGS84", south=True)

# Função para calcular a distância euclidiana entre coordenadas convertidas para UTM
def calcular_distancia(coord1, coord2):
    x1, y1 = proj_utm(coord1[1], coord1[0])  # longitude, latitude para coord1
    x2, y2 = proj_utm(coord2[1], coord2[0])  # longitude, latitude para coord2
    return sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

# Criar um grafo com as distâncias entre cada candidato e cada escola
grafo = defaultdict(list)
for _, candidato in candidatos_df.iterrows():
    coord_candidato = (candidato["Latitude"], candidato["Longitude"])
    for _, escola in escolas_df.iterrows():
        coord_escola = (escola["Latitude"], escola["Longitude"])
        distancia = calcular_distancia(coord_candidato, coord_escola)
        grafo[candidato["Nome"]].append((distancia, escola["Nome_Escola"]))

# Exemplo de como acessar os dados no grafo
# Mostra as 5 primeiras entradas de distâncias para cada candidato
grafo_list_preview = {k: v[:5] for k, v in grafo.items()}
print(grafo_list_preview)  # Remova este print em produção, ele está aqui para demonstração.
