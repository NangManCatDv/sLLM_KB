import stanza
import pandas as pd
import os
import re

# Stanza 한국어 모델 다운로드
stanza.download("ko")

# Stanza NLP 파이프라인 로드
nlp = stanza.Pipeline(lang="ko", processors="tokenize,pos,lemma,depparse")

# 텍스트 파일 로드
file_path = "doc/doc.txt"
with open(file_path, "r", encoding="utf-8") as file:
    text = file.read()

# NLP 분석 실행
doc = nlp(text)

# 주어 자동 보정 기능 개선
last_subject = ""  # 주어가 없는 경우 이전 문장의 주어를 참조

structured_data = []
for sentence in doc.sentences:
    subj, verb, obj = "", "", ""

    for word in sentence.words:
        # 올바른 주어만 선택 (첫 번째 명사나 고유명사를 자동으로 주어로 설정)
        if not subj and word.upos in ["NOUN", "PROPN"]:
            subj = word.text
            last_subject = subj  # 주어가 있으면 업데이트
        elif word.deprel == "root":  # 서술어
            verb = word.text
        elif word.deprel in ["obj", "iobj"]:  # 목적어
            obj = word.text

    # 주어가 없는 경우, 이전 문장의 주어를 사용
    if subj == "":
        subj = last_subject

    # 서술어 보정: "이르다", "되었다" 같은 단순 표현을 문맥 기반 변환
    if verb in ["이르다", "되었다"]:
        verb = "임명되었다" if "관직" in obj else "발생했다" if "사건" in obj else verb

    # 목적어 보정: 지나치게 "없음"이 많다면, 문맥에서 유의미한 단어를 선택
    if obj == "없음":
        obj = "알 수 없음"  # 예외 처리를 위한 기본 값 설정

    # 빈 괄호 정리
    cleaned_sentence = re.sub(
        r"\(\s*\)", "", " ".join([w.text for w in sentence.words])
    )

    # 여러 개의 공백 정리
    cleaned_sentence = re.sub(r"\s+", " ", cleaned_sentence)

    # 쉼표, 마침표 정리
    cleaned_sentence = re.sub(r"\s*,\s*", ", ", cleaned_sentence)
    cleaned_sentence = re.sub(r"\s*\.\s*", ". ", cleaned_sentence)

    structured_data.append(
        {
            "주어": subj if subj else "없음",
            "서술어": verb if verb else "없음",
            "목적어": obj if obj else "없음",
            "원본 문장": cleaned_sentence,
        }
    )

# 데이터프레임 생성
df_corrected = pd.DataFrame(structured_data)

# NaN 값이 생기지 않도록 처리
df_corrected.fillna("", inplace=True)

# 디버그 폴더 생성
debug_folder = "debug"
if not os.path.exists(debug_folder):
    os.makedirs(debug_folder)

# 보정된 CSV 파일 저장
corrected_csv_path = os.path.join(
    debug_folder, "structured_data_final_corrected_v2.csv"
)
df_corrected.to_csv(corrected_csv_path, index=False, encoding="utf-8")

print(f"최종적으로 개선된 구문 분석 결과가 저장되었습니다: {corrected_csv_path}")
