import re
import json
import subprocess
import requests

with open('dados.txt', 'r', encoding='utf-8') as f:
    texto = f.read()

api_url = "https://dashboard-app-tau-tan.vercel.app/api/process-rider-data"
headers = {
    "Content-Type": "application/json"
}

dados = {
    "apiKey": None, 
    "Geo": None, 
    "categoria": None,
    "valor_corrida": None,
    "nota_passageiro": None,
    "embarque": {
        "tempo_estimado": None,
        "distancia_km": None
    },
    "endereco_partida": None,
    "viagem_total": {
        "tempo_estimado": None,
        "distancia_km": None
    },
    "endereco_destino": None,
    "ganho_km": None,
    "ganho_horas": None
}

padroes = {
    "apiKey": r"^apiKey:\s*(.+)$",
    "Geo": r"^Geo:\s*(-?\d+\.\d+),(-?\d+\.\d+)$",
    "numero_radar": r"^\[index:\d+\]:\s*\d+$",
    "categoria": r"^(?:\[com\.ubercab\.driver:id/ub_badge_text_view\]|\[index:\d+\]):\s*(Uber\w+)\b",
    "valor_corrida": r"^\[index:\d+\]:\s*R\$[\s ]*([\d.,]+)",
    "nota_passageiro": r"^\[index:\d+\]:\s*(\d+[,.]\d{2})$",
    "embarque_tempo_distancia": r"(\d+)\s*minutos?\s*\(([\d.,]+)\s*km?\)",
    "endereco_partida": r"^\[index:\d+\]:\s*(.+)\s+e\s+arredores$",
    "viagem_total": r"^\[index:\d+\]:\s*Viagem de\s*(\d+)\s*minutos?\s*\(([\d.,]+)\s*km?\)",
    "destino": r"^\[index:\d+\]:\s*(.+)\s+-\s+([A-Z]{2}),?\s*(\d{5}-?\d{3})" 
}

linhas = texto.strip().split('\n')

if len(linhas) > 0:
    if match_apikey := re.match(padroes["apiKey"], linhas[0].strip()):
        dados["apiKey"] = match_apikey.group(1)

if len(linhas) > 1:
    if match_geo := re.match(padroes["Geo"], linhas[1].strip()):
        dados["Geo"] = {
            "latitude": float(match_geo.group(1)),
            "longitude": float(match_geo.group(2))
        }

for linha in linhas:
    linha = linha.strip()
    
    if any(s in linha for s in ["Selecionar", "Aceitar", "incluído"]) \
       or re.match(padroes["numero_radar"], linha) \
       or linha.startswith("apiKey:") \
       or linha.startswith("Geo:"):
        continue
        
    if match := re.match(padroes["categoria"], linha, re.IGNORECASE):
        dados["categoria"] = match.group(1)
    
    elif "R$" in linha and "+R$" not in linha:
        if match := re.search(padroes["valor_corrida"], linha):
            dados["valor_corrida"] = float(match.group(1).replace(',', '.'))
    
    elif re.match(padroes["nota_passageiro"], linha):
        dados["nota_passageiro"] = float(linha.split(': ')[1].replace(',', '.'))
    
    elif "de distância" in linha:
        if match := re.search(padroes["embarque_tempo_distancia"], linha):
            dados["embarque"]["tempo_estimado"] = int(match.group(1))
            dados["embarque"]["distancia_km"] = float(match.group(2).replace(',', '.'))
    
    elif re.match(padroes["endereco_partida"], linha):
        dados["endereco_partida"] = re.match(padroes["endereco_partida"], linha).group(1)
    
    elif "Viagem de" in linha:
        if match := re.search(padroes["viagem_total"], linha):
            dados["viagem_total"]["tempo_estimado"] = int(match.group(1))
            dados["viagem_total"]["distancia_km"] = float(match.group(2).replace(',', '.'))
    
    elif match := re.search(padroes["destino"], linha):
        dados["endereco_destino"] = {
            "endereco": match.group(1).strip(),
            "estado": match.group(2),
            "cep": match.group(3)
        }

dados_viagem = dados

valor = dados_viagem['valor_corrida']

tempo_embarque = dados_viagem['embarque']['tempo_estimado'] or 0
tempo_viagem = dados_viagem['viagem_total']['tempo_estimado'] or 0
tempo_total_horas = (tempo_embarque + tempo_viagem) / 60

distancia_embarque = dados_viagem['embarque']['distancia_km'] or 0
distancia_viagem = dados_viagem['viagem_total']['distancia_km'] or 0
distancia_total_km = distancia_embarque + distancia_viagem

ganho_hora = valor / tempo_total_horas if tempo_total_horas > 0 else 0
ganho_km = valor / distancia_total_km if distancia_total_km > 0 else 0

dados["ganho_horas"] = round(ganho_hora, 2)
dados["ganho_km"] = round(ganho_km, 2)
print(json.dumps(dados, indent=2, ensure_ascii=False))

mensagem = f"Ganho/hora: R$ {ganho_hora:.2f}\nGanho/km: R$ {ganho_km:.2f}"

subprocess.run([
    "termux-notification",
    "--title", "Relatório de Corrida",
    "--content", mensagem,
    "--priority", "high"
])

response = requests.post(api_url, json=dados, headers=headers)
response.raise_for_status()
