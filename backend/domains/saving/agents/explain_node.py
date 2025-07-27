from typing import List
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai.chat_models.base import ChatOpenAI
from langgraph.config import get_stream_writer
from langgraph.graph import END

from domains.common.agents.graph_state import GraphState
from domains.saving.agents.prompts import (SAVING_EXPLAIN_NODE_SYSTEM_PROMPT,
                                           SAVING_EXPLAIN_USER_PROMPT_TEMPLATE)


def init_explain_node(llm: BaseChatModel):

    llm = ChatOpenAI(model="gpt-4.1", temperature=0.3)

    async def node(state: GraphState):
        writer = get_stream_writer()

        print("============ Explain Node ============")

        prompt_template = ChatPromptTemplate.from_messages([
            ("system", SAVING_EXPLAIN_NODE_SYSTEM_PROMPT),
            ("user", SAVING_EXPLAIN_USER_PROMPT_TEMPLATE)
        ])

        products = state["selected"]

        if not products:
            writer({
                "chat_id": state["chat_id"],
                "status": "response",
                "content": {
                    "message": "적합한 상품을 찾지 못했어요."
                }
            })

            return {"next": END}

        writer({
            "chat_id": state["chat_id"],
            "status": "response",
            "content": {
                "products": [{
                    "name": p.product.name,
                    "product_type": "saving",
                    "options": p.product.format_interest_rates(),
                    "institution": p.product.institution,
                    "description": p.product.name,
                    "details": str(p.product),
                    "tags": [],
                } for p in products]
            }
        })

        research_blob = "\n\n## 외부 참고 정보\n" + "\n".join(
            f"- {d}" for d in state["documents"])

        blob: str = "\n---\n".join(map(str, products))

        print(blob)

        prompt = prompt_template.invoke({
            "user_info": "",
            "product_info": blob,
            "context": research_blob,
            "user_question": str(state["messages"][0].content),
        })

        chunks: List[str] = []
        async for chunk in llm.astream(prompt):
            chunk_content = str(chunk.content)
            chunks.append(chunk_content)
            writer({
                "chat_id": state["chat_id"],
                "status": "response",
                "content": {
                    "message": chunk_content
                }
            })

        writer({
            "chat_id": state["chat_id"],
            "status": "stop",
        })

        content = "".join(chunks)

        state["messages"].append(AIMessage(content=content, name="explainer"))
        state["next"] = END

        return state

    return node
