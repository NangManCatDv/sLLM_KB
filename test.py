# 2024.11.17일 첫 생성

# Note: 기본 세팅
import os
import warnings
from langchain_ollama import OllamaLLM

# Note: 실시간 답변 출력
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

# Note: PDF Loader
from langchain_community.document_loaders import PyMuPDFLoader

# Note: TextSplitter
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Note: Text Vector Embedding
from langchain_community.embeddings import HuggingFaceEmbeddings

# Note: VectorStore(Chroma)
from langchain_community.vectorstores import Chroma

# Note: LangChain
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate


loader = PyMuPDFLoader("doc/doc1.pdf")
pages = loader.load()


# INFO: 문서를 문장으로 분리
## INFO: 청크 크기 500, 각 청크의 50자씩 겹치도록 청크를 나눔
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
)
docs = text_splitter.split_documents(pages)


# INFO: 문장을 임베딩으로 변환하고 벡터 저장소에 저장
embeddings = HuggingFaceEmbeddings(
    model_name="BAAI/bge-m3",
    # model_kwargs={'device':'cpu'},
    model_kwargs={"device": "cuda"},
    encode_kwargs={"normalize_embeddings": True},
)

# INFO: 벡터 저장소 생성
vectorstore = Chroma.from_documents(docs, embeddings)

# INFO: 벡터 저장소 경로 설정
## INFO: 현재 경로에 'vectorstore' 경로 생성
vectorstore_path = "vectorstore"
os.makedirs(vectorstore_path, exist_ok=True)

# INFO: 벡터 저장소 생성 및 저장
vectorstore = Chroma.from_documents(
    docs, embeddings, persist_directory=vectorstore_path
)
# INFO: vectorstore 데이터를 디스크에 저장
vectorstore.persist()
print("Vectorstore created and persisted")


# INFO: 모델 설정
llm = OllamaLLM(
    model="gemma2:latest",
    temperature=0,
    callback_manager=CallbackManager([StreamingStdOutCallbackHandler()]),
)

# INFO: Retriever
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})


# INFO: Prompt 템플릿
template = """
Use the following context to answer the question:

Context:
{context}

Question:
{question}

Answer:
"""


prompt = ChatPromptTemplate.from_template(template)


def format_docs(docs):
    return "\n\n".join([d.page_content for d in docs])


# INFO: RAG Chain 연결
rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

# INFO: Chain 실행
query = "내 구강검진 결과에 대해 알려줘"
answer = rag_chain.invoke(query)


print("Query", query)
print("Answer", answer)
