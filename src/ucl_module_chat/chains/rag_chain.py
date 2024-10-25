from pathlib import Path

from dotenv import load_dotenv
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_community.vectorstores import FAISS
from langchain_core.embeddings.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

load_dotenv()

context_prompt = """Given a chat history and the latest user question
        which might reference context in the chat history,
        formulate a standalone question which can be understood
        without the chat history. Do NOT answer the question,
        just reformulate it if needed and otherwise return it as is."""

rag_prompt = """You are an assistant for question-answering tasks related
        to university courses (modules) at Univeristy College London (UCL).
        Use the following pieces of retrieved context to answer the question.
        The context is from entires in the UCL module catalogue,
        which is available publicly on the internet. 
        The first time you refer to a module in the conversation, refer to
        it by it's full name followed by the module code in brackets, e.g.
        Supervised Learning (COMP0078).
        If you don't know the answer, apologise, say that
        you don't know the answer, and suggest that the user
        manually reviews the UCL website and module catalogue.
        Use five sentences maximum and keep the answer concise. 
        Use professional British English and avoid using slang.
        Do not refer to the context directly in your answer, but you
        should use it to answer the question. 
        You can ask the user if they would like to know more about a 
        specific area if you think it may be helpful.
        \n\n
        {context}"""


def build_rag_chain(
    llm: BaseChatModel,
    embedding_model: Embeddings,
    vectorstore_dir: str | Path,
    context_system_prompt: str = context_prompt,
    rag_system_prompt: str = rag_prompt,
):
    """Build a RAG chain for the UCL module chatbot."""

    contextualize_q_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", context_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )
    vectorstore = FAISS.load_local(
        vectorstore_dir,
        embeddings=embedding_model,
        allow_dangerous_deserialization=True,
    )
    retriever = vectorstore.as_retriever()

    history_aware_retriever = create_history_aware_retriever(
        llm, retriever, contextualize_q_prompt
    )

    qa_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", rag_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )

    # Stuff documents chain combines documents from retreiver | qa_prompt
    # | llm | StrOutputParser
    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt).with_config(
        tags=["qa"]
    )

    # Full rag chain is history aware retriever | question answer chain
    rag_chain = create_retrieval_chain(
        history_aware_retriever, question_answer_chain
    ).with_config(tags=["rag"])

    return rag_chain
