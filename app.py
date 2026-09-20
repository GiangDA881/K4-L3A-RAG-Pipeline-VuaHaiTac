import streamlit as st
from dotenv import load_dotenv


load_dotenv()

st.set_page_config(
    page_title="RAG Chatbot",
    page_icon="",
    layout="wide",
)

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.title("RAG Chatbot")
    st.caption("Du lịch Việt Nam: lịch trình, địa điểm, ẩm thực, quy định địa phương")
    top_k = st.slider("Số chunks", 3, 10, 5)

st.title("RAG Chatbot — Du lịch Việt Nam")
st.caption("Hỏi về lịch trình, địa điểm, ẩm thực hoặc quy định du lịch. Câu trả lời phải bám nguồn đã thu thập.")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        # TODO: Hiển thị sources và retrieval score.

query = st.chat_input("Nhập câu hỏi...")

if query:
    st.session_state.messages.append({"role": "user", "content": query})

    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
        # TODO: Gọi generate_with_citation(query, top_k).
        answer = "TODO: Itegration RAG Pipeline hêre"
        sources = []
        st.markdown(answer)

        # TODO: Hiển thị sources và citation.

    # TODO: Lưu answer và sources vào session state.
