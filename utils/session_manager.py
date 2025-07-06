# session_manager.py

import json
import os
import sys
import datetime
import uuid # Para gerar IDs únicos para os resumos

# Adiciona o diretório raiz do projeto ao sys.path para permitir importações absolutas
# quando o módulo é executado diretamente.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.insert(0, project_root)

# Importa as configurações de caminhos do config.py
from config.config import SESSIONS_DIR, SUMMARIES_DIR, DEFAULT_SESSION_NAME, SYSTEM_MESSAGE

# --- Funções Auxiliares ---
def _ensure_dir_exists(directory_path: str):
    """Garante que um diretório exista. Se não existir, ele é criado."""
    os.makedirs(directory_path, exist_ok=True)

def _get_session_path(session_name: str) -> str:
    """Retorna o caminho completo para o arquivo de uma sessão."""
    _ensure_dir_exists(SESSIONS_DIR)
    return os.path.join(SESSIONS_DIR, f"{session_name}.json")

def _get_summary_path(summary_id: str) -> str:
    """Retorna o caminho completo para o arquivo de um resumo."""
    _ensure_dir_exists(SUMMARIES_DIR)
    return os.path.join(SUMMARIES_DIR, f"{summary_id}.json")


# --- Gerenciamento de Sessões ---
def load_session(session_name: str) -> dict:
    session_path = _get_session_path(session_name)
    if os.path.exists(session_path):
        try:
            with open(session_path, 'r', encoding='utf-8') as f:
                session_data = json.load(f) # <--- Linha existente

            # --- Adicione as validações de estrutura AQUI ---
            if not isinstance(session_data, dict):
                print(f"Aviso: Sessão '{session_name}' carregada, mas o conteúdo não é um dicionário. Revertendo para padrão.")
                return {
                    "chat_history": [{"role": "system", "content": SYSTEM_MESSAGE}],
                    "active_api_summary_content": None,
                    "active_api_summary_metadata": None
                }

            # Garante que 'chat_history' é uma lista
            if "chat_history" not in session_data or not isinstance(session_data["chat_history"], list):
                print(f"Aviso: Sessão '{session_name}' tem 'chat_history' inválido. Revertendo para histórico padrão.")
                session_data["chat_history"] = [{"role": "system", "content": SYSTEM_MESSAGE}]

            # Garante que 'active_api_summary_content' é uma string ou None
            if "active_api_summary_content" not in session_data or not isinstance(session_data["active_api_summary_content"], (str, type(None))):
                session_data["active_api_summary_content"] = None

            # Garante que 'active_api_summary_metadata' é um dicionário ou None
            if "active_api_summary_metadata" not in session_data or not isinstance(session_data["active_api_summary_metadata"], (dict, type(None))):
                session_data["active_api_summary_metadata"] = None
            # --- Fim das validações de estrutura ---

            print(f"Sessão '{session_name}' carregada com sucesso.")
            return session_data
        except json.JSONDecodeError as e:
            print(f"Erro ao decodificar a sessão '{session_name}': {e}. Criando uma nova sessão.")
            # Se o arquivo estiver corrompido, retorna uma sessão padrão
            return {
                "chat_history": [{"role": "system", "content": SYSTEM_MESSAGE}],
                "active_api_summary_content": None,
                "active_api_summary_metadata": None
            }
    else: # Este é o bloco para quando a sessão não existe no disco
        print(f"Sessão '{session_name}' não encontrada. Iniciando uma nova sessão.")
        return {
            "chat_history": [{"role": "system", "content": SYSTEM_MESSAGE}],
            "active_api_summary_content": None,
            "active_api_summary_metadata": None
        }

# ... (suas funções load_session, save_session, list_sessions, delete_session) ...

def session_exists(session_name: str) -> bool:
    """
    Verifica se uma sessão com o nome fornecido existe no disco.

    Args:
        session_name (str): O nome da sessão a ser verificada.

    Returns:
        bool: True se a sessão existir, False caso contrário.
    """
    return os.path.exists(_get_session_path(session_name))

# ... (suas funções load_session, save_session, list_sessions, delete_session) ...

