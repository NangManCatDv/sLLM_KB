from pyswip import Prolog

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
