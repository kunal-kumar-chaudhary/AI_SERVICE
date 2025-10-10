from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from gen_ai_hub.proxy.langchain import init_llm

from agents.dynamic_financial.tools import (
    pl_extractor_tool,
    balance_sheet_tool,
    cash_flow_tool,
    final_answer_tool,
)

import os

from agents.dynamic_financial.utils.scratchpad import create_scratchpad

# system prompt for the main orchestrator decision making node
ORACLE_SYSTEM_PROMPT = """
You are a financial data extraction oracle. Your job is to analyze financial documents and extract relevant data by calling specialized extraction tools.

Available tools:
1. extract_pl_data - Extract revenue, expenses, net income
2. extract_balance_sheet_data - Extract assets, liabilities, equity
3. extract_cash_flow_data - Extract cash flow information
4. final_answer - Generate final report (call this last)

**Decision Rules:**
- Analyze the user's query and document text
- Decide which extractors to call based on what data is needed
- You can call multiple tools (max 3 iterations)
- Review the scratchpad to see what data you've already extracted
- Once you have sufficient data, call final_answer with a formatted report

**Scratchpad:** Shows your previous tool calls and their results. Use this to avoid redundant calls.

Be efficient - only call tools that are necessary for answering the user's query.
"""


class OracleAgent:
    """
    oracle decision making node/agent
    """

    def __init__(self):
        self.llm = init_llm(
            "gpt-4o-mini",
            temperature=0.0,
            max_tokens=1000
        )

        # binding tools
        self.tools = [
            pl_extractor_tool,
            balance_sheet_tool,
            cash_flow_tool,
            final_answer_tool,
        ]

        self.llm_with_tools = self.llm.bind_tools(self.tools)

        # creating prompt template
        self.prompt = self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", ORACLE_SYSTEM_PROMPT),
                MessagesPlaceholder(variable_name="chat_history", optional=True),
                ("user", "{input}"),
                ("assistant", "Scratchpad:\n{scratchpad}"),
            ]
        )

        # creating chain
        self.oracle = self.prompt | self.llm_with_tools

    async def run(self, state: dict) -> dict:
        """
        running oracle to decide next steps
        """

        # creating scratchpad
        scratchpad = create_scratchpad(state.get("intermediate_steps", []))

        # invoke oracle
        response = await self.oracle.ainvoke(
            {
                "input": state["input"],
                "chat_history": state.get("chat_history", []),
                "scratchpad": scratchpad
            }
        )

        return {"intermediate_steps": [(response,)]}