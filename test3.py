import os
from langchain_community.document_loaders import PyMuPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_ollama import OllamaLLM
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler


# Info: 최종수정: 2025-01-05, 수정자: NangManCat
# Note: 해당 코드는 PDF 파일을 PyPDF(PDF를 읽는 라이브러리)를 사용하여 읽고 vectorstore을 생성한 다음,
# Note: 그 verctorstore에 기반해 질의응답을 하는 코드입니다.

# BUG: PDF에 관한 질문이 아님에도 PDF에 대해 대답하는 문제

# Note: 이 코드는 이순신 위키백과 PDF를 Prolog로 바꾸고자 사용한 코드다. 사용한 프롬프트는 아래와 같다.
# 이순신에 대한 Prolog 코드를 작성해주세요. 다음 조건을 반드시 충족해야 합니다:

# 1. **문법적으로 올바른 Prolog 코드**를 작성하세요.
#    - 모든 predicate는 끝에 마침표(`.`)를 추가하세요.
#    - 공백이나 특수 문자가 포함된 문자열은 반드시 작은따옴표(`'`)로 감싸세요.
#      - 중첩된 따옴표(예: `"'텍스트'"`)는 절대 사용하지 마세요.
#      - 모든 문자열은 단일 작은따옴표(`'`)로 감싸야 합니다. (예: `'이순신 장군의 활약'`)

# 2. 다음 정보를 포함하세요:
#    - **기본 정보**:
#      - 이순신의 이름, 생년, 사망년을 predicate로 작성하세요.
#      - 각 정보는 개별 predicate로 구분하세요. (예: `이름('이순신').`)
#    - **주요 업적**:
#      - 업적을 리스트 형식으로 작성하되, 최소 5개 이상의 세부 업적을 포함하세요.
#    - **특이 사항**:
#      - 특이 사항을 리스트 형식으로 작성하되, 최소 3개 이상의 항목을 포함하세요.
#    - **각 전투에 대한 요약 정보 (`전투요약`)**:
#      - 전투 이름, 연도, 요약, 결과를 포함한 predicate를 작성하세요.
#      - 요약 내용은 공백과 특수 문자가 포함될 수 있으므로 반드시 작은따옴표(`'`)로 감싸세요.
#      - 전투는 최소 5개 이상 포함하세요.
#    - **전투 지휘 관계**:
#      - 이순신과 각 전투의 관계를 나타내는 predicate를 작성하세요.
#    - **전투 결과**:
#      - 각 전투의 결과('승리' 또는 '패배')를 명시하세요.
#    - **연도별 주요 사건**:
#      - 연도와 사건을 연결하는 predicate를 작성하되, 최소 5개의 주요 사건을 포함하세요.
#    - **생애와 업적 요약**:
#      - 이순신의 생애와 업적을 요약한 내용을 리스트 형식으로 작성하세요.

# 3. **구문 및 형식 규칙**:
#    - Prolog에서 문자열은 항상 작은따옴표(`'`)로 감싸세요.
#    - predicate 이름과 데이터 구조를 일관되게 작성하세요.
#    - 리스트는 대괄호(`[]`)로 감싸고, 원소는 콤마(`,`)로 구분하세요.
#    - 모든 predicate는 끝에 마침표(`.`)를 추가하세요.

# 4. **가독성 강화**:
#    - 각 섹션의 시작에 주석(`%`)을 추가하세요.
#    - predicate와 predicate 사이에 빈 줄을 추가하여 가독성을 높이세요.

# 5. **요청의 목적**:
#    - 이 코드는 교육 자료로 사용될 것이므로, 정확성과 세부 사항을 중시해주세요.
#    - Prolog 구문 오류가 발생하지 않도록 작성하세요.
#    - 중첩된 따옴표를 사용하는 코드는 절대 생성하지 마세요.


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
print("Vectorstore created and persisted.")

# 모델 설정
llm = OllamaLLM(
    model="gemma2:latest",
    temperature=0,
    callback_manager=CallbackManager([StreamingStdOutCallbackHandler()]),
)

# 검색기 초기화
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})


# 문서 포맷 함수
def format_docs(docs):
    return "\n\n".join([d.page_content for d in docs])


# RAG 체인 설정
def get_answer(query):
    context_docs = retriever.invoke(query)
    formatted_context = format_docs(context_docs)
    input_data = f"Context:\n{formatted_context}\n\nQuestion:\n{query}"
    return llm.invoke(input_data)


# 질문 처리
while True:
    query = input("\n질문을 입력하세요 (종료하려면 'exit' 입력): ")
    if query.lower() == "exit":
        print("프로그램을 종료합니다.")
        break
    answer = get_answer(query)
