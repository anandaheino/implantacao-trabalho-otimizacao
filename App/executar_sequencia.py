import subprocess
import os
import sys
import time

# Obter o diretório do script atual
script_dir = os.path.dirname(os.path.abspath(__file__))

# Lista dos scripts a serem executados na ordem desejada
scripts = [
    #os.path.join(script_dir, 'gerar posição gps.py'),
    #os.path.join(script_dir, 'Algoritmo_Ensalamento.py'),
    #os.path.join(script_dir, 'Algoritmo Dijkstra.py'),
    os.path.join(script_dir, 'Algoritmo AGM.py'),
    os.path.join(script_dir, 'grafico com os nos.py')
]

# Executar cada script em ordem com um intervalo de 5 segundos entre eles
for script in scripts:
    try:
        print(f"\nExecutando o script: {script}")
        result = subprocess.run([sys.executable, script], check=True, capture_output=True, text=True)
        print("Saída do script:")
        print(result.stdout)  # Exibir a saída padrão do script
    except subprocess.CalledProcessError as e:
        print(f"Erro ao executar o script {script}: {e}")
        print("Detalhes do erro:", e.stderr)  # Exibir a saída de erro para depuração
    
    # Espera de 5 segundos antes de executar o próximo script
    time.sleep(5)

print("\nExecução dos scripts concluída.")
