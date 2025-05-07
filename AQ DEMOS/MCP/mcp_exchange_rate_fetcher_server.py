import httpx
from mcp.server.fastmcp import FastMCP  # Import FastMCP, the quickstart server base

mcp = FastMCP("Exchange Rate Server")  # Initialize an MCP server instance with a descriptive name


@mcp.tool()
async def get_exchange_rate(from_currency: str, to_currency: str) -> str:
    """Fetch current exchange rate from one currency to another."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.exchangerate-api.com/v4/latest/{from_currency}"
        )
        rates = response.json().get("rates", {})
        rate = rates.get(to_currency)
        if rate:
            return f"1 {from_currency} = {rate} {to_currency}"
        return "Unable to fetch exchange rate."

if __name__ == "__main__":
    mcp.run(transport="stdio")  # Run the server, using standard input/output for communication
    # mcp.run(transport="sse")  # Uncomment this line to run the server using Server-Sent Events (SSE)
    # mcp.run(transport="http")  # Uncomment this line to run the server using HTTP
    # mcp.run(transport="grpc")  # Uncomment this line to run the server using gRPC