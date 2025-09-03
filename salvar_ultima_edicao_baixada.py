import csv
import json
import logging
import os
import pymupdf
import re
import shutil
import subprocess
import unicodedata

from datetime import date, timedelta

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    force=True
)
logger = logging.getLogger(__name__)


PASTA_ARQUIVOS = "data"
PASTA_PDFS = f"{PASTA_ARQUIVOS}/pdfs"
PASTA_TXTS = f"{PASTA_ARQUIVOS}/txts"
PASTA_CONSULTAS = "consultas"
METADADOS = f"{PASTA_ARQUIVOS}/db.csv"
ARQUIVO_JSON = "ultima_edicao.json"

ontem = date.today() - timedelta(days=1)
ontem_fmt_iso8601 = ontem.strftime("%Y-%m-%d")
ontem_fmt_br = ontem.strftime("%d/%m/%Y")


def limpar_pasta_arquivos():
    if os.path.exists(PASTA_ARQUIVOS):
        shutil.rmtree(PASTA_ARQUIVOS)
    os.makedirs(PASTA_ARQUIVOS)
    os.makedirs(PASTA_TXTS)
    os.makedirs(PASTA_PDFS)


def remover_acentos(texto: str) -> str:
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )


def normalizar_texto(texto: str):
    texto = texto.lower()
    texto = re.sub(r"-\s*\n", "", texto)
    texto = re.sub(r"\s*\n\s*", " ", texto)
    texto = re.sub(r"\s+", " ", texto).strip()
    texto = remover_acentos(texto)

    return texto

def pdf_para_txt():
    for arquivo in os.listdir(PASTA_PDFS):
        if arquivo.endswith(".pdf"):
            arquivo_txt = arquivo[:-4] + ".txt"
            caminho_txt = os.path.join(PASTA_TXTS, arquivo_txt)

            caminho_pdf = os.path.join(PASTA_PDFS, arquivo)
            pdf = pymupdf.open(caminho_pdf)
    
            with open(caminho_txt, "w", encoding="utf-8") as arquivo_txt:
                for pagina in pdf:
                    texto = pagina.get_text("text")  # Extrai só texto puro
                    texto = normalizar_texto(texto)
                    arquivo_txt.write(texto + "\n")
            pdf.close()


def salvar_ultima_edicao_baixada(spiders):
    ARQUIVO_JSON = "ultima_edicao.json"
    if os.path.exists(ARQUIVO_JSON):
        with open(ARQUIVO_JSON, "r", encoding="utf-8") as f:
            ultima_edicao = json.load(f)
    else:
        ultima_edicao = {spider: '2000-01-01' for spider in spiders}

    with open(METADADOS, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            ultima_edicao[row["name"]] = row["date"]

    with open(ARQUIVO_JSON, "w", encoding="utf-8") as f:
        json.dump(ultima_edicao, f, indent=4, ensure_ascii=False)

    logger.info("artefato ultima_edicao.json gravado")


def baixar_diarios_e_converter_para_txt():
    limpar_pasta_arquivos()

    spiders = subprocess.check_output(["scrapy", "list"], text=True).splitlines()
    spiders_executados = []
    i = 0
    for spider in spiders:
        if spider.startswith("rj_"):
            spiders_executados.append(spider)
            logger.info(f"🚀 Executando {spider}")
            subprocess.run(["scrapy", "crawl", spider, "-a", f"start_date={ontem_fmt_iso8601}", "-a", f"end_date={ontem_fmt_iso8601}", "-o", METADADOS, "-s", f"LOG_FILE={PASTA_ARQUIVOS}/log.txt"])
        i += 1
        if i > 10: break

    pdf_para_txt()
    salvar_ultima_edicao_baixada(spiders_executados)        


# === Execução Principal ===
if __name__ == "__main__":
    baixar_diarios_e_converter_para_txt()
