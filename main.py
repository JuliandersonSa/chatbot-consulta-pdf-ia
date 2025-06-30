import os
import sys
import datetime # Importado para timestamp dos resumos
import uuid     # Importado para gerar IDs de resumo
import traceback
from utils import pdf_exporter

# --- Funçõe Auxiliare de Exibição no Terminal ---

def print_separator(char="=", length=60):
    """Imprime uma linha de separação no terminal."""
    print(char * length)

# Adiciona o diretório raiz do projeto ao sys.path para garantir que as importações funcionem
# quando main.py é executado de qualquer subdiretório (embora geralmente seja da raiz).
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_root)

# Importa módulos e configurações
from config.config import (
    DEFAULT_MODEL, TEMPERATURE, MAX_TOKENS_LIMIT, HISTORY_MESSAGE_LIMIT,
    SYSTEM_MESSAGE, SUMMARY_INSTRUCTION_MESSAGE, DEFAULT_SESSION_NAME,
    PDFS_DIR, COMMANDS, SUMMARY_MAX_TOKENS # SUMMARY_MAX_TOKENS importado aqui
)
from utils import api_service, pdf_processor, session_manager, token_utils, pdf_exporter

# --- Variáveis de Estado Global ---
# Histórico de mensagens da sessão atual
chat_history = []
# Conteúdo do resumo do PDF atualmente ativo na API
active_api_summary_content = None
# Metadados do resumo do PDF atualmente ativo (ex: nome do arquivo original)
active_api_summary_metadata = None
# Nome da sessão de chat atualmente ativa
current_session_name = DEFAULT_SESSION_NAME

# --- Funções Auxiliares de Gerenciamento de Sessão ---

# --- Funções Auxiliares de Gerenciamento de Sessão ---

def load_session_state(session_name: str):
    """Carrega o estado de uma sessão."""
    global chat_history, active_api_summary_content, active_api_summary_metadata, current_session_name

   # print(f"DEBUG: Tentando carregar sessão: {session_name}")
    loaded_data = session_manager.load_session(session_name)
    #print(f"DEBUG: Tipo de loaded_data: {type(loaded_data)}, Valor: {loaded_data}")

    if loaded_data: # Início do bloco principal 'if loaded_data'
        loaded_chat_history = loaded_data.get("chat_history", [])
       # print(f"DEBUG: Tipo de loaded_chat_history: {type(loaded_chat_history)}, Valor: {loaded_chat_history}")

        loaded_active_api_summary_content = loaded_data.get("active_api_summary_content", None)
        loaded_active_api_summary_metadata = loaded_data.get("active_api_summary_metadata", None)

        # Início do bloco 'if' interno para ajustar o histórico de chat
        if (not loaded_chat_history or
            not isinstance(loaded_chat_history[0], dict) or # Esta é a linha onde o erro estava
            loaded_chat_history[0].get("role") != "system"):
            # Estas linhas são o corpo do 'if' interno. Devem estar indentadas.
            chat_history = [{"role": "system", "content": SYSTEM_MESSAGE}] + \
                           [m for m in loaded_chat_history if isinstance(m, dict) and m.get("role") != "system"]
        else: # 'else' do 'if' interno
            chat_history = loaded_chat_history
        # Fim do bloco 'if/else' interno

        # Estas linhas pertencem ao bloco principal 'if loaded_data'.
        # Elas devem estar na mesma indentação do 'if' interno acima.
        active_api_summary_content = loaded_active_api_summary_content
        active_api_summary_metadata = loaded_active_api_summary_metadata
        current_session_name = session_name
        print_separator()
        print(f"Sessão '{current_session_name}' carregada com sucesso.") # Mensagem de sucesso aqui
        print_separator()
        # Aprimoramento: Verifica se ambos, conteúdo E metadados, existem
        if active_api_summary_content and active_api_summary_metadata:
            print(f"Resumo ativo: {active_api_summary_metadata.get('original_filename', 'PDF Desconhecido')}")
        else:
            print("Nenhum resumo de PDF ativo nesta sessão.")

    else: # 'else' do bloco principal 'if loaded_data', para quando a sessão não existe
        print(f"Sessão '{session_name}' não encontrada. Iniciando uma nova sessão.")
        chat_history = [{"role": "system", "content": SYSTEM_MESSAGE}]
        active_api_summary_content = None
        active_api_summary_metadata = None
        current_session_name = session_name
        session_manager.save_session(current_session_name, chat_history, active_api_summary_content, active_api_summary_metadata)

