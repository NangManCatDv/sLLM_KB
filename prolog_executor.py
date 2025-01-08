import logging
import os
import subprocess
from langchain_ollama import OllamaLLM
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

# 모델 설정
llm = OllamaLLM(
    model="gemma2:latest",
    temperature=0,
    callback_manager=CallbackManager([StreamingStdOutCallbackHandler()]),
)


def natural_language_to_prolog_query(natural_language_query: str) -> str:
    """
    사용자의 자연어 질의를 Prolog 쿼리로 변환합니다.
    """
    prompt = (
        "Convert the following natural language query to a Prolog query:\n\n"
        f"Natural Language: {natural_language_query}\n"
        "Prolog Query:"
    )
    response = llm(prompt)
    return response.strip()


def execute_prolog_query(facts_path: str, prolog_query: str) -> str:
    """
    Prolog 파일에 쿼리를 실행하고 결과를 반환합니다.
    """
    absolute_facts_path = os.path.abspath(facts_path).replace("\\", "/")

    # Prolog 파일 존재 확인
    if not os.path.exists(facts_path):
        logging.error(f"Prolog facts file '{facts_path}' not found.")
        return "Facts file not found."

    try:
        # Prolog 실행 명령어 생성
        command = f'swipl -s {absolute_facts_path} -g "{prolog_query}, halt."'
        logging.debug(f"Executing Prolog command: {command}")

        # subprocess로 Prolog 실행
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        # 실행 결과 가져오기
        stdout, stderr = process.communicate()

        if stderr:
            logging.error(f"Prolog Error: {stderr.strip()}")
            return f"Prolog Error: {stderr.strip()}"

        return stdout.strip() if stdout else "No results found."

    except Exception as e:
        logging.error(f"Error executing Prolog query: {e}")
        return f"Error: {e}"


def main():
    logging.basicConfig(level=logging.DEBUG)

    # facts2.pl 경로 설정
    facts_path = "prolog/facts2.pl"  # Prolog facts 파일 경로

    # 사용자 입력 받기
    natural_language_query = input("Enter your query in natural language: ")

    # 자연어 질의를 Prolog 쿼리로 변환
    prolog_query = natural_language_to_prolog_query(natural_language_query)
    print(f"Prolog Query: {prolog_query}")

    # Prolog 쿼리 실행 및 결과 출력
    result = execute_prolog_query(facts_path, prolog_query)
    print("\nQuery Results:")
    print(result)


if __name__ == "__main__":
    main()