def session_exists(session_name: str) -> bool:
    """
    Verifica se uma sessão com o nome fornecido existe no disco.

    Args:
        session_name (str): O nome da sessão a ser verificada.

    Returns:
        bool: True se a sessão existir, False caso contrário.
    """
    return os.path.exists(_get_session_path(session_name))

def save_session(session_name: str, chat_history: list, active_api_summary_content: str = None, active_api_summary_metadata: dict = None):
    """
    Salva o estado atual da sessão de chat.

    Args:
        session_name (str): O nome da sessão a ser salva.
        chat_history (list): A lista de mensagens do histórico de chat.
        active_api_summary_content (str): O conteúdo do resumo ativo, se houver.
        active_api_summary_metadata (dict): Metadados do resumo ativo, se houver.
    """
    session_path = _get_session_path(session_name)
    session_data = {
        "chat_history": chat_history,
        "active_api_summary_content": active_api_summary_content,
        "active_api_summary_metadata": active_api_summary_metadata
    }
    try:
        with open(session_path, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=4, ensure_ascii=False)
        # print(f"Sessão '{session_name}' salva com sucesso.")
    except Exception as e:
        print(f"Erro ao salvar a sessão '{session_name}': {e}")

def list_sessions() -> list:
    """
    Lista todas as sessões salvas.

    Returns:
        list: Uma lista de nomes de sessões.
    """
    _ensure_dir_exists(SESSIONS_DIR)
    sessions = [
        f.replace('.json', '')
        for f in os.listdir(SESSIONS_DIR)
        if f.endswith('.json')
    ]
    return sorted(sessions)

def delete_session(session_name: str) -> bool:
    """
    Exclui uma sessão salva.

    Args:
        session_name (str): O nome da sessão a ser excluída.

    Returns:
        bool: True se a sessão foi excluída com sucesso, False caso contrário.
    """
    session_path = _get_session_path(session_name)
    if os.path.exists(session_path):
        try:
            os.remove(session_path)
            return True
        except Exception as e:
            return False
    else:
        return False

# --- Gerenciamento de Resumos de PDF ---
def save_pdf_summary(summary_content: str, metadata: dict) -> str:
    """
    Salva um resumo de PDF e seus metadados.

    Args:
        summary_content (str): O conteúdo de texto do resumo.
        metadata (dict): Dicionário com metadados do resumo (ex: nome do arquivo original, data).

    Returns:
        str: O ID único do resumo salvo.
    """
    _ensure_dir_exists(SUMMARIES_DIR)
    summary_id = str(uuid.uuid4()) # Gera um ID único
    summary_data = {
        "id": summary_id,
        "timestamp": datetime.datetime.now().isoformat(),
        "content": summary_content,
        "metadata": metadata
    }
    summary_path = _get_summary_path(summary_id)
    try:
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, indent=4, ensure_ascii=False)
        print(f"Resumo do PDF '{metadata.get('original_filename', 'N/A')}' salvo com ID: {summary_id}")
        return summary_id
    except Exception as e:
        print(f"Erro ao salvar o resumo do PDF: {e}")
        return ""

def load_specific_pdf_summary(summary_id: str) -> dict or None:
    """
    Carrega um resumo de PDF específico pelo seu ID.

    Args:
        summary_id (str): O ID único do resumo a ser carregado.

    Returns:
        dict or None: Um dicionário contendo 'content' e 'metadata' do resumo,
                      ou None se o resumo não for encontrado.
    """
    summary_path = _get_summary_path(summary_id)
    if os.path.exists(summary_path):
        try:
            with open(summary_path, 'r', encoding='utf-8') as f:
                summary_data = json.load(f)
            return summary_data
        except json.JSONDecodeError as e:
            print(f"Erro ao decodificar o resumo '{summary_id}': {e}")
            return None
    else:
        print(f"Resumo com ID '{summary_id}' não encontrado.")
        return None

# Em utils/session_manager.py

# ... (código existente, incluindo _get_summary_path) ...

def delete_pdf_summary(summary_id: str) -> bool:
    """
    Exclui um arquivo de resumo de PDF existente.

    Args:
        summary_id (str): O ID do resumo a ser excluído.

    Returns:
        bool: True se o resumo foi excluído com sucesso, False caso contrário.
    """
    summary_path = _get_summary_path(summary_id)
    if os.path.exists(summary_path):
        try:
            os.remove(summary_path)
            return True
        except OSError as e:
            print(f"Erro ao excluir o resumo '{summary_id}': {e}")
            return False
    else:
        return False # Resumo não encontrado