# --- Funções Auxiliares de Gerenciamento de Sessão ---

def save_session_state():
    """Salva o estado atual da sessão."""
    session_manager.save_session(current_session_name, chat_history, active_api_summary_content, active_api_summary_metadata)
    print(f"Sessão '{current_session_name}' salva.")

# --- Funções de Comando ---

def handle_read_pdf(file_name: str):
    """Processa o comando /lerpdf."""
    global active_api_summary_content, active_api_summary_metadata, chat_history
    pdf_path = os.path.join(PDFS_DIR, file_name)
    print(f"Lendo PDF de '{pdf_path}'...")

    extracted_text = pdf_processor.extract_text_from_pdf(pdf_path)

    if not extracted_text:
        print("Erro: Não foi possível extrair texto do PDF ou o arquivo está vazio.")
        return

    print("Texto extraído. Gerando resumo do PDF via OpenAI API (isso pode levar um tempo)...")

    # Preparar mensagens para a API para resumir o PDF
    summary_prompt_messages = [
        {"role": "system", "content": "Você é um assistente especializado em criar resumos concisos e objetivos de documentos. Seu objetivo é extrair as informações mais importantes e apresentá-las de forma clara. Responda apenas com o resumo."},
        {"role": "user", "content": f"Resuma o seguinte texto de um documento PDF, focando nos pontos chave e informações mais relevantes. Seja conciso e direto. Texto do PDF:\n\n{extracted_text}"}
    ]

    # Contar tokens do prompt do resumo para evitar exceder o limite
    prompt_tokens = token_utils.count_tokens_in_messages(summary_prompt_messages)
    
    # Lógica de Truncamento Aprimorada:
    # Considera o limite de tokens do modelo menos uma margem para a resposta do resumo
    # e uma margem de segurança para o sistema/instrução (ex: 200 tokens).
    max_prompt_tokens_allowed = MAX_TOKENS_LIMIT - SUMMARY_MAX_TOKENS - 200 

    if prompt_tokens > max_prompt_tokens_allowed:
        print(f"Aviso: O texto do PDF é muito longo ({prompt_tokens} tokens) para ser resumido no modelo atual.")
        print(f"Truncando o texto do PDF para caber no limite de {max_prompt_tokens_allowed} tokens...")
        
        # Truncar o texto do PDF
        encoded_text = token_utils.ENCODER.encode(extracted_text)
        
        # Garante que não tentamos fatiar mais do que o texto tem
        if len(encoded_text) > max_prompt_tokens_allowed:
            truncated_encoded_text = encoded_text[:max_prompt_tokens_allowed]
            extracted_text = token_utils.ENCODER.decode(truncated_encoded_text)
        else:
            # Caso o texto original já fosse menor que o limite permitido após margem,
            # mas ainda excedia o MAX_TOKENS_LIMIT total, isso não deve ocorrer com a lógica
            # de max_prompt_tokens_allowed, mas é uma salvaguarda.
            print("Erro inesperado durante o truncamento: texto não reduzido o suficiente.")
            return

        # Atualiza a mensagem do usuário com o texto truncado
        summary_prompt_messages[1]["content"] = f"Resuma o seguinte texto de um documento PDF, focando nos pontos chave e informações mais relevantes. Seja conciso e direto. Texto do PDF:\n\n{extracted_text}"
        
        # Recalcula prompt_tokens com o texto truncado
        prompt_tokens = token_utils.count_tokens_in_messages(summary_prompt_messages)
        print(f"Texto do PDF truncado. Novo tamanho do prompt: {prompt_tokens} tokens.")
    
    # Se mesmo após a tentativa de truncar ainda for muito grande, ou se a lógica
    # de limite não funcionou como esperado.
    if prompt_tokens > MAX_TOKENS_LIMIT - 100: # Pequena margem de segurança final
        print("Erro: O prompt do resumo ainda é muito grande mesmo após truncamento. Não é possível gerar resumo.")
        return

    # Chamada à API da OpenAI com o max_tokens corrigido
    summary_response = api_service.get_openai_completion(
        messages=summary_prompt_messages,
        model=DEFAULT_MODEL,
        temperature=TEMPERATURE,
        max_tokens=SUMMARY_MAX_TOKENS  # Usando a constante definida em config.py
    )

    if summary_response:
        active_api_summary_content = summary_response
        active_api_summary_metadata = {
            "original_filename": file_name,
            "timestamp": datetime.datetime.now().isoformat(),
            "summary_id": str(uuid.uuid4()) # Gera um ID temporário que será atualizado após salvar
        }
        # Salva o resumo no sistema de arquivos
        actual_summary_id = session_manager.save_pdf_summary(active_api_summary_content, active_api_summary_metadata)
        active_api_summary_metadata["summary_id"] = actual_summary_id # Atualiza com o ID real

        print(f"\nResumo gerado e definido como contexto ativo para a sessão '{current_session_name}'.")
        print("Você pode fazer perguntas sobre o PDF agora.")
        # Opcional: Adicionar uma mensagem ao histórico indicando que um resumo foi carregado
        chat_history.append({"role": "system", "content": f"Resumo do PDF '{file_name}' carregado e pronto para consultas."})
    else:
        print("Não foi possível gerar o resumo do PDF.")
        active_api_summary_content = None
        active_api_summary_metadata = None

