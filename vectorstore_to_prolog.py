import os
import logging
from langchain_ollama import OllamaLLM
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from konlpy.tag import Komoran

# 로깅 설정
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)

# NLP 분석기 설정
komoran = Komoran()

# OllamaLLM 모델 설정
llm = OllamaLLM(
    model="gemma2:latest",
    temperature=0,
    callback_manager=CallbackManager([StreamingStdOutCallbackHandler()]),
)

# 디버그 폴더 생성
DEBUG_FOLDER = "debug"
os.makedirs(DEBUG_FOLDER, exist_ok=True)


def split_sentences(text):
    """문장을 마침표 기준으로 나누기"""
    sentences = text.replace("\n", " ").split(". ")
    return [s.strip() + "." for s in sentences if s.strip()]


def extract_svo(sentence):
    """
    문장에서 주어(S), 동사(V), 목적어(O) 추출 (구문 분석).

    Args:
        sentence (str): 입력 문장.

    Returns:
        dict: {"주어": 주어, "동사": 동사, "목적어": 목적어} (없으면 None)
    """
    parsed = komoran.pos(sentence)
    subject, verb, obj = None, None, None

    for i, (word, pos) in enumerate(parsed):
        if pos in ["NNG", "NNP"]:  # 일반명사, 고유명사
            if i > 0 and parsed[i - 1][1] in ["JKS", "JKC"]:  # 주격 조사 ('이/가')
                subject = word
            elif i > 0 and parsed[i - 1][1] in ["JKO"]:  # 목적격 조사 ('을/를')
                obj = word
        elif pos in ["VV"]:  # 동사
            verb = word + "다"  # 원형 복원

    if subject and verb and obj:
        return {"주어": subject, "동사": verb, "목적어": obj}
    return None  # SVO가 모두 없으면 None 반환


def save_debug_info(parsed_sentences, parsed_errors):
    """
    구문 분석된 문장과 오류 문장을 debug 폴더에 저장.
    """
    parsed_path = os.path.join(DEBUG_FOLDER, "parsed_sentences.txt")
    errors_path = os.path.join(DEBUG_FOLDER, "parsed_errors.txt")

    with open(parsed_path, "w", encoding="utf-8") as f:
        for entry in parsed_sentences:
            f.write(f"{entry}\n")

    with open(errors_path, "w", encoding="utf-8") as f:
        for error in parsed_errors:
            f.write(f"{error}\n")

    logging.info(f"디버깅 파일 저장 완료: {parsed_path}, {errors_path}")


def convert_text_to_prolog(
    doc_txt_path, system_prompt_path, output_prolog_path="prolog/facts.pl"
):
    logging.info("Prolog 변환 시작...")

    if not os.path.exists(doc_txt_path):
        raise FileNotFoundError(f"텍스트 파일 {doc_txt_path}을 찾을 수 없습니다.")
    if not os.path.exists(system_prompt_path):
        raise FileNotFoundError(
            f"시스템 프롬프트 파일 {system_prompt_path}을 찾을 수 없습니다."
        )

    with open(system_prompt_path, "r", encoding="utf-8") as file:
        system_prompt = file.read().strip()
    logging.info(f"시스템 프롬프트 로드 완료: {system_prompt}")

    with open(doc_txt_path, "r", encoding="utf-8") as file:
        text = file.read()

    sentences = split_sentences(text)

    prolog_facts = []
    parsed_sentences = []
    parsed_errors = []

    for sentence in sentences:
        svo = extract_svo(sentence)
        if not svo:
            logging.warning(f"SVO 추출 실패: {sentence}")
            parsed_errors.append(sentence)
            continue

        logging.debug(f"SVO 분석 결과: {svo}")
        parsed_sentences.append(f"{svo['주어']} {svo['동사']} {svo['목적어']}")

        prompt = f"""{system_prompt}

Convert the following structured sentence into a Prolog fact:
Subject: {svo["주어"]}
Verb: {svo["동사"]}
Object: {svo["목적어"]}

Use the format: fact(subject, verb, object)."""

        try:
            prolog_fact = llm(prompt).strip()
        except Exception as e:
            logging.error(f"OllamaLLM 변환 오류: {e}")
            parsed_errors.append(f"LLM 변환 실패: {sentence}")
            prolog_fact = f"% 변환 실패: {sentence}"

        prolog_facts.append(prolog_fact)

    save_debug_info(parsed_sentences, parsed_errors)

    os.makedirs(os.path.dirname(output_prolog_path), exist_ok=True)

    with open(output_prolog_path, "w", encoding="utf-8") as file:
        file.write(f"% {system_prompt}\n\n")
        for fact in prolog_facts:
            file.write(f"{fact}\n")

    logging.info(f"Prolog 파일 생성 완료: {output_prolog_path}")
    print(f"✅ Prolog 파일이 생성되었습니다: {output_prolog_path}")
