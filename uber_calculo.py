import re
import json
import subprocess

with open('texto.txt', 'r', encoding='utf-8') as f:
    texto = f.read()

dados = {
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
    "endereco_destino": None
}

padroes = {
    "categoria": r"^\[index:\d+\]:\s*(Uber\w+)$",
    "valor_corrida": r"R\$\s*([\d,]+)",
    "nota_passageiro": r"^\[index:\d+\]:\s*(\d+,\d+)$",
    "embarque_tempo_distancia": r"(\d+)\s*minutos\s*\(([\d.]+)\s*km\)\s*de distância",
    "endereco_partida": r"^\[index:\d+\]:\s*([A-Za-záàâãéèêíïóôõöúçñ\s]+)$",
    "viagem_total": r"Viagem de (\d+)\s*minutos\s*\(([\d.]+)\s*km\)",
    "destino": r"(.*)\b([A-Z]{2})\b,?\s*(\d{5}-?\d{3})\b(.*)"
}

padrao_endereco = re.compile(
    r'(.*)\b([A-Z]{2})\b,?\s*(\d{5}-?\d{3})\b(.*)',
    re.IGNORECASE | re.VERBOSE
)

for linha in texto.strip().split('\n'):
    linha = linha.strip()
    
    if match := re.match(padroes["categoria"], linha, re.IGNORECASE):
        dados["categoria"] = match.group(1)
    
    elif "R$" in linha:
        if match := re.search(padroes["valor_corrida"], linha):
            dados["valor_corrida"] = float(match.group(1).replace(',', '.'))
    
    elif re.match(padroes["nota_passageiro"], linha):
        dados["nota_passageiro"] = float(linha.split(': ')[1].replace(',', '.'))
    
    elif "de distância" in linha:
        if match := re.search(padroes["embarque_tempo_distancia"], linha):
            dados["embarque"]["tempo_estimado"] = int(match.group(1))
            dados["embarque"]["distancia_km"] = float(match.group(2))
    
    elif re.match(padroes["endereco_partida"], linha):
        dados["endereco_partida"] = linha.split(': ')[1]
    
    elif "Viagem de" in linha:
        if match := re.search(padroes["viagem_total"], linha):
            dados["viagem_total"]["tempo_estimado"] = int(match.group(1))
            dados["viagem_total"]["distancia_km"] = float(match.group(2))
    
    elif re.match(padroes["destino"], linha):
        match = padrao_endereco.search(linha.split(': ')[1])
        if match:
            endereco = {
                "rua": match.group(1).strip(' -,'),
                "estado": match.group(2),
                "cep": match.group(3),
                "complemento": match.group(4).strip(' ,')
            }
            dados["endereco_destino"] = endereco

dados_viagem = dados
##print(json.dumps(dados, indent=2, ensure_ascii=False))

valor = dados_viagem['valor_corrida']

tempo_embarque = dados_viagem['embarque']['tempo_estimado'] or 0
tempo_viagem = dados_viagem['viagem_total']['tempo_estimado'] or 0
tempo_total_horas = (tempo_embarque + tempo_viagem) / 60

distancia_embarque = dados_viagem['embarque']['distancia_km'] or 0
distancia_viagem = dados_viagem['viagem_total']['distancia_km'] or 0
distancia_total_km = distancia_embarque + distancia_viagem

ganho_hora = valor / tempo_total_horas if tempo_total_horas > 0 else 0
ganho_km = valor / distancia_total_km if distancia_total_km > 0 else 0

mensagem = f"Ganho/hora: R$ {ganho_hora:.2f}\nGanho/km: R$ {ganho_km:.2f}"

subprocess.run([
    "termux-notification",
    "--title", "Relatório de Corrida",
    "--content", mensagem,
    "--priority", "high"
])
