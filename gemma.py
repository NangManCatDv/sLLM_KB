# from langchain_community.chat_models import ChatOllama
from langchain_community.llms import Ollama

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
import sys
import logging

logging.getLogger("langchain").setLevel(logging.ERROR)

# to help the CLI write unicode characters to the terminal
sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf8", buffering=1)

# 세션 기록을 관리할 변수 (직접 관리)
session_store = {}


# 세션 기록을 가져오는 함수
def get_session_history(session_id: str):
    if session_id not in session_store:
        session_store[session_id] = ChatMessageHistory()
    return session_store[session_id]


# 파일에서 프롬프트 읽기
def load_prompt_from_file(file_path="prompt.txt"):
    with open(file_path, "r", encoding="utf8") as f:
        return f.read()


# response를 생성하는 함수
def generate_response(user_input: str, session_id: str):
    llm = Ollama(model="gemma2:latest", temperature=1)

    # 프롬프트 파일에서 불러오기
    system_prompt = load_prompt_from_file()

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{question}"),
        ]
    )

    chain = prompt | llm

    chain_with_memory = RunnableWithMessageHistory(
        chain,
        get_session_history,
        input_messages_key="question",
        history_messages_key="history",
    )

    response = chain_with_memory.invoke(
        {"question": user_input},
        config={"configurable": {"session_id": session_id}},
    )

    # 세션 기록 디버깅 출력
    # print(f"After: {session_store}\n")

    return response  # 여기서 .content를 제거하고 response 그대로 반환


def chat():
    print("メガミ: hello!")
    session_id = "unique_session_id"
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["종료", "exit", "quit"]:
            print("メガミ: 안녕히 가세요!")
            break

        response = generate_response(user_input, session_id)
        print(f"メガミ: {response}")


if __name__ == "__main__":
    chat()
