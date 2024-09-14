import streamlit as st
import openai
from dotenv import load_dotenv
import os
import json

# Carrega as variáveis de ambiente
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
modelo = "gpt-4o"

# Carrega o prompt do sistema
from prompt_sistema import prompt_do_sistema
prompt_sistema = prompt_do_sistema

st.set_page_config(page_title="Eva Medical Chatbot", page_icon="💊")

# Função principal para gerar a resposta do chatbot
def gerar_resposta(messages):
    response = openai.chat.completions.create(
        model=modelo,
        messages=messages,
        temperature=1.0,
    )
    return response

# Inicializa a sessão do Streamlit
if 'messages' not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": prompt_sistema}
    ]

if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []

st.title("Eva Medical Chatbot 💊")
st.markdown("""
Eva é um chatbot médico que fornece diagnósticos e condutas sugeridas com base nos casos clínicos fornecidos.
""")

# Exibe o histórico de mensagens
for msg in st.session_state.messages[1:]:
    if msg['role'] == 'user':
        st.markdown(f"**Você:** {msg['content']}")
    elif msg['role'] == 'assistant':
        st.markdown(f"**Eva:** {msg['content']}")

# Campo de entrada do usuário
with st.form(key='chat_form', clear_on_submit=True):
    user_input = st.text_area("Digite o caso clínico ou sua mensagem:", height=100)
    submit_button = st.form_submit_button(label='Enviar')

if submit_button and user_input:
    # Adiciona a mensagem do usuário ao histórico
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Gera a resposta do chatbot
    resposta = gerar_resposta(st.session_state.messages)

    # Adiciona a resposta do assistente ao histórico
    assistant_message = resposta['choices'][0]['message']['content']
    st.session_state.messages.append({"role": "assistant", "content": assistant_message})

    # Atualiza o histórico da conversa para salvar posteriormente
    st.session_state.conversation_history.append({"role": "user", "content": user_input})
    st.session_state.conversation_history.append({"role": "assistant", "content": assistant_message})

    # Exibe a resposta do assistente
    st.markdown(f"**Eva:** {assistant_message}")

# Botão para encerrar a conversa e salvar o histórico
if st.button('Encerrar Conversa'):
    st.write("Conversa encerrada.")

    # Remove o prompt do sistema do histórico
    conversation_history_without_system = [msg for msg in st.session_state.conversation_history if msg['role'] != 'system']

    # Cria o objeto de dados para fine-tuning
    data = {
        "messages": conversation_history_without_system
    }

    # Salva no arquivo JSONL
    with open("fine_tuning_data.jsonl", "a", encoding="utf-8") as f:
        json_line = json.dumps(data, ensure_ascii=False)
        f.write(json_line + "\n")

    # Limpa o estado da sessão
    st.session_state.messages = [
        {"role": "system", "content": prompt_sistema}
    ]
    st.session_state.conversation_history = []
    st.experimental_rerun()
