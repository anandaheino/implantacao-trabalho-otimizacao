import os
import pandas as pd
import folium
import numpy as np

# Obter o diretório do script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Carregar os dados de escolas, candidatos e alocações
escolas_df = pd.read_csv(os.path.join(script_dir, 'escolas_gps.csv'))
candidatos_df = pd.read_csv(os.path.join(script_dir, 'candidatos_gps.csv'))
alocacoes_df = pd.read_csv(os.path.join(script_dir, 'alocacao_candidatos_escolas.csv'))

# Inicializar o mapa centrado em uma posição média
media_latitude = (escolas_df['Latitude'].mean() + candidatos_df['Latitude'].mean()) / 2
media_longitude = (escolas_df['Longitude'].mean() + candidatos_df['Longitude'].mean()) / 2
mapa = folium.Map(location=[media_latitude, media_longitude], zoom_start=10)

# Dicionários para armazenar as coordenadas marcadas
marcadores_escolas = {}
marcadores_candidatos = {}

# Função para aplicar jitter condicional com base na densidade
def apply_jitter_conditional(lat, lon, candidates_df, jitter_base=0.0100):
    # Contar candidatos com a mesma localização para calcular densidade
    same_location_count = candidates_df[(candidates_df['Latitude'] == lat) & (candidates_df['Longitude'] == lon)].shape[0]
    jitter_amount = jitter_base / max(same_location_count, 1)  # Reduz o jitter para maior densidade
    return lat + np.random.uniform(-jitter_amount, jitter_amount), lon + np.random.uniform(-jitter_amount, jitter_amount)

# Iterar pelas entradas do arquivo de alocação
for _, row in alocacoes_df.iterrows():
    nome_escola = row['Escola_Alocada']
    nome_candidato = row['Nome_Candidato']

    # Obter informações de localização da escola e do candidato
    escola_info = escolas_df[escolas_df['Nome_Escola'] == nome_escola].iloc[0]
    candidato_info = candidatos_df[candidatos_df['Nome'] == nome_candidato].iloc[0]

    # Marcar a escola se ainda não foi marcada
    if nome_escola not in marcadores_escolas:
        folium.Marker(
            location=[escola_info['Latitude'], escola_info['Longitude']],
            popup=nome_escola,
            icon=folium.Icon(color='red', icon='school', prefix='fa')
        ).add_to(mapa)
        marcadores_escolas[nome_escola] = (escola_info['Latitude'], escola_info['Longitude'])

    # Marcar o candidato com jitter condicional se ainda não foi marcado
    if nome_candidato not in marcadores_candidatos:
        lat_jitter, lon_jitter = apply_jitter_conditional(
            candidato_info['Latitude'], 
            candidato_info['Longitude'], 
            candidatos_df
        )
        folium.Marker(
            location=[lat_jitter, lon_jitter],
            popup=nome_candidato,
            icon=folium.Icon(color='blue', icon='user', prefix='fa')
        ).add_to(mapa)
        marcadores_candidatos[nome_candidato] = (lat_jitter, lon_jitter)

    # Conectar o candidato à escola especificada
    folium.PolyLine(
        locations=[marcadores_candidatos[nome_candidato], marcadores_escolas[nome_escola]],
        color='gray',
        weight=2.5,
        opacity=0.6
    ).add_to(mapa)

# Caminho de salvamento para o arquivo HTML na mesma pasta do script
mapa_output_path = os.path.join(script_dir, 'alocacao_candidatos_escolas_mapa.html')
mapa.save(mapa_output_path)
print(f"Mapa de alocações salvo em '{mapa_output_path}'")