def handle_new_session(args: list):
    """Processa o comando /nova_sessao."""
    global current_session_name
    if len(args) < 1:
        print("Uso: /nova_sessao <nome_da_sessao>")
        return
    
    save_session_state() # Salva a sessão atual antes de mudar
    new_session_name = args[0]
    # Cria uma nova sessão com estado inicial
    session_manager.save_session(new_session_name, {
        "chat_history": [{"role": "system", "content": SYSTEM_MESSAGE}],
        "active_api_summary_content": None,
        "active_api_summary_metadata": None
    })
    load_session_state(new_session_name)
    print(f"Sessão '{new_session_name}' criada e ativada.")

def handle_load_session(args: list):
    """Processa o comando /carregar_sessao."""
    if len(args) < 1:
        print("Uso: /carregar_sessao <nome_da_sessao>")
        return
    
    session_to_load = args[0]
    if session_manager.session_exists(session_to_load):
        save_session_state() # Salva a sessão atual antes de carregar outra
        load_session_state(session_to_load)
    else:
        print(f"Sessão '{session_to_load}' não encontrada.")

def handle_list_sessions():
    """Processa o comando /listar_sessoes."""
    sessions = session_manager.list_sessions()
    if sessions:
        print("\nSessões salvas:")
        for session in sessions:
            status = "(Atual)" if session == current_session_name else ""
            print(f"- {session} {status}")
    else:
        print("Nenhuma sessão salva.")

def handle_delete_session(args: list):
    """Processa o comando /excluir_sessao."""
    if len(args) < 1:
        print("Uso: /excluir_sessao <nome_da_sessao>")
        return
    
    session_to_delete = args[0]
    if session_to_delete == current_session_name:
        print("Não é possível excluir a sessão ativa. Mude para outra sessão ou crie uma nova primeiro.")
        return

    if session_manager.session_exists(session_to_delete):
        session_manager.delete_session(session_to_delete)
        print(f"Sessão '{session_to_delete}' excluída com sucesso.")
    else:
        print(f"Sessão '{session_to_delete}' não encontrada.")

