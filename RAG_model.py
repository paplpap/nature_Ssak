from langchain_community.chat_models import ChatOpenAI
from langchain_community.embeddings import OpenAIEmbeddings
from langchain.prompts import PromptTemplate
from langchain.chains.question_answering import load_qa_chain
from langchain.vectorstores import FAISS
from dotenv import load_dotenv
from api_nature import extract_seoul_district

load_dotenv()


embeddings = OpenAIEmbeddings()

vectorstore1 = FAISS.load_local(
    "faiss_index",
    embeddings=embeddings,
    allow_dangerous_deserialization=True
)

vectorstore2 = FAISS.load_local(
    "faiss_xlsx_index",
    embeddings=embeddings,
    allow_dangerous_deserialization=True
)


llm = ChatOpenAI(temperature=0, model="gpt-3.5-turbo")



# 프롬프트 로드 및 구성
def load_prompt_template(filepath: str) -> str:
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


prompt_text = load_prompt_template("prompt_official")
prompt = PromptTemplate(
    input_variables=["context", "question"],
    template=prompt_text
)

qa_chain = load_qa_chain(
    llm=llm,
    chain_type="stuff",
    prompt=prompt
)


# retriever와 XLSX retriever 준비
retriever1 = vectorstore1.as_retriever(search_kwargs={"k": 3})
retriever2 = vectorstore2.as_retriever(search_kwargs={"k": 3})

# RAG + 통계 기반 응답 함수
def double_rag(query):
    region_name = extract_seoul_district(query)
    if region_name is None:
        return "서울의 행정 구역이 아닙니다."

    docs1 = retriever1.get_relevant_documents(query)
    docs2 = retriever2.get_relevant_documents(query)
    unified_docs = docs1 + docs2
    rag_context = "\n\n".join([doc.page_content for doc in unified_docs])

    region_stat_context = f"{region_name}의 지역 통계 정보는 별도로 추가됩니다."

    full_context = f"[문서 기반 정보]\n{rag_context}\n\n[지역 기반 통계 정보]\n{region_stat_context}"

    response = qa_chain.invoke({
        "input_documents": unified_docs,
        "question": query,
        "context": full_context
    })

    return response['output_text']


if __name__ == "__main__":
    result = double_rag('강남구 3번 출구 앞에 검정색 쓰레기 봉지가 쌓여 있어요')
    print(result)

