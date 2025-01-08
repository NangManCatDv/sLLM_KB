import os
import logging
from langchain_ollama import OllamaLLM
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler


# OllamaLLM 모델 설정
llm = OllamaLLM(
    model="gemma2:latest",
    temperature=0,
    callback_manager=CallbackManager([StreamingStdOutCallbackHandler()]),
)


def convert_vectorstore_to_prolog(vectorstore_path, doc_txt_path, system_prompt_path):
    """
    벡터 저장소와 텍스트 파일 내용을 Prolog 형식으로 변환하여 prolog/facts.pl에 저장.
    OllamaLLM 모델을 사용하여 변환 작업 수행.

    Args:
        vectorstore_path (str): 벡터 저장소 디렉토리 경로.
        doc_txt_path (str): 입력 텍스트 파일 경로.
        system_prompt_path (str): 시스템 프롬프트 텍스트 파일 경로.

    Returns:
        None
    """
    logging.debug("Prolog 변환 시작...")

    # 경로 확인
    if not os.path.exists(vectorstore_path):
        raise FileNotFoundError(f"벡터 저장소 {vectorstore_path}을 찾을 수 없습니다.")
    if not os.path.exists(doc_txt_path):
        raise FileNotFoundError(f"텍스트 파일 {doc_txt_path}을 찾을 수 없습니다.")
    if not os.path.exists(system_prompt_path):
        raise FileNotFoundError(
            f"시스템 프롬프트 파일 {system_prompt_path}을 찾을 수 없습니다."
        )

    # 시스템 프롬프트 읽기
    with open(system_prompt_path, "r", encoding="utf-8") as file:
        system_prompt = file.read().strip()
    logging.debug(f"시스템 프롬프트 로드 완료: {system_prompt}")

    # doc.txt 파일 읽기
    with open(doc_txt_path, "r", encoding="utf-8") as file:
        doc_lines = file.readlines()

    # 텍스트를 Prolog 형식으로 변환 (OllamaLLM 사용)
    prolog_facts = []
    for line in doc_lines:
        line = line.strip()
        if line:  # 빈 줄 건너뜀
            # OllamaLLM을 사용하여 Prolog 형식으로 변환
            prompt = f"{system_prompt}\n\nConvert the following text to a Prolog fact:\n\n{line}"
            fact = llm(prompt).strip()
            prolog_facts.append(fact)

    # Prolog 파일 저장 경로 설정
    output_prolog_path = "prolog/facts.pl"
    os.makedirs(os.path.dirname(output_prolog_path), exist_ok=True)

    # Prolog 파일 쓰기
    with open(output_prolog_path, "w", encoding="utf-8") as file:
        # 시스템 프롬프트를 주석으로 추가
        file.write(f"% {system_prompt}\n\n")
        for fact in prolog_facts:
            file.write(f"{fact}\n")

    logging.debug(f"Prolog 파일 생성 완료: {output_prolog_path}")
    print(f"Prolog 파일이 생성되었습니다: {output_prolog_path}")
