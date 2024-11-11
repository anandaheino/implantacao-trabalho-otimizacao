import pandas as pd
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent

escolas = pd.read_csv(rf'{project_root}\dados\micro_Escolas_com_vagas_gps.csv')
print("Total de escolas:" , escolas)

alocacoes = pd.read_csv(rf'{project_root}\dados\alocacao_candidatos_escolas.csv')
print("Alocacoes:" ,alocacoes)

