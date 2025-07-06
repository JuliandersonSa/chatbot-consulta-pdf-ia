#pdf_exporter.py

import os
import sys
import json
import datetime
from fpdf import FPDF # Importa a classe FPDF
from typing import Union # Adicionado para 'Union' na delete_exported_pdf
# Adiciona o diretório raiz do projeto ao sys.path para permitir importações absolutas
# quando o módulo é executado diretamente ou como parte do projeto maior.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.insert(0, project_root)

# Importa as configurações de caminhos do config.py
from config.config import EXPORTS_DIR, DEFAULT_SESSION_NAME # Importamos EXPORTS_DIR e DEFAULT_SESSION_NAME

# --- Funções Auxiliares ---
def _ensure_dir_exists(directory_path: str):
    """Garante que um diretório exista. Se não existir, ele é criado."""
    os.makedirs(directory_path, exist_ok=True)

def _get_export_path(session_name: str, export_name: str) -> str:
    """
    Retorna o caminho completo para o arquivo PDF exportado dentro da sessão.
    Os exports são organizados em subdiretórios por nome de sessão.
    """
    session_export_dir = os.path.join(EXPORTS_DIR, session_name)
    _ensure_dir_exists(session_export_dir)
    return os.path.join(session_export_dir, export_name) # Removido o ".pdf" extra aqui

# --- Funções de Gerenciamento de Exportação de Chat ---
def export_chat_to_pdf(chat_history: list, session_name: str, export_name: str) -> str:
    """
    Exporta o histórico completo de um chat para um arquivo PDF.
    """
    #print(f"DEBUG: export_chat_to_pdf iniciado. session_name: {session_name}, export_name: {export_name}") # Print de depuração

    if not chat_history:
        #print("DEBUG: Histórico do chat vazio.") # Print de depuração
        return "O histórico do chat está vazio. Nada para exportar."

    # ESTA É A LINHA CRUCIAL QUE PRECISA SER ADICIONADA OU VERIFICADA!
    # Ela limpa o nome do export e atribui à variável base_name_cleaned.
    base_name_cleaned = "".join(c for c in export_name if c.isalnum() or c in (' ', '_', '-')).strip()
    #print(f"DEBUG: base_name_cleaned após limpeza inicial: '{base_name_cleaned}'") # Print de depuração

    # 1. Garante que o nome base não tenha .pdf extra
    # Agora, base_name_cleaned EXISTE ANTES DE SER USADA aqui.
    if base_name_cleaned.lower().endswith(".pdf"):
        #print(f"DEBUG: '{base_name_cleaned}' termina com .pdf, removendo a extensão.") # Print de depuração
        base_name_cleaned = base_name_cleaned[:-4] # Remove a última ".pdf"
        #print(f"DEBUG: base_name_cleaned após remover .pdf extra: '{base_name_cleaned}'") # Print de depuração

    # Adicione uma verificação para nome vazio após a limpeza
    if not base_name_cleaned:
        #print("DEBUG: base_name_cleaned está vazia após a limpeza. Retornando erro.") # Print de depuração
        return "Erro: O nome do arquivo exportado não pode ser vazio ou conter apenas caracteres inválidos após a limpeza."

    # 2. Adiciona o timestamp para garantir um nome de arquivo único
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    #print(f"DEBUG: Timestamp gerado: {timestamp}") # Print de depuração

    # 3. Constrói o nome de arquivo final, com o nome limpo, timestamp e UMA extensão .pdf
    final_export_filename = f"{base_name_cleaned}_{timestamp}.pdf"
    #print(f"DEBUG: Nome final do arquivo exportado: '{final_export_filename}'") # Print de depuração

    # 4. Chama _get_export_path com o nome de arquivo FINAL e COMPLETO
    pdf_path = _get_export_path(session_name, final_export_filename)
    #print(f"DEBUG: Caminho completo para o PDF: '{pdf_path}'") # Print de depuração

    try:
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15) # Adicionado para melhor quebra de página
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        pdf.multi_cell(0, 10, f"Documentação da Interação - Sessão: {session_name}\n")
        pdf.multi_cell(0, 10, f"Nome do Export: {final_export_filename}\n\n")

        # Itera sobre o histórico do chat
        for message in chat_history:
            role = message.get("role", "unknown").capitalize()
            content = message.get("content", "")

            # Ignora a mensagem do sistema para a exportação, pois ela é fixa e não parte da interação dinâmica
            if role.lower() == "system":
                continue

            # Formatação melhorada para usuário e assistente
            if role == "User":
                pdf.set_font("Arial", "B", 12) # Negrito para usuário
                pdf.write(5, f"Você: ")
                pdf.set_font("Arial", size=12) # Volta à fonte normal
                pdf.multi_cell(0, 5, content)
            elif role == "Assistant":
                pdf.set_font("Arial", "B", 12) # Negrito para bot
                pdf.write(5, f"Bot: ")
                pdf.set_font("Arial", size=12) # Volta à fonte normal
                pdf.multi_cell(0, 5, content)
            else: # Para outros papéis desconhecidos
                pdf.multi_cell(0, 5, f"{role}: {content}")
            
            pdf.ln(2) # Pequena quebra de linha entre mensagens para melhor leitura

        pdf.output(pdf_path)
        #print(f"DEBUG: PDF gerado com sucesso em '{pdf_path}'") # Print de depuração
        return f"Histórico do chat exportado com sucesso para: {pdf_path}"
    except Exception as e:
        import traceback # Para depuração
        traceback.print_exc() # Mostra o erro completo no console para depuração
        #print(f"DEBUG: Erro na exportação do PDF: {e}") # Print de depuração
        return f"Erro ao exportar chat para PDF: {e}"

