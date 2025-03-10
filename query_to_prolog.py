from langchain_ollama import OllamaLLM
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

# 모델 설정
llm = OllamaLLM(
    model="deepseek-r1:14b",
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
