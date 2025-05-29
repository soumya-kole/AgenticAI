import os
from dotenv import load_dotenv
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.prompts import ChatPromptTemplate
from langchain.tools import tool
from langchain_openai import ChatOpenAI
import random


load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPEN_AI_API_KEY")

llm = ChatOpenAI(model="gpt-4o", temperature=0)


def dummy_send_email(to: str, subject: str, body: str):
    print(f"\n📧 Sending email to: {to}")
    print(f"Subject: {subject}")
    print(f"Body: {body}\n")
    return random.randint(0, 1)


@tool
def send_fixed_email(subject: str, body: str) -> str:
    """Send an email to a fixed recipient address with the given subject and body.

    Args:
        subject: Email subject line
        body: Email body content

    Returns:
        Confirmation message when email is sent successfully.
    """
    recipient = "ops-team@example.com"
    result = dummy_send_email(to=recipient, subject=subject, body=body)
    if result == 0:
        return f"❌ TASK FAILED: Email NOT Sent. TRY AGAIN."
    return f"✅ TASK COMPLETED: Email successfully sent to {recipient} with subject '{subject}'. No further action needed."


prompt = ChatPromptTemplate.from_messages([
    ("system", """
You are an assistant that sends status update or alert emails to ops-team@example.com.

INSTRUCTIONS:
1. Extract the subject and body from the user's message
2. Send exactly ONE email using the send_fixed_email tool
3. Once the email is sent successfully, provide a brief confirmation and STOP
4. DO NOT send multiple emails or call the tool repeatedly
5. DO NOT ask for additional information - work with what's provided

The email address is fixed at ops-team@example.com and not part of user input.
"""),
    ("user", "{input}"),
    ("assistant", "{agent_scratchpad}")
])

agent = create_openai_functions_agent(
    llm=llm,
    tools=[send_fixed_email],
    prompt=prompt
)

executor = AgentExecutor(
    agent=agent,
    tools=[send_fixed_email],
    verbose=True,
    max_execution_time=30,  # 30 second timeout instead of max_iterations
    return_intermediate_steps=True
)

if __name__ == "__main__":
    question = "Let the ops team know that database server db-prod-2 crashed at 2AM due to power loss. Subject can be 'DB Outage'."

    try:
        response = executor.invoke({"input": question})
        print("\n✅ Final Output:", response["output"])
    except Exception as e:
        print(f"\n❌ Error: {e}")