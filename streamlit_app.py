import streamlit as st
from openai import OpenAI
import json

# Configuração da página do Streamlit
st.set_page_config(page_title="Eva Medical Chatbot", page_icon="💊")

# Carrega o prompt do sistema
from prompt_sistema import prompt_do_sistema
prompt_sistema = prompt_do_sistema

# Título e descrição
st.title("Eva Medical Chatbot 💊")
st.markdown("""
Eva é um chatbot médico que fornece diagnósticos e condutas sugeridas com base nos casos clínicos fornecidos.
""")

# Função principal para gerar a resposta do chatbot
def gerar_resposta(cliente, messages):
    response = cliente.chat.completions.create(
        model=modelo,
        messages=messages,
        temperature=1.0,
    )
    return response

# Inicializa a sessão do Streamlit
if 'api_key' not in st.session_state:
    st.session_state.api_key = ''

if 'messages' not in st.session_state:
    # Inclui o prompt do sistema nas mensagens
    st.session_state.messages = [
        {"role": "system", "content": prompt_sistema}
    ]

if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []

# Campo para inserção da chave da API
st.sidebar.header("Configurações")
api_key_input = st.sidebar.text_input(
    "Insira sua chave da OpenAI API:",
    type="password",
    placeholder="sk-...",
    help="Você pode obter sua chave de API em https://platform.openai.com/account/api-keys."
)

if api_key_input:
    st.session_state.api_key = api_key_input
    # Inicializa o cliente com a chave de API fornecida
    cliente = OpenAI(api_key=st.session_state.api_key)
    modelo = "gpt-4"

    # Campo de entrada do usuário
    with st.form(key='chat_form', clear_on_submit=True):
        user_input = st.text_area("Digite o caso clínico ou sua mensagem:", height=100)
        submit_button = st.form_submit_button(label='Enviar')

    if submit_button and user_input:
        # Adiciona a mensagem do usuário ao histórico
        st.session_state.messages.append({"role": "user", "content": user_input})
        st.session_state.conversation_history.append({"role": "user", "content": user_input})

        # Gera a resposta do chatbot
        try:
            resposta = gerar_resposta(cliente, st.session_state.messages)

            # Adiciona a resposta do assistente ao histórico
            assistant_message = resposta.choices[0].message.content
            st.session_state.messages.append({"role": "assistant", "content": assistant_message})
            st.session_state.conversation_history.append({"role": "assistant", "content": assistant_message})

            # Exibe a resposta do assistente
            st.markdown(f"**Eva:** {assistant_message}")
        except Exception as e:
            st.error(f"Ocorreu um erro: {e}")

    # Exibe o histórico de mensagens
    if st.session_state.messages:
        for msg in st.session_state.messages[1:]:
            if msg['role'] == 'user':
                st.markdown(f"**Você:** {msg['content']}")
            elif msg['role'] == 'assistant':
                st.markdown(f"**Eva:** {msg['content']}")

    # Botão para encerrar a conversa e salvar o histórico
    if st.button('Encerrar Conversa'):
        st.write("Conversa encerrada.")

        # Remove o prompt do sistema do histórico ao salvar
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
else:
    st.warning("Por favor, insira sua chave da OpenAI API na barra lateral.")


