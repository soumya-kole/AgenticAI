import asyncio

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from firstagent.agents.exchange_rate_agent import get_agent
from firstagent.utils.project_init import initialize

# Initialize Vertex AI
client = initialize()

APP_NAME = "FirstAgentAlternativeApp"
USER_ID = "soumya123"


async def main(query):
    #create memory session
    session_service = InMemorySessionService()
    # my_session = await session_service.create_session(APP_NAME, USER_ID)
    # print(f"--- Got Session Properties ---")
    # print(f"ID (`id`):                {my_session.id}")
    # print(f"Application Name (`app_name`): {my_session.app_name}")
    # print(f"User ID (`user_id`):         {my_session.user_id}")
    # print(f"State (`state`):           {my_session.state}")  # Note: Only shows initial state here
    # print(f"Events (`events`):         {my_session.events}")  # Initially empty
    # print(f"Last Update (`last_update_time`): {my_session.last_update_time:.2f}")
    # print(f"---------------------------------")

    # Create runner
    runner = Runner(
        app_name=APP_NAME,
        agent=await get_agent(),
        session_service=session_service,
    )

    # my_session = await session_service.create_session(app_name=APP_NAME, user_id=USER_ID)

    content = types.Content(role="user", parts=[types.Part(text=query)])

    events = runner.run_async(
        user_id=USER_ID,
        session_id="123jh",
        new_message=content,
    )


    # print the response
    async for event in events:
        if event.is_final_response():
            final_response = event.content.parts[0].text
            print(f"Final Response: {final_response}")

if __name__ == "__main__":
    asyncio.run(main("What is the capital of India?"))





