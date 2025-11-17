from google.adk.agents import LlmAgent
from google.genai import types

from firstagent.tools.exchange_rate import get_exchange_rate
from firstagent.utils.config import config


async def get_agent():
    generate_content_config = types.GenerateContentConfig(
        temperature=config.temperature,
        max_output_tokens=config.max_output_tokens,
        top_p=config.top_p,)
    agent = LlmAgent(
        model=config.agent_model,
        name='currency_exchange_agent',
        generate_content_config=generate_content_config,
        tools=[get_exchange_rate],
    )
    return agent

# app = AdkApp(agent=agent)
#
#
# async def main(message: str = "What is the exchange rate from US dollars to SEK on 2025-04-03?"):
#     async for event in app.async_stream_query(
#         user_id="USER_ID",
#         message=message,
#     ):
#         # Events from async_stream_query are dictionaries
#         author = event.get("author", "unknown")
#         content = event.get("content")
#
#         if content and "parts" in content:
#             for part in content["parts"]:
#                 if "text" in part and part["text"]:
#                     print(f"[{author}]: Agent response - {part['text']}")
#                 elif "function_call" in part:
#                     func_call = part["function_call"]
#                     print(f"[{author}]: Function call - {func_call.get('name', 'unknown')}")
#                     if "args" in func_call:
#                         print(f"  Args: {func_call['args']}")
#                 elif "function_response" in part:
#                     func_resp = part["function_response"]
#                     print(f"[{author}]: Function response - {func_resp.get('name', 'unknown')}")
#                     if "response" in func_resp:
#                         print(f"  Response: {func_resp['response']}")
#         else:
#             # Fallback for events without content
#             print(f"[{author}]: {event}")
#
# if __name__ == "__main__":
#     asyncio.run(main())