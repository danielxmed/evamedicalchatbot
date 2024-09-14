import streamlit as st
from openai import OpenAI
import json
import os
from pathlib import Path
import pickle

# Configuração da página do Streamlit
st.set_page_config(page_title="Eva Medical Chatbot", page_icon="💊")

# Carrega o prompt do sistema
from prompt_sistema import prompt_do_sistema
prompt_sistema = prompt_do_sistema

# Diretórios para salvar conversas e configurações
PASTA_CONVERSAS = Path('conversas')
PASTA_CONVERSAS.mkdir(exist_ok=True)
PASTA_CONFIGURACOES = Path('configuracoes')
PASTA_CONFIGURACOES.mkdir(exist_ok=True)

# Funções utilitárias para salvar e carregar conversas
def salvar_conversa(nome_conversa, mensagens):
    with open(PASTA_CONVERSAS / f"{nome_conversa}.pkl", "wb") as f:
        pickle.dump(mensagens, f)

def carregar_conversa(nome_conversa):
    with open(PASTA_CONVERSAS / f"{nome_conversa}.pkl", "rb") as f:
        return pickle.load(f)

def listar_conversas():
    conversas = list(PASTA_CONVERSAS.glob("*.pkl"))
    conversas = sorted(conversas, key=lambda x: x.stat().st_mtime, reverse=True)
    return [c.stem for c in conversas]

# Função principal para gerar a resposta do chatbot
def gerar_resposta(cliente, messages):
    response = cliente.chat.completions.create(
        model=st.session_state.modelo,
        messages=messages,
        temperature=1.0,
    )
    return response

# Inicialização da sessão do Streamlit
def inicializacao():
    if 'api_key' not in st.session_state:
        st.session_state.api_key = ''
    if 'cliente' not in st.session_state:
        st.session_state.cliente = None
    if 'modelo' not in st.session_state:
        st.session_state.modelo = 'gpt-3.5-turbo'
    if 'mensagens' not in st.session_state:
        st.session_state.mensagens = []
    if 'conversa_atual' not in st.session_state:
        st.session_state.conversa_atual = ''
    if 'prompt_sistema' not in st.session_state:
        st.session_state.prompt_sistema = prompt_sistema

# Configurações na barra lateral
def tab_configuracoes():
    st.sidebar.header("Configurações")
    modelo_escolhido = st.sidebar.selectbox('Selecione o modelo', ['gpt-3.5-turbo', 'gpt-4'])
    st.session_state.modelo = modelo_escolhido

    api_key_input = st.sidebar.text_input(
        "Insira sua chave da OpenAI API:",
        type="password",
        placeholder="sk-...",
        help="Você pode obter sua chave de API em https://platform.openai.com/account/api-keys."
    )
    if api_key_input != st.session_state.api_key:
        st.session_state.api_key = api_key_input
        st.session_state.cliente = OpenAI(api_key=st.session_state.api_key)
        st.sidebar.success('Chave da API atualizada com sucesso!')

# Tab para gerenciar conversas
def tab_conversas():
    st.sidebar.markdown("## Conversas")
    if st.sidebar.button('➕ Nova conversa', use_container_width=True):
        st.session_state.mensagens = [{"role": "system", "content": st.session_state.prompt_sistema}]
        st.session_state.conversa_atual = ''
        # Não chamamos st.experimental_rerun()

    conversas = listar_conversas()
    for nome_conversa in conversas:
        if st.sidebar.button(nome_conversa, key=nome_conversa, use_container_width=True):
            st.session_state.mensagens = carregar_conversa(nome_conversa)
            st.session_state.conversa_atual = nome_conversa
            # Não chamamos st.experimental_rerun()

# Página principal do chatbot
def pagina_principal():
    st.title("Eva Medical Chatbot 💊")
    st.markdown("""
    Eva é um chatbot médico que fornece diagnósticos e condutas sugeridas com base nos casos clínicos fornecidos.
    """)
    if not st.session_state.api_key:
        st.warning("Por favor, insira sua chave da OpenAI API na aba de configurações.")
        return
    if st.session_state.mensagens == []:
        # Inicia a conversa com o prompt do sistema
        st.session_state.mensagens = [{"role": "system", "content": st.session_state.prompt_sistema}]
    # Exibe o histórico de mensagens
    for msg in st.session_state.mensagens[1:]:
        if msg['role'] == 'user':
            st.chat_message("user").markdown(msg['content'])
        elif msg['role'] == 'assistant':
            st.chat_message("assistant").markdown(msg['content'])

    # Campo de entrada do usuário
    prompt = st.chat_input('Digite sua mensagem')
    if prompt:
        # Adiciona a mensagem do usuário
        st.session_state.mensagens.append({"role": "user", "content": prompt})
        st.chat_message("user").markdown(prompt)
        # Gera a resposta do chatbot
        try:
            resposta = gerar_resposta(st.session_state.cliente, st.session_state.mensagens)
            assistant_message = resposta.choices[0].message.content
            st.session_state.mensagens.append({"role": "assistant", "content": assistant_message})
            st.chat_message("assistant").markdown(assistant_message)
            # Salva a conversa
            if st.session_state.conversa_atual:
                nome_conversa = st.session_state.conversa_atual
            else:
                nome_conversa = prompt[:30].strip()
            salvar_conversa(nome_conversa, st.session_state.mensagens)
            st.session_state.conversa_atual = nome_conversa
        except Exception as e:
            st.error(f"Ocorreu um erro: {e}")

# Main
def main():
    inicializacao()
    tab_configuracoes()
    tab_conversas()
    pagina_principal()

if __name__ == '__main__':
    main()


