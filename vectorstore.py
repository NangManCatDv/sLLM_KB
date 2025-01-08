import logging
import os
from langchain_community.document_loaders import PyMuPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

# 로깅 설정
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)


def vectorstore_main():
    logging.debug("vectorstore 확인 중...")

    # PDF 경로
    pdf_path = "doc/doc2.pdf"
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF 파일 {pdf_path}을 찾을 수 없습니다.")

    # PDF 로드 및 텍스트 추출
    loader = PyMuPDFLoader(pdf_path)
    documents = loader.load()

    # 텍스트 분리
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
    )
    docs = text_splitter.split_documents(documents)

    # 임베딩 생성
    embeddings = HuggingFaceEmbeddings(
        model_name="BAAI/bge-m3",
        model_kwargs={"device": "cuda"},
        encode_kwargs={"normalize_embeddings": True},
    )

    # 벡터 저장소 초기화 및 저장
    vectorstore_path = "vectorstore"
    os.makedirs(vectorstore_path, exist_ok=True)
    vectorstore = Chroma.from_documents(
        docs, embeddings, persist_directory=vectorstore_path
    )
    vectorstore.persist()
    print("vectorstore 생성 및 유지 중...")