def handle_delete_summary(args: list):
    """Processa o comando /excluir_resumo."""
    global active_api_summary_content, active_api_summary_metadata, chat_history

    if len(args) < 1:
        print("Uso: /excluir_resumo <ID_do_resumo_ou_numero>")
        return

    summaries = session_manager.list_summaries()
    target_summary_id = None
    target_summary_filename = "Resumo Desconhecido" # Para mensagens de feedback

    try:
        # Tenta excluir por número na lista (ex: /excluir_resumo 1)
        index = int(args[0]) - 1
        if 0 <= index < len(summaries):
            target_summary_data = summaries[index]
            target_summary_id = target_summary_data['id']
            target_summary_filename = target_summary_data['filename']
        else:
            print(f"Número '{args[0]}' fora do intervalo. Use /listar_resumos para ver os números válidos.")
            return
    except ValueError:
        # Tenta excluir por ID direto (ex: /excluir_resumo 7ae7cf17-d96d-4640-872e-22ec38bbaf4c)
        input_id = args[0]
        found_by_id = False
        for s in summaries:
            if s['id'] == input_id:
                target_summary_id = s['id']
                target_summary_filename = s['filename']
                found_by_id = True
                break
        if not found_by_id:
            print(f"ID de resumo '{input_id}' não encontrado.")
            return

    if target_summary_id:
        # Se o resumo a ser excluído é o resumo ativo, descarrega-o primeiro
        if active_api_summary_metadata and active_api_summary_metadata.get('summary_id') == target_summary_id:
            active_api_summary_content = None
            active_api_summary_metadata = None
            print(f"O resumo ativo ('{target_summary_filename}') foi descarregado antes da exclusão.")

        if session_manager.delete_pdf_summary(target_summary_id):
            print(f"Resumo '{target_summary_filename}' (ID: {target_summary_id}) excluído com sucesso.")
            save_session_state() # Salva o estado da sessão após a exclusão para refletir a remoção
        else:
            print(f"Não foi possível excluir o resumo com ID '{target_summary_id}'.")

# IMPORTANTE: Certifique-se de que 'os' esteja importado no topo do main.py
import os

# ... (suas funções handle_existentes, por exemplo, após handle_delete_summary ou handle_clear_context)

def handle_export_chat(args: list):
    """
    Exporta o histórico do chat atual para um arquivo PDF.
    Uso: /exportar_chat <nome_do_export>
    """
    if not args:
        print(f"Uso: {COMMANDS['export_chat']} <nome_do_export>. Por favor, forneça um nome para o arquivo PDF.")
        return

    export_name = args[0] # O nome do export é o primeiro argumento
    if not export_name:
        print("O nome do export não pode estar vazio. Por favor, forneça um nome válido.")
        return

    print(f"Exportando chat da sessão '{current_session_name}' para PDF '{export_name}.pdf'...")
    # A função export_chat_to_pdf espera o histórico completo da sessão
    # E o nome da sessão para organizar os arquivos
    result = pdf_exporter.export_chat_to_pdf(chat_history, current_session_name, export_name)
    print(result)

def handle_list_exports(args: list): # 'args' para possível filtro futuro
    """
    Lista os PDFs de chat exportados para a sessão atual.
    Uso: /listar_exports
    """
    session_to_list = current_session_name # Por padrão, lista da sessão atual
    if args:
        # Se um argumento for fornecido, tente listar para essa sessão
        session_to_list = args[0]
        print(f"Listando exports para a sessão: '{session_to_list}'...")
    else:
        print(f"Listando exports para a sessão atual: '{session_to_list}'...")

    exports = pdf_exporter.list_exported_pdfs(session_to_list)

    if exports:
        print(f"\nExports disponíveis para a sessão '{session_to_list}':")
        for i, exp in enumerate(exports):
            # O exp retornado é apenas o nome do arquivo, ex: "MeuEstudo.pdf"
            print(f"  {i+1}. {exp}")
    else:
        print(f"Não há exports de chat para a sessão '{session_to_list}'.")
        if args and not os.path.exists(os.path.join(EXPORTS_DIR, session_to_list)):
            print(f"O diretório para a sessão '{session_to_list}' não existe em {EXPORTS_DIR}.")