def list_exported_pdfs(session_name: str = None) -> list:
    """
    Lista todos os PDFs de interações exportados.
    Se session_name for fornecido, lista apenas os exports daquela sessão.
    """
    _ensure_dir_exists(EXPORTS_DIR) # Garante que o diretório base exista

    exported_files = []
    if session_name:
        # Lista exports para uma sessão específica
        session_export_dir = os.path.join(EXPORTS_DIR, session_name)
        if os.path.exists(session_export_dir):
            for filename in os.listdir(session_export_dir):
                if filename.endswith(".pdf"):
                    exported_files.append(f"{session_name}/{filename}")
    else:
        # Lista todos os exports de todas as sessões
        for session_dir in os.listdir(EXPORTS_DIR):
            session_path = os.path.join(EXPORTS_DIR, session_dir)
            if os.path.isdir(session_path):
                for filename in os.listdir(session_path):
                    if filename.endswith(".pdf"):
                        exported_files.append(f"{session_dir}/{filename}")
    return exported_files

def get_exported_pdf_path(session_name: str, export_name: str) -> str:
    """
    Retorna o caminho completo de um PDF de interação exportado específico.
    """
    #print(f"DEBUG (get_exported_pdf_path): Tentando obter caminho para sessão='{session_name}', export_name='{export_name}'")
    pdf_path = _get_export_path(session_name, export_name)
    #print(f"DEBUG (get_exported_pdf_path): Caminho construído: '{pdf_path}'")
    if os.path.exists(pdf_path):
        #print(f"DEBUG (get_exported_pdf_path): Arquivo encontrado em: '{pdf_path}'")
        return pdf_path
    #print(f"DEBUG (get_exported_pdf_path): Arquivo NÃO encontrado em: '{pdf_path}'")
    return None

