import os
from typing import TypedDict, Optional

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END

# Enable LangChain debug mode to see chain execution details
import langchain

langchain.debug = True

# Set up LLM (GPT-4o)
load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPEN_AI_API_KEY")

llm = ChatOpenAI(model="gpt-4o", temperature=0)


# ----------- DUMMY TOOLS -----------
@tool
def get_company_history(company: str) -> str:
    """Retrieve historical background of a company. Might return empty if not found."""
    if company.lower() == "acme corp":
        return "Acme Corp was founded in 1950 as a manufacturer of rocket-powered gadgets."
    return ""


@tool
def get_stock_price(company: str) -> str:
    """Fetches the current stock price of the company."""
    return f"The current stock price of {company} is $123.45."


# ----------- STATE -----------
class CompanySummaryState(TypedDict):
    company: str
    history: Optional[str]
    summary: Optional[str]
    stock_info: Optional[str]
    enriched_summary: Optional[str]
    final_summary: Optional[str]


# ----------- NODES -----------
def agent_history_node(state: CompanySummaryState) -> CompanySummaryState:
    history = get_company_history.invoke({"company": state["company"]})

    if not history:
        # No history found - be explicit about it
        summary = f"No historical information is available for {state['company']} in our database."
    else:
        # Only use the retrieved history
        prompt = f"""
        Write a short company background for {state['company']} using ONLY the provided information. 
        Do not add any information that is not explicitly provided.

        Available information:
        {history}

        If the information is insufficient, state that clearly rather than making assumptions.
        """
        result = llm.invoke([HumanMessage(content=prompt)])
        summary = result.content

    return {**state, "history": history, "summary": summary}


def agent_stock_node(state: CompanySummaryState) -> CompanySummaryState:
    stock_info = get_stock_price.invoke({"company": state["company"]})

    # Check if we have a meaningful summary to enhance
    if not state.get('summary') or 'No historical information is available' in state['summary']:
        # Don't enhance if there's no base information
        enriched_summary = f"{state.get('summary', 'No company information available.')} Current stock price: {stock_info}"
    else:
        prompt = f"""
        Add the stock price information to this company summary. Use ONLY the information provided.
        Do not add any new facts or details not explicitly given.

        Existing Summary:
        {state['summary']}

        Stock Information to add:
        {stock_info}

        Simply combine these two pieces of information without adding anything else.
        """
        result = llm.invoke([HumanMessage(content=prompt)])
        enriched_summary = result.content

    return {**state, "stock_info": stock_info, "enriched_summary": enriched_summary}


def agent_finalize_node(state: CompanySummaryState) -> CompanySummaryState:
    # Check if we have meaningful content to summarize
    if not state.get('enriched_summary') or 'No historical information is available' in state.get('enriched_summary',
                                                                                                  ''):
        # Return as-is if no meaningful data
        final_summary = state.get('enriched_summary', 'No information available for this company.')
    else:
        prompt = f"""
        Create a concise 3-4 sentence summary using ONLY the information provided below.
        Do not add any facts, details, or context not explicitly stated.

        Information to summarize:
        {state['enriched_summary']}

        If the information is limited, acknowledge that clearly rather than filling gaps with assumptions.
        """
        result = llm.invoke([HumanMessage(content=prompt)])
        final_summary = result.content

    return {**state, "final_summary": final_summary}


# ----------- LANGGRAPH -----------
graph = StateGraph(CompanySummaryState)
graph.set_entry_point("GetHistory")

graph.add_node("GetHistory", agent_history_node)
graph.add_node("GetStock", agent_stock_node)
graph.add_node("Summarize", agent_finalize_node)

graph.add_edge("GetHistory", "GetStock")
graph.add_edge("GetStock", "Summarize")
graph.add_edge("Summarize", END)

workflow = graph.compile()


# ----------- EXECUTOR -----------
def run_company_summary(company: str):
    initial_state = {"company": company}
    result = workflow.invoke(initial_state)
    return result["final_summary"]


# Example:
if __name__ == "__main__":
    company_name = "Acme Corp"
    final_output = run_company_summary(company_name)
    print('\n✅ Final summary :: \n')
    print(final_output)

