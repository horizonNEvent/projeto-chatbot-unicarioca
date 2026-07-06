import os
import streamlit as st
import pandas as pd
from src.nlp import detectar_intencao, CORPUS
from src.database import consultar_csv, carregar_dados
from src.llm import responder_groq, obter_cliente_groq

# Configuração da página Streamlit (deve ser o primeiro comando Streamlit)
st.set_page_config(
    page_title="BotF1 - Inteligência Artificial de Fórmula 1",
    page_icon="🏎️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização CSS Customizada - Tema Formula 1 Light (Fundo Claro, Detalhes em Vermelho Corrida)
st.markdown("""
<style>
    /* Estilos gerais */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');
    
    html, body, [data-testid="stSidebar"] {
        font-family: 'Outfit', sans-serif;
    }

    /* Alterando cor de fundo do app principal para tema claro */
    .stApp {
        background-color: #f8fafc;
        color: #0f172a;
    }

    /* Customização do título */
    .f1-title {
        color: #E10600;
        font-weight: 800;
        font-size: 2.8rem;
        text-transform: uppercase;
        letter-spacing: -1px;
        margin-bottom: 0px;
        padding-bottom: 0px;
    }

    .f1-subtitle {
        color: #475569;
        font-size: 1.1rem;
        margin-top: -10px;
        margin-bottom: 25px;
        border-left: 3px solid #E10600;
        padding-left: 10px;
    }

    /* Cards de métricas personalizadas - Clean Light Theme */
    .metric-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-left: 4px solid #E10600;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.04);
        text-align: left;
        margin-bottom: 15px;
        transition: all 0.3s ease;
    }

    .metric-card:hover {
        transform: translateY(-3px);
        border-color: rgba(225, 6, 0, 0.5);
        box-shadow: 0 8px 25px rgba(225, 6, 0, 0.1);
    }

    .metric-value {
        font-size: 1.8rem;
        font-weight: 800;
        color: #0f172a;
        margin: 0;
    }

    .metric-label {
        font-size: 0.85rem;
        color: #475569;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-top: 5px;
    }

    .metric-detail {
        font-size: 0.75rem;
        color: #e10600;
        font-weight: 600;
        margin-top: 3px;
    }

    /* Barra lateral em tom claro e limpo */
    [data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 1px solid #e2e8f0;
    }

    /* Ajuste de contraste para campos de entrada (input) ficarem visíveis */
    div[data-baseweb="input"] {
        background-color: #f1f5f9 !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 8px !important;
    }
    
    div[data-baseweb="input"] input {
        color: #0f172a !important;
    }

    .sidebar-header {
        color: #0f172a;
        font-size: 1.4rem;
        font-weight: 700;
        border-bottom: 2px solid #E10600;
        padding-bottom: 5px;
        margin-bottom: 15px;
    }

    /* Badges de Intenção no Chat em estilo claro */
    .intent-badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
        background-color: #f1f5f9;
        color: #475569;
        border: 1px solid #e2e8f0;
        margin-top: 5px;
    }
</style>
""", unsafe_allow_html=True)


# Carrega os dados para uso na página
try:
    df_pilotos = carregar_dados()
except Exception as e:
    st.error(f"Erro ao carregar base de dados de pilotos: {e}")
    df_pilotos = pd.DataFrame()

# --- BARRA LATERAL (SIDEBAR) ---
with st.sidebar:
    st.markdown('<div class="sidebar-header">🏎️ BOTF1 CONTROL</div>', unsafe_allow_html=True)
    
    st.markdown(
        "Bem-vindo ao **BotF1**, um assistente de inteligência artificial "
        "especializado no campeonato de 2024 e história da Fórmula 1."
    )
    
    # Gerenciamento da API Key do Groq
    st.markdown('<div style="margin-top: 20px;"></div>', unsafe_allow_html=True)
    st.subheader("🔑 Chave de API do Groq")
    
    # Tenta ler a API Key da variável de ambiente primeiro para facilitar a experiência do usuário
    env_key = os.environ.get("GROQ_API_KEY", "")
    api_key_input = st.text_input(
        "Insira sua API Key do Groq:",
        value=env_key,
        type="password",
        help="Acesse console.groq.com para gerar uma chave gratuita. Se configurado via variáveis de ambiente/secrets, o app lerá automaticamente."
    )
    
    if api_key_input:
        st.session_state["groq_api_key"] = api_key_input
        st.success("Chave configurada com sucesso!")
    else:
        st.info("💡 Insira a chave acima ou configure a variável `GROQ_API_KEY` para iniciar as conversas.")
        
    st.markdown("---")
    
    # Estatísticas Rápidas do Campeonato (Derivadas do CSV)
    if not df_pilotos.empty:
        st.subheader("📊 Estatísticas F1 2024")
        
        # Piloto Líder
        lider_row = df_pilotos.sort_values("pontos", ascending=False).iloc[0]
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{lider_row['piloto']}</div>
            <div class="metric-label">Líder do Campeonato</div>
            <div class="metric-detail">{lider_row['pontos']} pts ({lider_row['equipe']})</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Maior Vencedor
        vencedor_row = df_pilotos.sort_values("vitorias", ascending=False).iloc[0]
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{vencedor_row['piloto']}</div>
            <div class="metric-label">Mais Vitórias</div>
            <div class="metric-detail">{vencedor_row['vitorias']} vitórias</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Maior Pole Position
        pole_row = df_pilotos.sort_values("poles", ascending=False).iloc[0]
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{pole_row['piloto']}</div>
            <div class="metric-label">Mais Poles</div>
            <div class="metric-detail">{pole_row['poles']} poles</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown('<div style="text-align: center; color: #64748b; font-size: 0.8rem; margin-top: 30px;">BotF1 | Projeto Acadêmico UniCarioca</div>', unsafe_allow_html=True)


# --- ÁREA PRINCIPAL ---
st.markdown('<h1 class="f1-title">🏁 BotF1 - Expert em Fórmula 1</h1>', unsafe_allow_html=True)
st.markdown('<p class="f1-subtitle">Processamento de Linguagem Natural (NLP) e Llama 3 integrado à base oficial de pilotos de 2024</p>', unsafe_allow_html=True)

# Definição das Abas
tab_chatbot, tab_classificacao = st.tabs(["💬 Chatbot Inteligente", "📊 Classificação & Gráficos"])

# ABA 1: CHATBOT
with tab_chatbot:
    st.write(
        "Converse com o BotF1 sobre classificação de pilotos, pontos, estatísticas "
        "ou tire suas dúvidas sobre a categoria mais rápida do automobilismo!"
    )
    
    # Inicializa o histórico do chat
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Olá! Sou o BotF1. O que você gostaria de saber sobre a Fórmula 1?", "intent": "boas_vindas", "score": 1.0}
        ]

    # Exibe as mensagens do histórico
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("intent") and msg["role"] == "assistant":
                # Exibe badge mostrando o processamento NLP por trás
                st.markdown(
                    f'<span class="intent-badge">Intenção: <b>{msg["intent"]}</b> | Confiança NLP: <b>{msg["score"]:.2f}</b></span>',
                    unsafe_allow_html=True
                )

    # Campo de input de chat do usuário
    if prompt := st.chat_input("Pergunte algo sobre F1... (Ex: 'Quais os dados do Verstappen?' ou 'Quem lidera o campeonato?')"):
        
        # Exibe mensagem do usuário no chat
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Processamento do NLP Local (Intent Detection)
        intencao, score, padrao_proximo = detectar_intencao(prompt)
        
        # Lógica de resposta baseada na intenção
        resposta_final = ""
        
        # Se a chave do Groq não estiver definida, mostra aviso amigável
        key_to_use = st.session_state.get("groq_api_key", env_key)
        
        if not key_to_use:
            resposta_final = (
                "⚠️ **Erro de Chave:** Olá! Percebi que você ainda não configurou uma chave de API do Groq. "
                "Para conversar comigo usando inteligência artificial, insira sua chave do Groq no menu lateral (🔑 Chave de API do Groq)."
            )
            # Adiciona ao chat sem precisar rodar o LLM
            with st.chat_message("assistant"):
                st.markdown(resposta_final)
                st.markdown(
                    f'<span class="intent-badge">Intenção: <b>{intencao}</b> | Confiança NLP: <b>{score:.2f}</b></span>',
                    unsafe_allow_html=True
                )
            st.session_state.messages.append({"role": "assistant", "content": resposta_final, "intent": intencao, "score": score})
            
        else:
            # Processamento com LLM e base de dados local
            with st.spinner("Pensando na pista rápida..."):
                try:
                    # Se a intenção for ler dados do CSV
                    if intencao == "consulta_csv":
                        contexto_csv = consultar_csv(prompt)
                        resposta_final = responder_groq(prompt, intencao, contexto_csv=contexto_csv, api_key=key_to_use)
                    else:
                        resposta_final = responder_groq(prompt, intencao, api_key=key_to_use)
                        
                except Exception as e:
                    resposta_final = f"Desculpe, ocorreu um erro ao processar a resposta: {str(e)}"
            
            # Exibe resposta do assistente no chat
            with st.chat_message("assistant"):
                st.markdown(resposta_final)
                st.markdown(
                    f'<span class="intent-badge">Intenção: <b>{intencao}</b> | Confiança NLP: <b>{score:.2f}</b></span>',
                    unsafe_allow_html=True
                )
            st.session_state.messages.append({"role": "assistant", "content": resposta_final, "intent": intencao, "score": score})


