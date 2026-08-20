from datetime import datetime
import json
import os
import re
import io
import requests
from pypdf import PdfReader

# Palavras-chave ou lista de nomes específicos a monitorar
TERMOS_BUSCA = [
    "NOMEAR",
    "NOMEACAO",
    "ANALISTA JUDICIARIO",
    "TECNICO JUDICIARIO",
    "OFICIAL DE JUSTICA",
    # Adicione nomes específicos aqui se quiser: "FULANO DE TAL",
]

DATA_HOJE = datetime.now()
DATA_STR = DATA_HOJE.strftime("%Y-%m-%d")
DATA_FORMATADA = DATA_HOJE.strftime("%d/%m/%Y")

# URL base do DJe TJPE para o Caderno Administrativo
# O TJPE organiza os arquivos por data: ANO_MES_DIA/Edicao_XX_Administrativo.pdf
# O script faz o download do caderno administrativo da data atual
URL_DJE_ADM = f"https://www.tjpe.jus.br/dje/download?data={DATA_FORMATADA}&caderno=A"


def buscar_nomeacoes():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    resultado = {
        "ultima_verificacao": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "data_diario": DATA_FORMATADA,
        "encontrou_mencoes": False,
        "total_ocorrencias": 0,
        "ocorrencias": [],
        "mensagem": "",
    }

    try:
        response = requests.get(URL_DJE_ADM, headers=headers, timeout=60)
        
        # Se o diário do dia ainda não saiu ou for fim de semana/feriado
        if response.status_code != 200 or len(response.content) < 1000:
            resultado["mensagem"] = f"Edição Administrativa de {DATA_FORMATADA} ainda não disponível ou sem publicação."
            salvar_json(resultado)
            return

        # Leitura do PDF em memória (sem precisar gravar em disco)
        pdf_file = io.BytesIO(response.content)
        reader = PdfReader(pdf_file)
        
        matches = []

        for num_pagina, pagina in enumerate(reader.pages, start=1):
            texto = pagina.extract_text()
            if not texto:
                continue

            # Busca insensível a maiúsculas/minúsculas e acentos
            texto_upper = texto.upper()
            
            for termo in TERMOS_BUSCA:
                termo_upper = termo.upper()
                if termo_upper in texto_upper:
                    # Extrai um trecho do parágrafo ao redor da palavra
                    pos = texto_upper.find(termo_upper)
                    inicio = max(0, pos - 150)
                    fim = min(len(texto), pos + 350)
                    trecho = texto[inicio:fim].replace("\n", " ").strip()
                    
                    matches.append({
                        "termo": termo,
                        "pagina": num_pagina,
                        "trecho": f"...{trecho}..."
                    })

        if matches:
            resultado["encontrou_mencoes"] = True
            resultado["total_ocorrencias"] = len(matches)
            resultado["ocorrencias"] = matches
            resultado["mensagem"] = f"Foram encontradas {len(matches)} menções a nomeações/termos no Caderno Administrativo de hoje!"
        else:
            resultado["mensagem"] = f"Caderno Administrativo de {DATA_FORMATADA} verificado. Nenhuma menção a nomeação encontrada."

    except Exception as e:
        resultado["mensagem"] = f"Erro durante a verificação: {str(e)}"

    salvar_json(resultado)


def salvar_json(dados):
    with open("status.json", "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
    print("Arquivo status.json atualizado com sucesso.")


if __name__ == "__main__":
    buscar_nomeacoes()
