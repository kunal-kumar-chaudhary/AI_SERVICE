import asyncio
from agents.financial.orchestrator import financial_orchestrator

async def test_extraction():
    """
    test financial extraction
    """

    sample_text = """
    XYZ Corporation Annual Report 2023
    
    Income Statement:
    Revenue: $10,000,000
    Operating Expenses: $6,000,000
    Net Income: $4,000,000
    
    Balance Sheet:
    Total Assets: $50,000,000
    Total Liabilities: $30,000,000
    Shareholders' Equity: $20,000,000
    """

    result = await financial_orchestrator.extract(sample_text)
    print("Extraction Result:", result)


if __name__ == "__main__":
    asyncio.run(test_extraction())
    