# ABA 2: CLASSIFICAÇÃO & GRÁFICOS
with tab_classificacao:
    if not df_pilotos.empty:
        st.subheader("🏆 Tabela Oficial de Pilotos - Temporada 2024")
        st.write("Dados extraídos do arquivo `pilotos_f1_2024.csv`:")
        
        # Exibe dataframe de forma bonita e interativa
        df_formatado = df_pilotos.sort_values("pontos", ascending=False).reset_index(drop=True)
        # Ajusta índice para começar em 1 (Posição)
        df_formatado.index += 1
        df_formatado.index.name = "Posição"
        
        st.dataframe(
            df_formatado,
            column_config={
                "piloto": "Piloto",
                "equipe": "Equipe",
                "nacionalidade": "Nacionalidade",
                "pontos": st.column_config.NumberColumn("Pontuação", format="%d pts"),
                "vitorias": st.column_config.NumberColumn("Vitórias", format="%d 🏆"),
                "podios": st.column_config.NumberColumn("Pódios", format="%d 🥉"),
                "poles": st.column_config.NumberColumn("Poles Position", format="%d ⏱️"),
            },
            use_container_width=True
        )
        
        # Gráfico de barras de pontuação por piloto
        st.markdown("---")
        st.subheader("📊 Comparativo de Pontos por Piloto")
        
        # Ordena pilotos para o gráfico
        df_grafico = df_pilotos.sort_values("pontos", ascending=True)
        
        # Gráfico nativo Streamlit horizontal
        st.bar_chart(
            df_grafico,
            x="piloto",
            y="pontos",
            color="equipe", # Agrupa e colore por equipe de forma inteligente!
            horizontal=True,
            use_container_width=True
        )
        
    else:
        st.warning("Não há dados de pilotos disponíveis para exibir no dashboard.")
