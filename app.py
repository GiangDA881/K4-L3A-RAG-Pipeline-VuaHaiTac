import streamlit as st
from dotenv import load_dotenv

from src.task10_generation import generate_with_citation


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
        if message["role"] == "assistant" and message.get("sources"):
            st.caption(f"Retrieval: {message.get('retrieval_source', 'unknown')}")
            with st.expander("Nguồn đã sử dụng"):
                for index, source in enumerate(message["sources"], 1):
                    metadata = source.get("metadata", {})
                    label = metadata.get("url") or metadata.get("source", "Không rõ nguồn")
                    st.markdown(
                        f"**[{source.get('id', index)}] {metadata.get('title', 'Không có tiêu đề')}**  \n"
                        f"Nguồn: `{label}`  \n"
                        f"Score: `{float(source.get('score', 0.0)):.4f}`"
                    )

query = st.chat_input("Nhập câu hỏi...")

if query:
    st.session_state.messages.append({"role": "user", "content": query})

    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
        result = generate_with_citation(query, top_k)
        answer = result["answer"]
        sources = result["sources"]
        retrieval_source = result["retrieval_source"]
        st.markdown(answer)
        if sources:
            st.caption(f"Retrieval: {retrieval_source}")
            with st.expander("Nguồn đã sử dụng"):
                for index, source in enumerate(sources, 1):
                    metadata = source.get("metadata", {})
                    label = metadata.get("url") or metadata.get("source", "Không rõ nguồn")
                    st.markdown(
                        f"**[{source.get('id', index)}] {metadata.get('title', 'Không có tiêu đề')}**  \n"
                        f"Nguồn: `{label}`  \n"
                        f"Score: `{float(source.get('score', 0.0)):.4f}`"
                    )

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "sources": sources,
        "retrieval_source": retrieval_source,
    })
