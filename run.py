from vectorstore import vectorstore_main
from vectorstore_to_prolog import convert_text_to_prolog
from vectorstore_to_NEO import convert_vectorstore_to_NEO
from query_to_prolog import convert_question_to_prolog_llm
from prolog_executor import natural_language_to_prolog_query, execute_prolog_query

import logging

# 로깅 설정
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)


# Info: 최종수정: 2025-01-05, 수정자: NangManCat
# Note: 해당 코드는 Prolog와의 상호작용을 통해 자연어 질문을 처리하고 결과를 반환하는 코드입니다.
# Note: 입력된 자연어 질문을 Prolog 쿼리로 변환하여 "rules.pl"에 정의된 규칙 기반으로 질의응답을 수행합니다.

# Vectorstore 실행
vectorstore_main()  # vectorstore.py의 주요 작업 실행

# vectorestore를 prolog 언어로 변경(convert_vectorstore_to_NEO 사용시 비활성화 할 것)
convert_text_to_prolog(
    # vectorstore_path="vectorstore",  # 벡터 저장소 디렉토리
    doc_txt_path="doc/doc.txt",  # doc.txt 파일 경로
    system_prompt_path="system_prompt1.txt",  # system_prompt1.txt 파일 경로
)

# # vectorstore를 NEO 언어로 변경(convert_vectorstore_to_NEO 사용시 비활성화 할 것)
# convert_vectorstore_to_NEO(
#     vectorstore_path="vectorstore",  # 벡터 저장소 디렉토리
#     doc_txt_path="doc/doc.txt",  # doc.txt 파일 경로
#     system_prompt_path="system_prompt2.txt",  # system_prompt2.txt 파일 경로
# )


if __name__ == "__main__":
    try:
        # 사용자 질문 입력
        user_question = input("Enter your question: ")

        # Prolog facts 파일 경로 설정
        facts_path = "prolog/facts2.pl"

        # 자연어를 Prolog 쿼리로 변환
        prolog_query = natural_language_to_prolog_query(user_question)
        print(f"Prolog Query: {prolog_query}")

        # Prolog 쿼리 실행 및 결과 출력
        result = execute_prolog_query(facts_path, prolog_query)
        print("\nQuery Results:")
        print(result)

    except Exception as e:
        logging.error(f"Error occurred: {e}")
