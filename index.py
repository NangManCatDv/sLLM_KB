from pyswip import Prolog


# Info: 최종수정: 2025-01-05, 수정자: NangManCat
# Note: 해당 코드는 Prolog와의 상호작용을 통해 자연어 질문을 처리하고 결과를 반환하는 코드입니다.
# Note: 입력된 자연어 질문을 Prolog 쿼리로 변환하여 "rules.pl"에 정의된 규칙 기반으로 질의응답을 수행합니다.

# BUG: 특정 질문이 Prolog에서 처리되지 않고 None으로 반환되는 경우 발생

# Note: 이 코드는 가족 관계 규칙이 정의된 Prolog 파일(rules.pl)을 로드하여,
# Note: 형제/자매, 부모, 조부모 관계를 묻는 자연어 질문에 답변하기 위해 작성되었습니다.

# Prolog 인스턴스 생성
prolog = Prolog()

# Prolog 규칙 파일 로드
prolog.consult("rules.pl")


# Prolog와의 상호작용 함수
def ask_prolog(query):
    """Prolog 쿼리를 수행하고 결과를 반환하는 함수."""
    result = list(prolog.query(query))
    if result:
        return result
    else:
        return "No result found"


# 자연어 질문을 Prolog 쿼리로 변환하는 함수
def process_question(question):
    """질문을 Prolog 쿼리로 변환하는 함수."""
    question = question.lower()

    if "siblings" in question:
        person = question.split(" ")[-1].strip("?")
        return f"sibling(X, {person})"

    elif "grandparent" in question:
        person = question.split(" ")[-1].strip("?")
        return f"grandparent(X, {person})"

    elif "parent" in question:
        person = question.split(" ")[-1].strip("?")
        return f"parent(X, {person})"

    else:
        return None


# 질문과 응답 예제
def main():
    questions = [
        "Who are the siblings of Mary?",
        "Who is the grandparent of Anna?",
        "Who is the parent of Tom?",
    ]

    for question in questions:
        prolog_query = process_question(question)
        if prolog_query:
            result = ask_prolog(prolog_query)
            if isinstance(result, list) and result:
                answer = ", ".join([res["X"] for res in result])
                print(f"{question} => {answer}")
            else:
                print(f"{question} => No result found")
        else:
            print(f"{question} => Unable to process question")


# 실행
if __name__ == "__main__":
    main()
