import os
import warnings
from langchain_ollama import OllamaLLM
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain_community.document_loaders import PyMuPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
import fitz  # PyMuPDF
from PIL import Image
import pytesseract

# Prolog
import re
import subprocess
from pyswip import Prolog

# Info: 최종수정: 2025-01-03, 수정자: NangManCat
# Note: 해당 코드는 PDF 파일을 OCR(이미지 기반 PDF를 읽는 라이브러리)를 사용하여 읽고 vectorstore을 생성한 다음,
# Note: 사전에 작업한 rule.txt(건강검진 결과에 따른 판단 기준이 작성된 txt파일) 또한 읽고 merge하여 사전 학습을 시킨 다음,
# Note: doc/doc2.pdf 파일을 읽고 그것을 prolog 언어로 바꾸고,
# Note: 바꾸어진 Prolog 언어는 process_prolog_code 함수를 통해 후처리 되어 적합한 Prolog언어로 바뀌어,
# Note: prolog/output.pl로 저장되는 코드입니다.
# Info: 이 코드는 test.py에서 merge 부분을 주석처리하고 rule.txt파일을 사전학습에서 배제시킨 코드이다.

# BUG: OCR된 결과를 Gemma가 제대로 처리하지 못하는 문제가 발생

# Fixme: 이미지 기반 PDF를 읽히는 대신(OCR), 텍스트 기반 파일을 읽히는 것으로 변경


# Prolog 구문 후처리 함수
def process_prolog_code(prolog_code):
    processed_lines = []
    for line in prolog_code.split("\n"):
        line = line.strip()  # 양쪽 공백 제거
        if not line:
            continue  # 빈 줄은 건너뛰기

        # 문자열 감싸기 (숫자는 제외)
        line = re.sub(r"(?<!')([\uAC00-\uD7A3\w]+)(?!')", r"'\1'", line)

        # 콤마 양쪽 공백 제거
        line = re.sub(r"\s*,\s*", ",", line)

        # 문장 끝에 . 추가
        if not line.endswith("."):
            line += "."

        processed_lines.append(line)
    return "\n".join(processed_lines)


# PDF 경로 및 OCR 처리
def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    full_text = ""

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()  # 텍스트 레이어 추출
        if text.strip():
            full_text += text
        else:
            pix = page.get_pixmap()
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            text = pytesseract.image_to_string(img, lang="kor")  # 한국어 OCR
            full_text += text

    return full_text


# # TXT 파일 읽기
# def read_text_file(txt_path):
#     if not os.path.exists(txt_path):
#         raise FileNotFoundError(f"TXT 파일 {txt_path}을 찾을 수 없습니다.")
#     with open(txt_path, "r", encoding="utf-8") as file:
#         return file.read()


# 파일 읽기
pdf_path = "doc/doc2.pdf"
txt_path = "rule/rule.txt"

if not os.path.exists(pdf_path):
    raise FileNotFoundError(f"PDF 파일 {pdf_path}을 찾을 수 없습니다.")

# if not os.path.exists(txt_path):
#     raise FileNotFoundError(f"TXT 파일 {txt_path}을 찾을 수 없습니다.")

# PDF와 TXT 읽기
extracted_text = extract_text_from_pdf(pdf_path)
# rule_text = read_text_file(txt_path)

# 텍스트 병합
merged_text = extracted_text
# merged_text = extracted_text + "\n" + rule_text

# 텍스트 분리
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
)
docs = text_splitter.create_documents([merged_text])

# 디버그 로그로 청크 확인
for i, doc in enumerate(docs):
    print(f"Chunk {i+1}:\n{doc.page_content}\n{'-'*40}")

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

# Prompt 템플릿
template = """
You are an AI assistant that specializes in converting health examination results into Prolog facts based on predefined rules. Utilize the provided rules from the file `rule.txt` to generate accurate Prolog facts. Ensure that the numerical values and descriptive text are faithfully represented from the health examination results, aligning them with the rules in `rule.txt`. If specific numerical values are not provided, represent them as `unknown` in the Prolog facts. Avoid assumptions or inferences, and focus strictly on creating valid Prolog facts. The output should contain only Prolog facts and no additional explanation or markdown formatting.

Context:
{context}

Instruction:
Convert the above context into Prolog statements, ensuring accurate representation without adding inferred data. Translate all non-numerical labels or terms into English.

Prolog Code:
"""


prompt = ChatPromptTemplate.from_template(template)


# 문서 포맷 함수
def format_docs(docs):
    return "\n\n".join([d.page_content for d in docs])


# RAG 체인 설정
rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

# 질문 처리
query = "내 건강검진결과서를 prolog어로 바꿔줘"
answer = rag_chain.invoke(query)

# Prolog 코드 후처리
formatted_answer = process_prolog_code(answer)

# 출력 파일 경로 설정
output_dir = "prolog"
output_file = os.path.join(output_dir, "output.pl")

# 폴더가 없으면 생성
os.makedirs(output_dir, exist_ok=True)

# 파일에 저장
with open(output_file, "w", encoding="utf-8") as file:
    file.write(answer)

print(f"Answer saved to {output_file}")

# Prolog 실행
try:
    # Prolog 명령 실행
    prolog_command = f"swipl -s {output_file} -g halt"
    subprocess.run(prolog_command, shell=True, check=True)
    print(f"Prolog file {output_file} consulted successfully.")
except subprocess.CalledProcessError as e:
    print(f"Error occurred while consulting Prolog file: {e}")
