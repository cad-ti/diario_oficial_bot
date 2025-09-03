import json
import logging
import os
import smtplib
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# === Configurações de Log ===
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    force=True
)
logger = logging.getLogger(__name__)

# === Constantes e Variáveis de Ambiente ===
ULTIMA_EDICAO = "ultima_edicao.json"
DIAS_LIMITE = 7
EMAIL_REMETENTE = os.getenv("EMAIL_REMETENTE")
EMAIL_SENHA = os.getenv("EMAIL_SENHA")
DESTINATARIOS_ALERTA = os.getenv("DESTINATARIOS_ALERTA", "").split(",")


# --- 1) Carrega JSON ---
def carregar_ultima_edicao(caminho: str) -> dict:
    if not os.path.exists(caminho):
        raise FileNotFoundError(f"Arquivo {caminho} não encontrado!")

    with open(caminho, "r", encoding="utf-8") as f:
        return json.load(f)


# --- 2) Verifica atrasos ---
def verificar_atrasos(dados: dict, dias_limite: int) -> list:
    hoje = datetime.today().date()
    limite = hoje - timedelta(days=dias_limite)
    atrasados = []

    for municipio, data_str in dados.items():
        try:
            data_edicao = datetime.strptime(data_str, "%Y-%m-%d").date()
            if data_edicao < limite:
                atrasados.append((municipio, data_str))
        except ValueError:
            atrasados.append((municipio, "Data inválida"))

    return atrasados


# --- 3) Monta corpo HTML ---
def montar_html(spiders_sem_downloads: list, dias_limite: int) -> str:
    hoje = datetime.today().date()
    titulo = f"🚨 Spiders que não baixaram PDFs nos últimos {dias_limite} dias"
    linhas = "".join(f"<li><b>{spider}</b>: {ultima_edicao_baixada}</li>" for spider, ultima_edicao_baixada in spiders_sem_downloads)
    conteudo = "<ul><li><b>SPIDER</b>: Data da última edição baixada</li></ul>"
    conteudo += f"<ul>{linhas}</ul>"

    return f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #333;">
        <h2>{titulo}</h2>
        {conteudo}
        <hr>
        <p style="font-size: 12px; color: #888;">Verificação executada em {hoje.strftime('%d/%m/%Y')}.</p>
      </body>
    </html>
    """


# --- 4) Envia e-mail ---
def enviar_email(html: str, remetente: str, senha: str, destinatarios: list):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Verificação de Atualizações - Diários Oficiais"
    msg["From"] = remetente
    msg["To"] = ", ".join(destinatarios)
    msg.attach(MIMEText(html, "html", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(remetente, senha)
            server.sendmail(remetente, destinatarios, msg.as_string())
        logger.info("📧 E-mail de verificação enviado com sucesso!")
    except Exception as e:
        logger.error(f"⚠️ Erro ao enviar e-mail: {e}")
        exit(1)


# --- 5) Função principal ---
def main():
    ultima_edicao = carregar_ultima_edicao(ULTIMA_EDICAO)
    spiders_sem_downloads = verificar_atrasos(ultima_edicao, DIAS_LIMITE)
    if spiders_sem_downloads:
        html = montar_html(spiders_sem_downloads, DIAS_LIMITE)
        enviar_email(html, EMAIL_REMETENTE, EMAIL_SENHA, DESTINATARIOS_ALERTA)
    else:
        logger.info(f"✅ Todos os spiders baixaram ao menos 1 edição nos últimos {DIAS_LIMITE} dias")


if __name__ == "__main__":
    main()
