# Diário Oficial Bot - TCE-RJ

Este projeto automatiza a geração e envio de um clipping de publicações extraídas de diários oficiais do Estado do Rio de Janeiro.
A parte de raspagem de dados é um fork do projeto [Querido Diário](https://queridodiario.ok.org.br/).

## 📚 Sumário

- [Objetivo](#objetivo)
- [Funcionalidades](#funcionalidades)
- [Requisitos](#requisitos)
- [Como executar](#como-executar)
- [Testes](#testes)
- [Automação com GitHub Actions](#automação-com-github-actions)
- [Licença](#licença)

## 📌 Objetivo

Extrair informações dos diários oficiais de municípios e do governo do Estado Rio de Janeiro com base em termos de pesquisa definidos, organizá-las em um relatório e enviar os resultados por e-mail.

## 🧰 Funcionalidades

- Raspagem dos diários oficiais
- Conversão de PDF para TXT
- Leitura de arquivos de configuração com termos de pesquisa e destinatários.
- Geração de e-mail com os resultados encontrados.
- Envio automático de e-mails usando SMTP.
- Execução automatizada via GitHub Actions.
- Testes automatizados com `unittest`.

## ⚙️ Requisitos

- Python 3.13+
- Conta de e-mail com senha de app (para envio via SMTP)

### Criação do ambiente virtual

```bash
python -m venv .venv
```

### Ativação do ambiente virtual

```bash
.\.venv\Scripts\Activate.ps1
```

### Instalação das dependências

```bash
pip install scrapy python-dateutil dateparser text-unidecode thefuzz filetype PyMuPDF PyYAML
```

## 🚀 Como executar

1. Crie um arquivo YAML dentro da pasta `consultas/` com a seguinte estrutura:

```yaml
titulo: Nome da Consulta
destinatarios:
  - exemplo1@email.com
  - exemplo2@email.com
termos_pesquisa:
  - educação
  - "merenda escolar"
```

2. Execute o script principal:

```bash
python gerar_enviar_clipping.py
```

3. O script irá:
   - Baixar diários oficiais e converter em TXT para realizar as consultas
   - Carregar os arquivos da pasta `consultas/`.
   - Gerar o clipping de publicações com os termos de interesse.
   - Enviar um e-mail com os resultados.

## 🧪 Testes

Para rodar os testes unitários:

```bash
python -m unittest discover -s testes -p "test_*.py"
```

## ⏰ Automação com GitHub Actions

O projeto possui dois workflows no GitHub:

- `agendamento.yml`: executa diariamente o script `gerar_enviar_clipping.py`.
- `python-tests.yml`: executa os testes unitários automaticamente a cada push.

## 📄 Licença

Este projeto está licenciado sob os termos da [Creative Commons Legal Code](LICENSE).

## 📧 Contato

CAD-TI: [cad_ti@tcerj.tc.br](mailto:cad_ti@tcerj.tc.br)
