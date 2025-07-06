#pdf_processor.py

import sys
import os
import PyPDF2

# Adiciona o diretório raiz do projeto ao sys.path para permitir importações absolutas
# quando o módulo é executado diretamente.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.insert(0, project_root)

# Importa as configurações do config.py (apenas para exemplo de uso de caminhos, não diretamente necessário para extração)
from config.config import PDFS_DIR

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extrai todo o texto de um arquivo PDF.

    Args:
        pdf_path (str): O caminho completo para o arquivo PDF.

    Returns:
        str: O conteúdo de texto extraído do PDF, ou uma string vazia se houver um erro.
    """
    if not os.path.exists(pdf_path):
        print(f"Erro: O arquivo PDF não foi encontrado em '{pdf_path}'")
        return ""

    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                text += page.extract_text() or "" # Adiciona o texto da página, garantindo que não seja None
        return text
    except Exception as e:
        print(f"Erro ao extrair texto do PDF '{pdf_path}': {e}")
        return ""

if __name__ == "__main__":
    print("Testando pdf_processor.py...")

    # Para testar, você precisará ter um arquivo PDF na pasta 'pdfs' do seu projeto.
    # Por exemplo, crie um arquivo chamado 'exemplo.pdf' ou use um dos PDFs do tutorial.
    test_pdf_name = "exemplo.pdf" # Altere para o nome de um PDF existente na sua pasta 'pdfs'
    full_pdf_path = os.path.join(PDFS_DIR, test_pdf_name)

    # Crie um arquivo PDF de exemplo se não existir para facilitar o teste
    # (Este é um snippet mínimo para criar um PDF vazio, PyPDF2 não cria conteúdo facilmente)
    # Se você não tem PDFs, pode pular esta parte e apenas observar o erro de arquivo não encontrado.
    if not os.path.exists(full_pdf_path):
        print(f"\nAVISO: O arquivo de teste '{test_pdf_name}' não foi encontrado em '{PDFS_DIR}'.")
        print("Por favor, coloque um PDF de teste na pasta 'pdfs/' ou crie um.")
        print("Você pode criar um PDF simples com texto usando um editor de texto e 'Salvar como PDF'.")
        # Exemplo de criação de um PDF muito simples via pypdf (requer pypdf instalado)
        # from pypdf import PdfWriter
        # writer = PdfWriter()
        # writer.add_blank_page(width=72, height=72)
        # with open(full_pdf_path, "wb") as fp:
        #     writer.write(fp)
        # print(f"Um PDF vazio '{test_pdf_name}' foi criado para teste.")

    extracted_content = extract_text_from_pdf(full_pdf_path)

    if extracted_content:
        print(f"\nConteúdo extraído de '{test_pdf_name}' (primeiros 500 caracteres):\n")
        print(extracted_content[:500])
        if len(extracted_content) > 500:
            print("\n...")
        print(f"\nTotal de caracteres extraídos: {len(extracted_content)}")
    else:
        print(f"\nNão foi possível extrair conteúdo de '{test_pdf_name}'.")
