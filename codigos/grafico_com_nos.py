import pandas as pd
import folium

relative_path = '../dados/'
# Carregar os dados de escolas e candidatos
escolas_df = pd.read_csv(relative_path+'micro_Escolas_com_vagas_gps.csv')
candidatos_df = pd.read_csv(relative_path+'micro_candidatos_concurso_lat_long.csv')
alocacoes_df = pd.read_csv(relative_path+'alocacao_candidatos_escolas.csv')

# Inicializar o mapa centrado em uma posição média
media_latitude = (escolas_df['Latitude'].mean() + candidatos_df['Latitude'].mean()) / 2
media_longitude = (escolas_df['Longitude'].mean() + candidatos_df['Longitude'].mean()) / 2
mapa = folium.Map(location=[media_latitude, media_longitude], zoom_start=10)

# Adicionar todas as escolas ao mapa
for _, row in escolas_df.iterrows():
    folium.Marker(
        location=[row['Latitude'], row['Longitude']],
        popup=row['Nome_Escola'],
        icon=folium.Icon(color='red', icon='school', prefix='fa')
    ).add_to(mapa)

# Adicionar todos os candidatos e suas alocações ao mapa
for _, row in alocacoes_df.iterrows():
    candidato_info = candidatos_df[candidatos_df['Nome'] == row['Nome_Candidato']].iloc[0]
    escola_info = escolas_df[escolas_df['Nome_Escola'] == row['Escola_Alocada']].iloc[0]

    # Adicionar o candidato como um marcador azul
    folium.Marker(
        location=[candidato_info['Latitude'], candidato_info['Longitude']],
        popup=row['Nome_Candidato'],
        icon=folium.Icon(color='blue', icon='user', prefix='fa')
    ).add_to(mapa)

    # Adicionar uma linha de conexão entre o candidato e a escola
    folium.PolyLine(
        locations=[(candidato_info['Latitude'], candidato_info['Longitude']),
                   (escola_info['Latitude'], escola_info['Longitude'])],
        color='gray',
        weight=2.5,
        opacity=0.6
    ).add_to(mapa)

# Salvar o mapa em um arquivo HTML
mapa.save(relative_path+'alocacao_candidatos_escolas_mapa.html')
print(f"Mapa de alocações salvo em '{relative_path}alocacao_candidatos_escolas_mapa.html'")
