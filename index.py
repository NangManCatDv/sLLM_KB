from pyswip import Prolog

# Prolog 인스턴스 생성
prolog = Prolog()

# Prolog에 기본 사실과 규칙 추가
prolog.assertz("parent(john, mary)")
prolog.assertz("parent(john, sam)")
prolog.assertz("parent(mary, anna)")
prolog.assertz("parent(sam, tom)")

# 가족 관계 규칙 정의
prolog.assertz("sibling(X, Y) :- parent(Z, X), parent(Z, Y), X \= Y")
prolog.assertz("grandparent(X, Y) :- parent(X, Z), parent(Z, Y)")


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
        # 형제 관계 질문 처리
        person = question.split(" ")[-1].strip("?")
        return f"sibling(X, {person})"

    elif "grandparent" in question:
        # 조부모 관계 질문 처리
        person = question.split(" ")[-1].strip("?")
        return f"grandparent(X, {person})"

    elif "parent" in question:
        # 부모 관계 질문 처리
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
