import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..'))
if project_root not in sys.path:
    sys.path.append(project_root)
import tiktoken
from config.config import DEFAULT_MODEL

# Carrega o codificador de tokens para o modelo padrão.
# O encoding "cl100k_base" é comumente usado por modelos como gpt-3.5-turbo e gpt-4.
ENCODER = tiktoken.get_encoding("cl100k_base")

def count_tokens_in_string(text: str) -> int:
    """
    Conta o número de tokens em uma string de texto usando o codificador padrão.

    Args:
        text (str): A string de texto a ser tokenizada.

    Returns:
        int: O número de tokens na string.
    """
    return len(ENCODER.encode(text))

def count_tokens_in_messages(messages: list) -> int:
    """
    Conta o número de tokens em uma lista de mensagens formatadas para a API do OpenAI.
    Esta função é baseada na documentação da OpenAI para contagem de tokens de mensagens
    e leva em consideração a estrutura de role/content.

    Args:
        messages (list): Uma lista de dicionários de mensagens, como:
                         [{"role": "system", "content": "Seu nome é Bot."},
                          {"role": "user", "content": "Olá!"}]

    Returns:
        int: O número total de tokens nas mensagens.
    """
    # Adaptação para gpt-3.5-turbo e gpt-4 conforme documentação da OpenAI
    # Cada mensagem tem um custo base de 4 tokens (role + content).
    # Algumas versões de modelo podem ter um custo extra de 1 token para respostas.
    # Estamos usando uma abordagem mais segura que se alinha com exemplos da OpenAI.
    tokens_per_message = 3 # Cada mensagem geralmente custa 3 tokens (role, content, e o final do turno)
    tokens_per_name = 1    # Se um nome é fornecido, ele custa 1 token extra.

    total_tokens = 0
    for message in messages:
        total_tokens += tokens_per_message
        for key, value in message.items():
            total_tokens += count_tokens_in_string(value)
            if key == "name":
                total_tokens += tokens_per_name
    total_tokens += 3 # Cada resposta geralmente começa com 'assistant', o que custa 3 tokens.
                      # Esta é uma estimativa, pode variar ligeiramente.
    return total_tokens

if __name__ == "__main__":
    print("Testando token_utils.py...")

    # Teste de contagem de tokens em string
    text_example = "Olá, como você está hoje? Espero que esteja tudo bem!"
    tokens_string = count_tokens_in_string(text_example)
    print(f"\nTexto: '{text_example}'")
    print(f"Tokens na string: {tokens_string}")

    # Teste de contagem de tokens em mensagens
    messages_example = [
        {"role": "system", "content": "Você é um assistente de IA útil."},
        {"role": "user", "content": "Qual a capital do Brasil?"},
        {"role": "assistant", "content": "A capital do Brasil é Brasília."}
    ]
    tokens_messages = count_tokens_in_messages(messages_example)
    print(f"\nMensagens de exemplo: {messages_example}")
    print(f"Tokens nas mensagens (estimado): {tokens_messages}")

    # Exemplo com uma string longa
    long_text = "Isso é um texto muito longo para testar a contagem de tokens. " * 50
    print(f"\nTexto longo (primeiros 50 chars): '{long_text[:50]}...'")
    print(f"Tokens no texto longo: {count_tokens_in_string(long_text)}")