def delete_exported_pdf(session_name: str, export_name: str) -> bool:
    """
    Exclui um PDF de interação exportado específico.
    """
    #print(f"DEBUG (delete_exported_pdf): Tentando excluir para sessão='{session_name}', export_name='{export_name}'")
    pdf_path = _get_export_path(session_name, export_name)
    #print(f"DEBUG (delete_exported_pdf): Caminho construído para exclusão: '{pdf_path}'")
    if os.path.exists(pdf_path):
        #print(f"DEBUG (delete_exported_pdf): Arquivo encontrado para exclusão em: '{pdf_path}'")
        try:
            os.remove(pdf_path)
            #print(f"DEBUG (delete_exported_pdf): Arquivo removido: '{pdf_path}'")
            # Tenta remover o diretório da sessão se estiver vazio
            session_export_dir = os.path.join(EXPORTS_DIR, session_name)
            if not os.listdir(session_export_dir): # Verifica se o diretório está vazio
                #print(f"DEBUG (delete_exported_pdf): Diretório da sessão vazio, tentando remover: '{session_export_dir}'")
                os.rmdir(session_export_dir)
                #print(f"DEBUG (delete_exported_pdf): Diretório da sessão removido: '{session_export_dir}'")
            return True
        except Exception as e:
            #print(f"DEBUG (delete_exported_pdf): Erro ao excluir PDF de exportação: {e}")
            print(f"Erro ao excluir PDF de exportação: {e}")
            return False
        #print(f"DEBUG (delete_exported_pdf): Arquivo NÃO encontrado para exclusão em: '{pdf_path}'")
    return False

# --- Bloco de Teste (apenas para depuração do módulo) ---
if __name__ == "__main__":
    print("Testando pdf_exporter.py...")

    # Certifica-se que o diretório de exports existe para o teste
    _ensure_dir_exists(EXPORTS_DIR)

    test_session = "TESTE_SESSAO_EXPORT"
    test_export_name = "Interacao_Exemplo"
    test_export_name_2 = "Outra_Interacao"

    # Simula um histórico de chat
    test_chat_history = [
        {"role": "system", "content": "Você é um assistente de teste."},
        {"role": "user", "content": "Olá, bot de teste! Como você está?"},
        {"role": "assistant", "content": "Olá! Estou funcionando perfeitamente."},
        {"role": "user", "content": "Pode me falar sobre a fpdf2?"},
        {"role": "assistant", "content": "A fpdf2 é uma biblioteca Python para geração de PDFs de forma simples e eficiente."},
    ]

    print("\n--- Teste de Exportação ---")
    export_result = export_chat_to_pdf(test_chat_history, test_session, test_export_name)
    print(export_result)

    export_result_2 = export_chat_to_pdf([{"role": "user", "content": "Mais um teste"}], test_session, test_export_name_2)
    print(export_result_2)

    print("\n--- Teste de Listagem (sessão específica) ---")
    listed_for_session = list_exported_pdfs(test_session)
    print(f"Exports para '{test_session}': {listed_for_session}")

    print("\n--- Teste de Listagem (todos os exports) ---")
    all_listed = list_exported_pdfs()
    print(f"Todos os Exports: {all_listed}")

    print("\n--- Teste de Obter Caminho ---")
    path_found = get_exported_pdf_path(test_session, test_export_name)
    print(f"Caminho do '{test_export_name}': {path_found}")

    print("\n--- Teste de Exclusão ---")
    if delete_exported_pdf(test_session, test_export_name):
        print(f"'{test_export_name}.pdf' excluído com sucesso.")
    else:
        print(f"Falha ao excluir '{test_export_name}.pdf' ou não encontrado.")

    if delete_exported_pdf(test_session, test_export_name_2):
        print(f"'{test_export_name_2}.pdf' excluído com sucesso.")
    else:
        print(f"Falha ao excluir '{test_export_name_2}.pdf' ou não encontrado.")

    print("\n--- Teste de Listagem Após Exclusão ---")
    all_listed_after_delete = list_exported_pdfs()
    print(f"Todos os Exports Após Exclusão: {all_listed_after_delete}")

    # Limpeza final do diretório de teste, se estiver vazio
    test_session_export_dir = os.path.join(EXPORTS_DIR, test_session)
    if os.path.exists(test_session_export_dir) and not os.listdir(test_session_export_dir):
        try:
            os.rmdir(test_session_export_dir)
            print(f"Diretório de teste '{test_session_export_dir}' removido.")
        except Exception as e:
            print(f"Erro ao remover diretório de teste: {e}")
