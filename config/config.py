import os

# --- Configurações Gerais do Chatbot ---
# Modelo padrão da OpenAI a ser usado.
# Considere "gpt-4o-mini" para melhor custo-benefício ou "gpt-3.5-turbo" para mais velocidade.
# Modelos disponíveis em: https://platform.openai.com/docs/models/overview
DEFAULT_MODEL = "gpt-4o-mini"

# Criatividade da resposta do modelo (0.0 a 2.0).
# Valores mais baixos são mais focados e determinísticos, valores mais altos são mais criativos.
TEMPERATURE = 0.7

# --- Limites de Contexto e Tokens ---
# Limite máximo de tokens de entrada para o modelo (incluindo System, Histórico e Pergunta).
# Consulte a documentação da OpenAI para os limites específicos do modelo escolhido.
# gpt-3.5-turbo (16k) -> 16385 tokens
# gpt-4o-mini (128k) -> 128000 tokens
MAX_TOKENS_LIMIT = 100000 # Um pouco abaixo do limite do gpt-4o-mini para segurança

# Limite de tokens para a resposta gerada pela IA ao resumir PDFs
SUMMARY_MAX_TOKENS = 1000 # Um valor razoável para a maioria dos resumos. Ajuste conforme necessário.

# Número máximo de mensagens do histórico de chat a serem incluídas na requisição da API.
# Isso ajuda a controlar o uso de tokens e manter o contexto relevante.
# Cada mensagem é um par (user, assistant).
HISTORY_MESSAGE_LIMIT = 10 # Limita o histórico a 10 pares (20 mensagens individuais)

# --- Caminhos de Arquivo e Diretórios ---
# Caminho base para o diretório de dados, relativo ao diretório raiz do projeto.
BASE_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')

# Caminho para o diretório de perfis de usuário.
PROFILES_DIR = os.path.join(BASE_DATA_DIR, 'profiles')

# Caminho para o diretório do perfil padrão (onde sessões e resumos serão salvos).
DEFAULT_PROFILE_DIR = os.path.join(PROFILES_DIR, 'default')

# Caminho para o diretório onde as sessões de chat são salvas.
SESSIONS_DIR = os.path.join(DEFAULT_PROFILE_DIR, 'sessions')

# Caminho para o diretório onde os resumos de PDF são salvos.
SUMMARIES_DIR = os.path.join(DEFAULT_PROFILE_DIR, 'summaries')

# Caminho para o diretório onde os PDFs de interações exportadas serão salvos.
EXPORTS_DIR = os.path.join(DEFAULT_PROFILE_DIR, 'exports')

# Caminho para o diretório onde os PDFs originais são armazenados.
PDFS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'pdfs')

# --- Mensagens Padrão do Sistema ---
# Mensagem de sistema que define o comportamento geral do chatbot.
# Ajuste para definir o "persona" do seu assistente.
SYSTEM_MESSAGE = (
    "Você é um assistente de IA prestativo e conciso, otimizado para responder perguntas "
    "com base em documentos PDF fornecidos. Seja objetivo, direto e sempre baseie suas "
    "respostas no contexto mais recente. Se não souber a resposta com base no contexto, "
    "indique isso. Priorize a eficiência e o uso mínimo de tokens."
)

# Mensagem de instrução que é anexada antes do conteúdo do resumo ativo.
# Isso orienta o modelo sobre como usar o resumo.
SUMMARY_INSTRUCTION_MESSAGE = (
    "O texto a seguir é um resumo de um documento PDF. Utilize-o como seu "
    "principal contexto para responder a perguntas futuras. Priorize "
    "as informações deste resumo ao gerar suas respostas. Se a pergunta "
    "não puder ser respondida com base neste resumo, indique isso. "
    "Resumo do PDF:\n\n"
)

# Nome da sessão padrão que será carregada ou criada ao iniciar o chatbot.
DEFAULT_SESSION_NAME = "default_session"

# --- Comandos do Chatbot ---
# Dicionário de comandos para facilitar a referência e futura expansão.
# Em config/config.py

# --- Comandos do Chatbot ---
# --- Comandos do Chatbot ---
# Dicionário de comandos para facilitar a referência e futura expansão.
COMMANDS = {
    "read_pdf": "/lerpdf",
    "new_session": "/nova_sessao",
    "load_session": "/carregar_sessao", # Mantido como você tem
    "list_sessions": "/listar_sessoes",
    "delete_session": "/excluir_sessao",
    "list_summaries": "/listar_resumos",
    "load_summary": "/carregar_resumo",
    "clear_context": "/limpar",       # Mantido como você tem
    "exit": "/sair",
    "help": "/ajuda",
    "delete_summary": "/excluir_resumo",
    # --- NOVOS COMANDOS DE EXPORTAÇÃO ---
    "export_chat": "/exportar_chat",
    "list_exports": "/listar_exports",
    "load_export": "/carregar_export",
    "delete_export": "/excluir_export",
    # --- FIM DOS NOVOS COMANDOS ---
}
