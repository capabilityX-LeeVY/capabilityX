# client.py
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def run():
    server_params = StdioServerParameters(
        command="python",
        args=["src/functions/mcp/server.py"],  
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools_resp = await session.list_tools()
            print("Available tools:")
            for tool in tools_resp.tools:
                print(f" • {tool.name}: {tool.description}")

            res_resp = await session.list_resources()
            print("\nAvailable resources:")
            for r in res_resp.resources:
                print(f" • {r.uri}")

            # Call list_test_cases tool
            try:
                print("\nCalling list_test_cases()...")
                result = await session.call_tool("list_test_cases", {})
                print("Test Cases:")
                for content in result.content:
                    if hasattr(content, 'text'):
                        print(content.text) # type: ignore
                    else:
                        print(content)
            except Exception as e:
                print(f"Error calling list_test_cases: {e}")

if __name__ == "__main__":
    asyncio.run(run())
