from konlpy.tag import Komoran
import pandas as pd

komoran = Komoran()

text = """
이순신은 조선 중기의 무신이다. 본관은 덕수, 자는 여해, 시호는 충무이며 한성 출신이다.
"""

# 형태소 분석 및 품사 태깅
pos_result = komoran.pos(text)

parsed = {"subject": [], "object": [], "verb": [], "postposition": [], "nouns": []}

current_noun = None
last_verb = None

for word, pos in pos_result:
    if pos in ["NNG", "NNP"]:  # 일반명사, 고유명사
        current_noun = word
        parsed["nouns"].append(word)
    elif pos == "JKS":  # 주격 조사 (ex: 이/가)
        if current_noun:
            parsed["subject"].append(current_noun)
            current_noun = None
        parsed["postposition"].append(word)
    elif pos == "JKO":  # 목적격 조사 (ex: 을/를)
        if current_noun:
            parsed["object"].append(current_noun)
            current_noun = None
        parsed["postposition"].append(word)
    elif pos in ["VV", "VA", "VCP", "VCN"]:  # 동사, 형용사, 서술격 조사
        last_verb = word
        parsed["verb"].append(word)
    elif pos.startswith("J"):  # 기타 조사
        parsed["postposition"].append(word)

# 데이터프레임 변환
df = pd.DataFrame({key: pd.Series(value) for key, value in parsed.items()})

print(df)