def handle_load_export(args: list):
    """
    'Carrega' (indica o caminho de) um PDF de chat exportado.
    Uso: /carregar_export <nome_do_export>
    """
    if not args:
        print(f"Uso: {COMMANDS['load_export']} <nome_do_export>. Por favor, forneça o nome do arquivo PDF.")
        return

    export_name = args[0]
    # Adiciona a extensão .pdf se não estiver presente para a busca
    if not export_name.lower().endswith(".pdf"):
        export_name += ".pdf"

    # Tenta obter o caminho completo e verifica se existe
    full_path = pdf_exporter.get_exported_pdf_path(current_session_name, export_name)

    if full_path and os.path.exists(full_path):
        print(f"PDF de exportação '{export_name}' encontrado em: {full_path}")
        print("Você pode acessar este arquivo diretamente para visualização ou compartilhamento.")
    else:
        print(f"PDF de exportação '{export_name}' não encontrado para a sessão '{current_session_name}'.")
        print("Verifique se o nome está correto e se ele foi exportado para esta sessão.")
        handle_list_exports([]) # Sugere listar os exports existentes


def handle_delete_export(args: list):
    """
    Exclui um PDF de chat exportado.
    Uso: /excluir_export <nome_do_export>
    """
    if not args:
        print(f"Uso: {COMMANDS['delete_export']} <nome_do_export>. Por favor, forneça o nome do arquivo PDF a ser excluído.")
        return

    export_name = args[0]
    # Adiciona a extensão .pdf se não estiver presente para a busca e exclusão
    if not export_name.lower().endswith(".pdf"):
        export_name += ".pdf"

    print(f"Tentando excluir o export '{export_name}' da sessão '{current_session_name}'...")
    success = pdf_exporter.delete_exported_pdf(current_session_name, export_name)

    if success:
        print(f"Export '{export_name}' excluído com sucesso da sessão '{current_session_name}'.")
    else:
        print(f"Falha ao excluir o export '{export_name}'. O arquivo pode não existir ou houve um erro.")
        handle_list_exports([]) # Sugere listar os exports existentes para ajudar

def handle_list_summaries():
    print("Resumos de PDF salvos:")
    summaries = session_manager.list_summaries() # Esta linha já está correta
    if summaries:
        # A linha abaixo precisa estar EXATAMENTE assim para formatar a saída
        for i, summary in enumerate(summaries, 1):
            print(f"{i}. ID: {summary['id']} | Arquivo Original: {summary['filename']} | Data: {summary['timestamp']}")
    else:
        print("Nenhum resumo de PDF encontrado.")

def handle_load_summary(args: list):
    """Processa o comando /carregar_resumo."""
    global active_api_summary_content, active_api_summary_metadata, chat_history
    if len(args) < 1:
        print("Uso: /carregar_resumo <ID_do_resumo_ou_numero>")
        return
    
    # Chama a função CORRETA em session_manager e guarda os resumos disponíveis
    available_summaries = session_manager.list_summaries() # CORRIGIDO AQUI
    
    summary_to_load_id = None
    summary_filename_for_display = "PDF Desconhecido" # Usado para mensagens de feedback

    try:
        # Tenta carregar o resumo pelo número na lista exibida
        index = int(args[0]) - 1
        if 0 <= index < len(available_summaries):
            # Extrai o dicionário completo do resumo e obtém o ID e nome do arquivo
            summary_data_from_list = available_summaries[index]
            summary_to_load_id = summary_data_from_list['id']
            summary_filename_for_display = summary_data_from_list.get('filename', summary_filename_for_display)
        else:
            print(f"Número '{args[0]}' fora do intervalo. Use /listar_resumos para ver os números válidos.")
            return
    except ValueError:
        # Se o argumento não for um número, tenta carregar o resumo por ID (string)
        input_id_string = args[0]
        found_by_id = False
        for s_data in available_summaries: # Itera sobre os dicionários de resumos disponíveis
            if s_data['id'] == input_id_string: # Compara o ID fornecido com o ID de cada resumo
                summary_to_load_id = s_data['id']
                summary_filename_for_display = s_data.get('filename', summary_filename_for_display)
                found_by_id = True
                break
        
        if not found_by_id:
            print(f"ID de resumo '{input_id_string}' não encontrado.")
            return

    if summary_to_load_id:
        # Se um ID válido (seja por número ou string) foi encontrado, tenta carregar o resumo
        summary_data = session_manager.load_specific_pdf_summary(summary_to_load_id)
        if summary_data:
            active_api_summary_content = summary_data.get("content")
            active_api_summary_metadata = summary_data.get("metadata")
            
            # Usa o nome do arquivo dos metadados para exibição, se disponível
            display_filename = active_api_summary_metadata.get('original_filename', summary_filename_for_display)

            print(f"\nResumo '{display_filename}' (ID: {summary_to_load_id}) carregado como contexto ativo.")
            # Adiciona mensagem ao histórico do chat sobre o resumo carregado
            chat_history.append({"role": "system", "content": f"Resumo '{display_filename}' carregado e pronto para consultas."})
            save_session_state() # Salva o estado da sessão com o novo resumo ativo
        else:
            print(f"Não foi possível carregar o resumo com ID '{summary_to_load_id}'.")

