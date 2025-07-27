import re
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai.chat_models.base import ChatOpenAI
from langgraph.config import get_stream_writer

from langchain_upstage import ChatUpstage

from domains.common.agents.graph_state import (
    GraphState,
    ProductSearchResult,
)
from domains.saving.agents.prompts import (SAVING_ANALYSIS_SYSTEM_PROMPT,
                                           SAVING_ANALYSIS_USER_PROMPT_TEMPLATE)

import asyncio


def _parse_saving_analysis(response: str):
    out = {"thought": None, "answer": None, "valid": False}

    thought_m = re.search(r"<Thought>(.*?)</Thought>", response, re.I | re.S)
    answer_m = re.search(r"<Answer>(.*?)</Answer>", response, re.I | re.S)

    if thought_m:
        out["thought"] = thought_m.group(1).strip()

    if answer_m:
        ans_raw = answer_m.group(1).strip()
        ans_pick = re.search(r"(적합|부적합)", ans_raw)
        if ans_pick:
            out["answer"] = ans_pick.group(1)

    if "부적합" not in out.get("answer", ""):
        out["valid"] = True

    return out


async def _evaluate_product_fit(
    llm: BaseChatModel,
    product: ProductSearchResult,
    state: GraphState,
) -> bool:

    llm = ChatOpenAI(model="gpt-4o")
    #llm = ChatUpstage(model="solar-pro2", reasoning_effort="low")

    prompt_template = ChatPromptTemplate([
        ("system", SAVING_ANALYSIS_SYSTEM_PROMPT),
        ("user", SAVING_ANALYSIS_USER_PROMPT_TEMPLATE),
    ])

    research_blob = "\n\n## 외부 참고 정보\n" + "\n".join(
        f"- {d}" for d in state["documents"])

    print(state["user_info"])

    prompt = prompt_template.invoke({
        "user_info": state["user_info"],
        "user_question": str(state["messages"][0].content),
        "product_info": str(product),
        "context": research_blob,
    })

    res = await llm.ainvoke(prompt)
    result = str(res.content)

    match llm:
        case ChatUpstage(model="solar-pro2"):
            result = re.sub(r'<think>.*?</think>', '', result, flags=re.DOTALL)

    parsed = _parse_saving_analysis(result)

    print(parsed["answer"], parsed["valid"])

    return parsed["valid"]


def init_filter_node(llm: BaseChatModel):

    async def node(state: GraphState):
        print("============ Fileter Node ============")
        writer = get_stream_writer()

        products = state.get("candidates") or []

        writer({
            "chat_id": state["chat_id"],
            "status": "pending",
            "content": {
                "message":
                    "상품을 분석하고 있습니다.",
                "products": [{
                    "name": p.product.name,
                    "product_type": "saving",
                    "institution": p.product.institution
                } for p in products]
            }
        })

        print(len(products))

        eval_result = await asyncio.gather(
            *[_evaluate_product_fit(llm, product, state) for product in products])
        filtered = [product for eval, product in zip(eval_result, products) if eval]

        return {
            "selected": filtered,
            "next": "router",
        }

    return node
