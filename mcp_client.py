import asyncio

from fastmcp import Client


MCP_SERVER_URL = "http://127.0.0.1:8000/mcp"

def print_mcp_result(record_id: str, result) -> None:
    print(f"\nRecord ID: {record_id}")
    print(f"Raw MCP result: {result}")


async def main() -> None:
    async with Client(MCP_SERVER_URL) as client:
        result_1 = await client.call_tool(
            "lookup_job_application",
            {"record_id": "APP-0001"},
        )

        result_2 = await client.call_tool(
            "lookup_job_application",
            {"record_id": "APP-0003"},
        )

        print("=" * 80)
        print("MCP CLIENT DEMONSTRATION")
        print("=" * 80)

        print_mcp_result(record_id="APP-0001",result=result_1)
        print_mcp_result(record_id="APP-0003",result=result_2)


if __name__ == "__main__":
    asyncio.run(main())