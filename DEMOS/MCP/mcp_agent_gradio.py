import asyncio
import gradio as gr
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import AzureChatOpenAI
from dotenv import load_dotenv
load_dotenv()

# Define llm
model = AzureChatOpenAI(model="gpt-4o", temperature=0)

# Define MCP servers
async def run_agent(query):
    async with MultiServerMCPClient(
        {
            "tavily": {
                "command": "python",
                "args": ["/Users/arturoquiroga/GITHUB/3CLOUD-LANGCHAIN/AQ DEMOS/MCP/mcp_tavily_server.py"],
                "transport": "stdio",
            },
            "youtube_transcript": {
                "command": "python",
                "args": ["/Users/arturoquiroga/GITHUB/3CLOUD-LANGCHAIN/AQ DEMOS/MCP/mcp_yt_transcript_server.py"],
                "transport": "stdio",
            }, 
            "math": {
                "command": "python",
                "args": ["/Users/arturoquiroga/GITHUB/3CLOUD-LANGCHAIN/AQ DEMOS/MCP/mcp_math_server.py"],
                "transport": "stdio",
            },
            "exchange_rate": {
                "command": "python",
                "args": ["/Users/arturoquiroga/GITHUB/3CLOUD-LANGCHAIN/AQ DEMOS/MCP/mcp_exchange_rate_fetcher_server.py"],
                "transport": "stdio",
            },       
            "weather": {
                "command": "python",
                "args": ["/Users/arturoquiroga/GITHUB/3CLOUD-LANGCHAIN/AQ DEMOS/MCP/mcp_weather_server.py"],
                "transport": "stdio",
            },
        }
    ) as client:
        # Load available tools
        tools = client.get_tools()
        agent = create_react_agent(model, tools)

        # Add system message
        system_message = SystemMessage(content=(
                "You have access to multiple tools that can help answer queries. "
                "Use them dynamically and efficiently based on the user's request. "
        ))

        # Process the query
        agent_response = await agent.ainvoke({"messages": [system_message, HumanMessage(content=query)]})

        return agent_response["messages"][-1].content

# Gradio interface function
def gradio_interface(query):
    return asyncio.run(run_agent(query))

# Example queries for the Gradio interface
# "What is weather in new york"
# "What is FastMCP?"
# "summarize this youtube video in 200 words, here is a video link: https://www.youtube.com/watch?v=2f3K43FHRKo&ab_channel=OpenAI"
# "What is 2+2?"
# "get me the rate for mexican pesos to canadian dollars"
# "summarize this youtube video in 200 words, here is a video link: https://www.youtube.com/watch?v=7j1t3UZA1TY&ab_channel=IBMTechnology"

# Create Gradio interface
iface = gr.Interface(
    fn=gradio_interface,
    inputs="text",
    outputs="text",
    title="MCP Agent",
    description=(
        "Enter your query to interact with the MCP Agent. "
        "Example queries:\n"
        "- What is weather in new york\n"
        "- What is FastMCP?\n"
        "- summarize this youtube video in 200 words, here is a video link: https://www.youtube.com/watch?v=2f3K43FHRKo&ab_channel=OpenAI\n"
        "- What is 2+2?\n"
        "- get me the rate for mexican pesos to canadian dollars\n"
        "- summarize this youtube video in 200 words, here is a video link: https://www.youtube.com/watch?v=7j1t3UZA1TY&ab_channel=IBMTechnology"
    )
)

# Launch the Gradio app
if __name__ == "__main__":
    iface.launch()