def handle_clear_context():
    """Processa o comando /limpar."""
    global chat_history, active_api_summary_content, active_api_summary_metadata
    chat_history = [{"role": "system", "content": SYSTEM_MESSAGE}] # Reseta histórico, mantendo mensagem do sistema
    active_api_summary_content = None
    active_api_summary_metadata = None
    print("Histórico de chat e contexto de PDF limpos para a sessão atual.")

def handle_help():
    """Exibe a lista de comandos disponíveis."""
    print("\nComandos disponíveis:")
    for cmd_name, cmd_value in COMMANDS.items():
        print(f"- {cmd_value}: {cmd_name.replace('_', ' ').capitalize()}")
    print("- /sair: Salva a sessão atual e encerra o chatbot.")
    print("\nPara fazer perguntas normais, basta digitar sua mensagem.")
    if active_api_summary_content:
        print("Lembre-se: Há um resumo de PDF ativo. Suas perguntas serão respondidas com base nele.")

# --- Loop Principal do Chatbot ---

def run_chatbot():
    """Inicia e executa o loop principal do chatbot."""
    # Carrega o estado inicial da sessão padrão
    load_session_state(DEFAULT_SESSION_NAME)

    print_separator()
    print("Bem-vindo ao Chatbot de Consulta de PDFs!")
    print("Digite suas perguntas ou um comando (ex: /ajuda para ver os comandos).")
    print_separator()

    while True:
        try:
            user_input = input(f"[{current_session_name}] Você: ")
            if not user_input.strip(): # Não processa entrada vazia
                continue

            # Processar comandos
            if user_input.startswith('/'):
                parts = user_input.split(maxsplit=1)
                command = parts[0].lower()
                args = parts[1].split() if len(parts) > 1 else []

                if command == COMMANDS["read_pdf"]:
                    if args:
                        handle_read_pdf(args[0])
                    else:
                        print("Uso: /lerpdf <nome_do_arquivo.pdf>")
                elif command == COMMANDS["new_session"]:
                    handle_new_session(args)
                elif command == COMMANDS["load_session"]:
                    handle_load_session(args)
                elif command == COMMANDS["list_sessions"]:
                    handle_list_sessions()
                elif command == COMMANDS["delete_session"]:
                    handle_delete_session(args)
                elif command == COMMANDS["list_summaries"]:
                    handle_list_summaries()
                elif command == COMMANDS["load_summary"]:
                    handle_load_summary(args)
                elif command == COMMANDS["delete_summary"]:
                    handle_delete_summary(args)
                elif command == COMMANDS["clear_context"]:
                    handle_clear_context()
                elif command == COMMANDS["help"]:
                    handle_help()
                elif command == COMMANDS["exit"]:
                    user_choice = input("\nDeseja exportar o chat atual para PDF antes de sair? (s/n): ").lower().strip()
                    
                    if user_choice == 's':
                        export_name = input("Por favor, digite um nome para o arquivo PDF (ex: MinhaConversaImportante): ").strip()
                        if export_name:
                            result = pdf_exporter.export_chat_to_pdf(chat_history, current_session_name, export_name)
                            print(result)
                        else:
                            print("Nome de exportação vazio. O chat não será exportado.")
                    elif user_choice == 'n':
                        print("Chat não exportado.")
                    else:
                        print("Opção inválida. Chat não exportado.")
                    
                    save_session_state()
                    print("Saindo do chatbot. Até mais!")
                    break
                # --- NOVOS COMANDOS DE EXPORTAÇÃO ---
                elif command == COMMANDS["export_chat"]:
                    handle_export_chat(args)
                elif command == COMMANDS["list_exports"]:
                    handle_list_exports(args)
                elif command == COMMANDS["load_export"]:
                    handle_load_export(args)
                elif command == COMMANDS["delete_export"]:
                    handle_delete_export(args)
                # --- FIM DOS NOVOS COMANDOS ---
                else:
                    print(f"Comando '{command}' não reconhecido. Digite /ajuda para ver os comandos.")
            else:
                # Se não for um comando, é uma pergunta ao chatbot
                user_message = {"role": "user", "content": user_input}
                
                # Preparar mensagens para a API
                messages_for_api = []

                # Incluir mensagem de instrução de resumo se houver um resumo ativo
                if active_api_summary_content:
                    summary_context_message = {
                        "role": "user",
                        "content": f"{SUMMARY_INSTRUCTION_MESSAGE}\n\nResumo do Documento:\n{active_api_summary_content}"
                    }
                    messages_for_api.append(summary_context_message)

                # Adicionar histórico de chat limitado (exceto a mensagem de sistema inicial, que já está em chat_history[0])
                # Limita para HISTORY_MESSAGE_LIMIT mensagens do usuário/assistente mais a mensagem do sistema
                messages_for_api.append(chat_history[0]) # Mensagem do sistema
                messages_for_api.extend(chat_history[max(1, len(chat_history) - HISTORY_MESSAGE_LIMIT):])
                
                # Adicionar a mensagem atual do usuário
                messages_for_api.append(user_message)

                # Contar tokens do prompt antes de enviar à API
                api_prompt_tokens = token_utils.count_tokens_in_messages(messages_for_api)

                # Se o prompt for muito longo, alertar e não enviar
                if api_prompt_tokens > MAX_TOKENS_LIMIT:
                    print(f"Aviso: Sua pergunta e o contexto (histórico/resumo) excedem o limite de tokens do modelo ({api_prompt_tokens} tokens). Por favor, limpe o contexto (/limpar) ou faça uma pergunta mais curta.")
                    continue
                
                print("Gerando resposta (isso pode levar um tempo)...")
                # max_tokens para a resposta da IA em conversas normais pode ser DEFAULT_MAX_TOKENS_RESPONSE
                # que podemos adicionar ao config.py, ou deixar a API definir.
                # Aqui, não estamos limitando explicitamente a resposta para conversas gerais,
                # a menos que o DEFAULT_MODEL já tenha um limite de saída implicito.
                bot_response = api_service.get_openai_completion(
                    messages=messages_for_api,
                    model=DEFAULT_MODEL,
                    temperature=TEMPERATURE
                )

                if bot_response:
                    print(f"[{current_session_name}] Bot: {bot_response}")
                    chat_history.append(user_message) # Adiciona a pergunta do usuário
                    chat_history.append({"role": "assistant", "content": bot_response}) # Adiciona a resposta do bot
                    save_session_state() # Salva a sessão após cada interação
                else:
                    print("Não foi possível obter uma resposta do chatbot.")

        except KeyboardInterrupt:
            print("\nEncerrando o chatbot.")
            save_session_state()
            break
        except Exception as e:
            print(f"Ocorreu um erro inesperado: {e}")
            traceback.print_exc()
            # Para depuração, você pode adicionar um traceback mais detalhado:
            # import traceback
            # traceback.print_exc()

if __name__ == "__main__":
    run_chatbot()
