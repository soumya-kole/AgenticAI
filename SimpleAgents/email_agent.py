import os
from typing import Dict
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.prompts import ChatPromptTemplate
from langchain.tools import tool
from langchain_openai import ChatOpenAI

# Setup API key
os.environ["OPENAI_API_KEY"] = "<your-openai-key>"

# Setup LLM (GPT-4o or GPT-3.5)
llm = ChatOpenAI(model="gpt-4o", temperature=0)

# Replace with real email logic
def dummy_send_email(to: str, subject: str, body: str):
    print(f"\n📧 Sending email to: {to}")
    print(f"Subject: {subject}")
    print(f"Body: {body}\n")
    return "Email sent successfully."

# ----------- TOOL -----------
@tool
def send_fixed_email(subject: str, body: str) -> str:
    """Send an email to a fixed recipient address with the given subject and body."""
    recipient = "ops-team@example.com"
    return dummy_send_email(to=recipient, subject=subject, body=body)

# ----------- PROMPT ----------
prompt = ChatPromptTemplate.from_messages([
    ("system", """
You are an assistant that sends status update or alert emails.
The email address is fixed and not part of user input.
From the user message, extract the subject and body clearly, then send the email using the tool.
"""),
    ("user", "{input}"),
    ("assistant", "{agent_scratchpad}")
])

# ----------- AGENT -----------
agent = create_openai_functions_agent(
    llm=llm,
    tools=[send_fixed_email],
    prompt=prompt
)

executor = AgentExecutor(agent=agent, tools=[send_fixed_email], verbose=True)

# ----------- TEST ----------
if __name__ == "__main__":
    question = "Let the ops team know that database server db-prod-2 crashed at 2AM due to power loss. Subject can be 'DB Outage'."
    response = executor.invoke({"input": question})
    print("\n✅ Final Output:", response["output"])
