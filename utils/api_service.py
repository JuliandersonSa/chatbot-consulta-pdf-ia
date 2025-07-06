#api_service.py

import os
import sys
from openai import OpenAI
from openai import RateLimitError, APIConnectionError, OpenAIError

# Adiciona o diretório raiz do projeto ao sys.path para permitir importações absolutas
# quando o módulo é executado diretamente.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.insert(0, project_root)

from config.config import DEFAULT_MODEL, TEMPERATURE

# Carrega a chave da API do arquivo .env
# Verifica se a chave OPENAI_API_KEY está definida como variável de ambiente.
# Se não estiver, tenta carregá-la do arquivo .env.
if "OPENAI_API_KEY" not in os.environ:
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("Chave de API OpenAI carregada do arquivo .env")
    except ImportError:
        print("Aviso: python-dotenv não está instalado. Não foi possível carregar variáveis do .env.")
        print("Por favor, instale com 'pip install python-dotenv' ou defina OPENAI_API_KEY manualmente.")

API_KEY = os.getenv("OPENAI_API_KEY")

if not API_KEY:
    raise ValueError("A chave OPENAI_API_KEY não foi encontrada. Por favor, defina-a no seu ambiente ou no arquivo .env.")

client = OpenAI(api_key=API_KEY)

def get_openai_completion(messages: list, model: str = DEFAULT_MODEL, temperature: float = TEMPERATURE, max_tokens: int = None) -> str:
    """
    Obtém uma resposta do modelo de linguagem da OpenAI.

    Args:
        messages (list): Uma lista de dicionários de mensagens para enviar à API.
                         Ex: [{"role": "system", "content": "You are a helpful assistant."},
                              {"role": "user", "content": "Hello!"}]
        model (str): O nome do modelo da OpenAI a ser usado (ex: "gpt-3.5-turbo").
        temperature (float): A temperatura para controlar a criatividade da resposta (0.0 a 2.0).
        max_tokens (int, optional): O número máximo de tokens na resposta gerada.
                                    Se None, a API usará seu padrão.

    Returns:
        str: A resposta de texto do modelo, ou uma string vazia se houver um erro.
    """
    try:
        # Constrói o dicionário de argumentos para a chamada da API
        completion_args = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }
        # Adiciona max_tokens apenas se for fornecido (não None)
        if max_tokens is not None:
            completion_args["max_tokens"] = max_tokens

        chat_completion = client.chat.completions.create(**completion_args)
        return chat_completion.choices[0].message.content
    except RateLimitError:
        print("Erro de limite de taxa da OpenAI: Muitas requisições. Por favor, espere um pouco.")
    except APIConnectionError as e:
        print(f"Erro de conexão com a API da OpenAI: {e}")
        print("Verifique sua conexão com a internet ou a URL da API.")
    except OpenAIError as e:
        print(f"Erro da API OpenAI: {e}")
        print("Verifique sua chave de API ou se há algum problema com o serviço da OpenAI.")
    except Exception as e:
        print(f"Ocorreu um erro inesperado ao chamar a API: {e}")
    return ""

if __name__ == "__main__":
    print("Testando api_service.py...")

    # Teste básico
    test_messages = [
        {"role": "system", "content": "Você é um assistente prestativo."},
        {"role": "user", "content": "Qual a capital do Brasil?"}
    ]

    print("\nTestando get_openai_completion sem max_tokens:")
    response = get_openai_completion(test_messages)
    print("Resposta da API:", response)

    # Teste com max_tokens (resposta curta esperada)
    test_messages_short = [
        {"role": "system", "content": "Responda de forma extremamente concisa."},
        {"role": "user", "content": "Quem descobriu o Brasil?"}
    ]
    print("\nTestando get_openai_completion com max_tokens=10:")
    response_short = get_openai_completion(test_messages_short, max_tokens=10)
    print("Resposta da API (curta):", response_short)

    # Teste de erro (ex: modelo inválido)
    print("\nTestando com modelo inválido (deve gerar erro):")
    error_response = get_openai_completion(test_messages, model="modelo_invalido_xyz")
    if not error_response:
        print("Teste de erro bem-sucedido: Não houve resposta (como esperado para modelo inválido).")
