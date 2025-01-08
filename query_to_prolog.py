import logging
import os
from pyswip import Prolog
from langchain_ollama import OllamaLLM
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

# 로깅 설정
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)

# OllamaLLM 모델 설정
llm = OllamaLLM(
    model="gemma2:latest",
    temperature=0,
    callback_manager=CallbackManager([StreamingStdOutCallbackHandler()]),
)


def convert_question_to_prolog_llm(question: str, prolog_path: str = "rules.pl") -> str:
    """
    OllamaLLM을 사용하여 사용자의 자연어 질문을 Prolog 쿼리로 변환하고 실행 결과를 반환합니다.
    생성된 Prolog 쿼리를 prolog/query.pl에 저장합니다.

    Args:
        question (str): 사용자의 자연어 질문
        prolog_path (str): Prolog 규칙이 정의된 파일 경로 (기본값: "rules.pl")

    Returns:
        str: Prolog 쿼리 실행 결과 또는 에러 메시지
    """
    logging.debug("Initializing Prolog engine.")
    prolog = Prolog()

    try:
        # Prolog 파일 로드
        logging.debug(f"Loading Prolog file: {prolog_path}")
        prolog.consult(prolog_path)
        logging.info(f"Prolog file '{prolog_path}' loaded successfully.")
    except Exception as e:
        logging.error(f"Error loading Prolog file: {e}")
        return f"Error loading Prolog file: {e}"

    # OllamaLLM을 사용하여 질문 -> Prolog 쿼리 변환
    logging.debug(f"Converting question to Prolog query using LLM: {question}")
    system_prompt = (
        "You are an expert in Prolog. Convert natural language questions into Prolog queries. "
        "Focus on queries related to family relationships such as siblings, parents, and grandparents."
    )
    prompt = (
        f"{system_prompt}\n\nQuestion: {question}\n\nConvert this to a Prolog query:"
    )
    try:
        prolog_query = llm(prompt).strip()
        logging.debug(f"Generated Prolog query: {prolog_query}")
    except Exception as e:
        logging.error(f"Error generating Prolog query with LLM: {e}")
        return f"Error generating Prolog query with LLM: {e}"

    # Prolog 쿼리를 파일로 저장
    output_prolog_path = "prolog/query.pl"
    os.makedirs(os.path.dirname(output_prolog_path), exist_ok=True)  # 디렉토리 생성
    try:
        with open(output_prolog_path, "w", encoding="utf-8") as file:
            file.write(f"% Generated Prolog Query\n")
            file.write(f"{prolog_query}\n")
        logging.info(f"Prolog query saved to {output_prolog_path}")
    except Exception as e:
        logging.error(f"Error saving Prolog query to file: {e}")
        return f"Error saving Prolog query to file: {e}"

    # Prolog 쿼리 실행
    try:
        logging.debug(f"Executing Prolog query: {prolog_query}")
        results = list(prolog.query(prolog_query))
        if not results:
            logging.info("No results found for the query.")
            return "No results found for the query."
        logging.info(f"Query executed successfully. Results: {results}")
        return results
    except Exception as e:
        logging.error(f"Error executing Prolog query: {e}")
        return f"Error executing Prolog query: {e}"
