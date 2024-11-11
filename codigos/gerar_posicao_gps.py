import pandas as pd
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from geopy.exc import GeocoderTimedOut
import os
from pathlib import Path


project_root = Path(__file__).resolve().parent.parent

# Configuração do geocodificador
geolocator = Nominatim(user_agent="cep_to_latlon_converter")
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=2)

# Função para converter CEP para latitude e longitude
def get_lat_lon(cep):
    try:
        location = geocode(f"{cep}, Brazil", timeout=10)
        if location:
            return location.latitude, location.longitude
        else:
            print(f"Nenhum resultado encontrado para o CEP: {cep}")
            return None, None
    except GeocoderTimedOut:
        print(f"Timeout para o CEP: {cep}. Tentando novamente...")
        return get_lat_lon(cep)
    except Exception as e:
        print(f"Erro ao obter localização para o CEP {cep}: {e}")
        return None, None

# Caminho dos arquivos
file_path = rf'{project_root}\dados\candidatos_concurso.csv'
output_file_path = rf'{project_root}\dados\candidatos_concurso_gps.csv'

# Carregar o arquivo original ou o de progresso, se já existir
if os.path.exists(output_file_path):
    df = pd.read_csv(output_file_path)
else:
    df = pd.read_csv(file_path)
    if 'Latitude' not in df.columns or 'Longitude' not in df.columns:
        df['Latitude'] = None
        df['Longitude'] = None

# Iterar sobre as linhas que ainda não foram processadas
for index, row in df.iterrows():
    if pd.notna(row['Latitude']) and pd.notna(row['Longitude']):
        continue  # Ignorar linhas que já possuem latitude e longitude
    
    print(f"Processando linha {index + 1} / {len(df)} - CEP: {row['CEP']}")
    
    lat, lon = get_lat_lon(row['CEP'])
    if lat is None or lon is None:
        print(f"Erro ao obter coordenadas para a linha {index + 1} (CEP: {row['CEP']}) - Definindo como None permanente.")
        df.at[index, 'Latitude'] = 'None'
        df.at[index, 'Longitude'] = 'None'
    else:
        # Atualizar as colunas Latitude e Longitude com valores válidos
        df.at[index, 'Latitude'] = lat
        df.at[index, 'Longitude'] = lon
    
    # Salvar o progresso após cada atualização
    df.to_csv(output_file_path, index=False)

print("Processo completo ou interrompido. Progresso salvo.")
