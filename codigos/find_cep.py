import pandas as pd
import numpy as np
import requests
from datetime import datetime

# abrindo os dados dos candidatos e ceps já consolidados em csv
df_candidatos = pd.read_csv('../dados/candidatos_concurso.csv', sep=',')
df_ceps = pd.read_csv('../dados/CEP_lat_long_1000.csv', sep=',')

#_____________________________________________________
# preencher a chave API
API_KEY = ''
#_____________________________________________________

# criando as colunas de latitude e longitude para os candidatos e escolas
LIST_CEPS = df_candidatos['CEP'].unique()

# filtando os ceps restantes
LIST_CEPS = [cep for cep in LIST_CEPS if cep not in df_ceps['CEP'].unique()]

list_lat_long = []
for cep in LIST_CEPS[:1000]:

    url = f"https://www.cepaberto.com/api/v3/cep?cep={str(cep)}"
    headers = {'Authorization': f'Token token={API_KEY}'}
    try:
        response = requests.get(url, headers=headers)
        latitude = response.json()['latitude']
        longitude = response.json()['longitude']
        print(f"CEP {cep} - Latitude: {latitude} - Longitude: {longitude}")
        if latitude is None or longitude is None:
            print(f"Coordenadas vazias para o CEP {cep} - Definindo como None.")
            latitude = np.nan
            longitude = np.nan
    except Exception as e:
        print(f"Erro `{e}` no CEP {cep}!")
        latitude = np.nan
        longitude = np.nan
        
    dict_lat_long = {
        'CEP': cep,
        'latitude': latitude,
        'longitude': longitude,
    }
    list_lat_long.append(dict_lat_long)

df_lat_long = pd.DataFrame(list_lat_long)
df_lat_long.to_csv(f'../dados/CEP_lat_long_{datetime.now().strftime("%Y-%m-%d %H:%M:%S").replace("-","").replace(" ","-").replace(":","")}.csv', index=False)

print(f"Arquivo salvo em ../dados/CEP_lat_long_{datetime.now().strftime("%Y-%m-%d %H:%M:%S").replace("-","").replace(" ","-").replace(":","")}.csv")
