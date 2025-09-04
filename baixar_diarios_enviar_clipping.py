import ast
import csv
import glob
import json
import logging
import os
import pymupdf
import re
import smtplib
import shutil
import subprocess
import yaml

from datetime import date, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pesquisa_textual import localizar_termo

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    force=True
)
logger = logging.getLogger(__name__)

EMAIL_REMETENTE = os.environ.get("EMAIL_REMETENTE") 
EMAIL_SENHA = os.environ.get("EMAIL_SENHA")

PASTA_ARQUIVOS = "data"
PASTA_PDFS = f"{PASTA_ARQUIVOS}/pdfs"
PASTA_TXTS = f"{PASTA_ARQUIVOS}/txts"
PASTA_CONSULTAS = "consultas"
METADADOS = f"{PASTA_ARQUIVOS}/db.csv"
ULTIMA_EDICAO = "ultima_edicao.json"

ontem = date.today() - timedelta(days=1)
ontem_fmt_iso8601 = ontem.strftime("%Y-%m-%d")
ontem_fmt_br = ontem.strftime("%d/%m/%Y")


def limpar_pasta_arquivos():
    if os.path.exists(PASTA_ARQUIVOS):
        shutil.rmtree(PASTA_ARQUIVOS)
    os.makedirs(PASTA_ARQUIVOS)
    os.makedirs(PASTA_TXTS)
    os.makedirs(PASTA_PDFS)


def normalizar_texto(texto: str):
    texto = re.sub(r"-\s*\n", "", texto)
    texto = re.sub(r"\s*\n\s*", " ", texto)
    texto = re.sub(r"\s+", " ", texto).strip()

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
    if os.path.exists(ULTIMA_EDICAO):
        with open(ULTIMA_EDICAO, "r", encoding="utf-8") as f:
            ultima_edicao = json.load(f)
    else:
        ultima_edicao = {spider: '2000-01-01' for spider in spiders}

    with open(METADADOS, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            ultima_edicao[row["name"]] = row["date"]

    with open(ULTIMA_EDICAO, "w", encoding="utf-8") as f:
        json.dump(ultima_edicao, f, indent=4, ensure_ascii=False)

    logger.info("✅ Artefato ultima_edicao.json gravado")


def baixar_diarios_e_converter_para_txt():
    limpar_pasta_arquivos()

    spiders = subprocess.check_output(["scrapy", "list"], text=True).splitlines()
    spiders_executados = []
    for spider in spiders:
        if spider.startswith("rj_"):
            spiders_executados.append(spider)
            logger.info(f"🚀 Executando {spider}")
            subprocess.run(["scrapy", "crawl", spider, "-a", f"start_date={ontem_fmt_iso8601}", "-a", f"end_date={ontem_fmt_iso8601}", "-o", METADADOS, "-s", f"LOG_FILE={PASTA_ARQUIVOS}/log.txt"])

    pdf_para_txt()
    salvar_ultima_edicao_baixada(spiders_executados)


def gerar_html_resultado(termo, resultados):
    html = ""
    total_trechos = 0
    for resultado in resultados:
        total_trechos += len(resultado["trechos"])
        trechos = "<br><br>".join(resultado["trechos"])
        html += f'''
        <p><strong>📍 Jurisdicionado:</strong> {resultado["spider"]}<br>
        <strong>📄 Edição:</strong> <a href="{resultado['url']}">{resultado['url']}</a><br>
        <strong>📝 Trechos:</strong><br>{trechos}</p><hr>
        '''
    titulo = f"<h2>🔍 Termo: <em>{termo}</em> (total: {total_trechos})</h2>"
    return titulo + html if html else ""


def listar_metadados():
    with open(METADADOS, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        metadados = []
        for row in reader:
            if row["files"]:
                files = ast.literal_eval(row["files"])[0]
                txt = files['path'][5:-4]
                txt = f"{PASTA_TXTS}/{txt}.txt"
                meta = {
                    "spider": row["name"],
                    "url": files['url'], 
                    "txt": txt
                } 
                metadados.append(meta)
        return metadados
        

def gerar_corpo_email(titulo, termos):
    link_git = "<a href=\"https://github.com/cad-ti/diario_oficial_bot/tree/main/diario_oficial_bot/spiders/rj\">Diário Oficial Bot - TCE-RJ</a>"
    html = f"<html><body><h1>📬 {titulo}</h1><p>Consulta realizada nos jurisdicionados disponíveis no {link_git} </p><hr>"
    possui_resultado = False
    for termo in termos:
        resultados = []
        metadados = listar_metadados()
        for meta in metadados:
            with open(meta["txt"], "r", encoding="utf-8") as f:
                texto = f.read()
            trechos = localizar_termo(texto, termo)
            if trechos:
                result = meta.copy()
                result["trechos"] = trechos
                resultados.append(result)

        if resultados:
            html_termo = gerar_html_resultado(termo, resultados)
            html += html_termo
            possui_resultado = True
    html += "</body></html>"
    
    return html if possui_resultado else ""


def enviar_email(destinatarios, assunto, corpo_html):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = assunto
    msg["From"] = EMAIL_REMETENTE
    msg["To"] = ", ".join(destinatarios)
    msg.attach(MIMEText(corpo_html, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_REMETENTE, EMAIL_SENHA)
            server.sendmail(EMAIL_REMETENTE, destinatarios, msg.as_string())
            logger.info(f"✅ E-mail enviado com sucesso para os destinatarios cadastrados")
    except Exception as e:
        logger.error(f"❌ Erro ao enviar e-mail: {e}")


def carregar_destinatarios(yaml_config):
    destinatarios = yaml_config.get("destinatarios", [])
    if isinstance(destinatarios, list):
        return destinatarios
    else:
        destinatarios_env = os.environ.get(destinatarios, "")
        return [email.strip() for email in destinatarios_env.splitlines() if email.strip()]


def buscar_termos_enviar_email():
    for consulta in glob.glob("consultas/*.yaml"):
        logger.info(f"📁 Processando arquivo: {consulta}")
        with open(consulta, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        titulo = config.get("titulo", "") 
        termos = config.get("termos_pesquisa", [])
        destinatarios = carregar_destinatarios(config)

        if not titulo or not termos or not destinatarios:
            logger.warning(f"⚠️ Ignorado: arquivo {consulta} sem campos obrigatórios (titulo, destinatarios ou termos_pesquisa).")
            continue

        titulo += f" - DOs de {ontem_fmt_br}"
        corpo_html = gerar_corpo_email(titulo, termos)
        if not corpo_html:
            logger.warning(f"⚠️ Nenhum resultado encontrado para a consulta {consulta}.")
            continue

        enviar_email(
            destinatarios=destinatarios,
            assunto=titulo,
            corpo_html=corpo_html,
        )
        


# === Execução Principal ===
if __name__ == "__main__":
    baixar_diarios_e_converter_para_txt()
    buscar_termos_enviar_email()
