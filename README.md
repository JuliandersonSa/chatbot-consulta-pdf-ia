# Chatbot de Terminal com Consulta de PDFs para Sistema Armbian

Este é um chatbot de terminal desenvolvido em Python que permite consultar o conteúdo de arquivos PDF utilizando a inteligência artificial da OpenAI. Projetado para rodar em sistemas como Armbian, especificamente testado em uma Tv Box x96 mini s905w, ele oferece uma solução leve e eficiente para interagir com seus documentos diretamente do terminal.

## Funcionalidades Principais:
- Leitura e Resumo de PDFs via OpenAI.
- Gerenciamento de sessões de chat.
- Exportação de histórico de chat para PDF.
- Interface de terminal simples e eficiente.

## Tecnologias Utilizadas:
- Python
- OpenAI API
- FPDF2
- PyPDF2
- python-dotenv
- tiktoken

## Como Começar:

### Pré-requisitos:
- Python 3.8+
- Chave da API OpenAI (obtenha em platform.openai.com)

### Instalação:
1. Clone este repositório:
   `git clone https://github.com/JuliandersonSa/chatbot-consulta-pdf-ia.git`
>>>>>>> 7eb1c62 (Initial commit: Chatbot project setup, core logic, and website structure)
2. Navegue até o diretório do projeto:
   `cd nome_do_seu_repositorio`
3. Crie e ative um ambiente virtual:
   `python3 -m venv env`
   `source env/bin/activate` (Linux/macOS)
   `.\env\Scripts\activate` (Windows)
4. Instale as dependências:
   `pip install -r requirements.txt`
5. Crie um arquivo `.env` na raiz do projeto com sua chave da API:
   `cp .env.example .env`
   Abra o arquivo `.env` e substitua `sua_chave_da_api_aqui` pela sua chave real:
   `OPENAI_API_KEY=sua_chave_da_api_aqui`

### Execução:
`python3 main.py`

## Comandos do Chatbot:
- `/ajuda`: Lista todos os comandos disponíveis.
- `/lerpdf <caminho_do_pdf>`: Lê um PDF e gera um resumo.
- `/nova_sessao`: Inicia uma nova sessão de chat.
- `/sair`: Salva a sessão e encerra o chatbot (com opção de exportar o chat).

---
*Por JuliandersoSa *
