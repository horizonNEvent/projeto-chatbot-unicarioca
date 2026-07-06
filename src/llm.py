import os
from groq import Groq

# Tentativa de carregar dotenv para desenvolvimento local
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

SYSTEM_PROMPT = """Você é o BotF1, assistente especialista em Fórmula 1.
Responda APENAS sobre Fórmula 1: pilotos, equipes, corridas, regras, história e campeonatos.
Se a pergunta não for sobre F1, diga de forma educada mas direta que só fala sobre F1.
Respostas curtas, objetivas, em português brasileiro, sem emojis.
Não invente dados. Se houver 'Dados da base' fornecidos na pergunta, use-os obrigatoriamente como fonte de verdade para informações sobre pontuações, equipes, vitórias, poles e pódios."""

def obter_cliente_groq(api_key=None):
    """
    Retorna o cliente Groq inicializado a partir da primeira chave encontrada:
    1. Parâmetro direto `api_key`
    2. Variável de ambiente (via os.environ ou arquivo .env)
    3. Streamlit secrets (st.secrets)
    4. Streamlit session_state (st.session_state)
    """
    key = api_key

    # 1. Variável de ambiente
    if not key:
        key = os.environ.get("GROQ_API_KEY")

    # 2. Streamlit Secrets ou Session State
    if not key:
        try:
            import streamlit as st
            if "GROQ_API_KEY" in st.secrets:
                key = st.secrets["GROQ_API_KEY"]
            elif "groq_api_key" in st.session_state and st.session_state["groq_api_key"]:
                key = st.session_state["groq_api_key"]
        except Exception:
            pass

    if not key:
        return None

    return Groq(api_key=key)

def responder_groq(mensagem_usuario, intencao, contexto_csv=None, api_key=None):
    """
    Gera a resposta da inteligência artificial através da API do Groq utilizando Llama 3.
    """
    cliente = obter_cliente_groq(api_key)
    if not cliente:
        raise ValueError(
            "Chave de API do Groq não configurada. "
            "Defina a variável de ambiente GROQ_API_KEY, adicione nos secrets do Streamlit "
            "ou forneça a chave na barra lateral do aplicativo."
        )

    conteudo = f"Intenção detectada: {intencao}\nPergunta: {mensagem_usuario}"
    if contexto_csv:
        conteudo += f"\nDados reais da base de dados F1 2024:\n{contexto_csv}"

    resposta = cliente.chat.completions.create(
        model='llama-3.1-8b-instant',
        messages=[
            {'role': 'system', 'content': SYSTEM_PROMPT},
            {'role': 'user',   'content': conteudo}
        ],
        max_tokens=300,
        temperature=0.4
    )
    return resposta.choices[0].message.content.strip()