def list_summaries() -> list:
    """
    Lista todos os resumos de PDF salvos.

    Returns:
        list: Uma lista de dicionários, cada um contendo 'id', 'filename' e 'timestamp' do resumo.
    """
    _ensure_dir_exists(SUMMARIES_DIR)
    summaries_info = []
    for f_name in os.listdir(SUMMARIES_DIR):
        if f_name.endswith('.json'):
            summary_id = f_name.replace('.json', '')
            summary_path = _get_summary_path(summary_id)
            try:
                with open(summary_path, 'r', encoding='utf-8') as f:
                    summary_data = json.load(f)
                metadata = summary_data.get('metadata', {})
                summaries_info.append({
                    "id": summary_data.get('id', 'N/A'),
                    "filename": metadata.get('original_filename', 'N/A'),
                    "timestamp": summary_data.get('timestamp', 'N/A')
                })
            except json.JSONDecodeError as e:
                print(f"Aviso: Arquivo de resumo corrompido ou inválido: {f_name} - {e}")
            except Exception as e:
                print(f"Aviso: Erro ao ler resumo: {f_name} - {e}")
    # Ordena os resumos pelo timestamp para que os mais recentes apareçam primeiro
    return sorted(summaries_info, key=lambda x: x.get('timestamp', ''), reverse=True)


if __name__ == "__main__":
    print("Testando session_manager.py...")

    # --- Teste de Sessões ---
    test_session_name = "test_session_123"
    print(f"\n--- Gerenciamento de Sessões ({test_session_name}) ---")

    # 1. Carregar sessão (deve ser nova)
    loaded_session = load_session(test_session_name)
    print(f"Histórico carregado (nova): {loaded_session['chat_history']}")

    # 2. Salvar uma sessão
    test_history = loaded_session['chat_history']
    test_history.append({"role": "user", "content": "Olá, esta é uma mensagem de teste."})
    test_history.append({"role": "assistant", "content": "Entendido. Salvando sessão."})
    save_session(test_session_name, test_history, None, None)

    # 3. Carregar novamente a sessão (agora deve ter histórico)
    loaded_session_again = load_session(test_session_name)
    print(f"Histórico carregado (existente): {loaded_session_again['chat_history']}")

    # 4. Listar sessões
    print("\nSessões Atuais:", list_sessions())

    # 5. Criar outra sessão para listar
    save_session("outra_sessao", [{"role": "user", "content": "Segunda sessão."}], None, None)
    print("Sessões Após criar 'outra_sessao':", list_sessions())

    # --- Teste de Resumos de PDF ---
    print("\n--- Gerenciamento de Resumos de PDF ---")
    test_summary_content = "Este é um resumo de teste de um documento sobre IA."
    test_summary_metadata = {
        "original_filename": "documento_ia.pdf",
        "pages": 5,
        "topic": "Inteligência Artificial"
    }

    # 1. Salvar um resumo
    saved_summary_id = save_pdf_summary(test_summary_content, test_summary_metadata)
    if saved_summary_id:
        print(f"Resumo de PDF salvo com ID: {saved_summary_id}")

        # 2. Carregar o resumo salvo
        loaded_summary = load_specific_pdf_summary(saved_summary_id)
        if loaded_summary:
            print(f"Conteúdo do resumo carregado: '{loaded_summary['content'][:50]}...'")
            print(f"Metadados do resumo carregado: {loaded_summary['metadata']}")

    # 3. Listar resumos
    print("\nResumos Atuais:")
    for summary in list_summaries():
        print(f"- ID: {summary['id']}, Arquivo: {summary['filename']}, Data: {summary['timestamp']}")

    # --- Limpeza ---
    print("\n--- Limpeza ---")
    # Deletar sessões de teste
    delete_session(test_session_name)
    delete_session("outra_sessao")
    print("Sessões Após limpeza:", list_sessions())

    # (Não há função para deletar resumo individualmente no teste, mas a sessão o gerencia)
    # Em um cenário real, você poderia adicionar uma função de exclusão de resumo se necessário.
