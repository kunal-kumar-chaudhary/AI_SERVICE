from typing import Dict, Any
from services.llm_service import get_llm_response_async
import json
import re

class JSONRepairAgent:
    """
    repairs malformed JSON responses from other agents
    """
    
    async def repair_json(self, malformed_json: str) -> Dict[str, Any]:
        """
        attempt to repair malformed JSON
        """

        try:
            cleaned = self._basic_json_cleaning(malformed_json)

            try:
                return {"success": True, "data": json.loads(cleaned)}
            except json.JSONDecodeError:
                pass

            # if basic cleaning fails, using LLM repair
            prompt = self._create_repair_prompt(malformed_json)
            response = await get_llm_response_async(prompt)

            # extracting json from response
            repaired_json = self._extract_json_from_response(response)

            if repaired_json:
                return {"success": True, "data": json.loads(repaired_json)}
            else:
                return {"success": False, "error": "LLM repair failed to produce valid JSON."}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _basic_json_cleaning(self, text: str) -> str:
        """
        basic json cleaning operations
        """
        text = re.sub(r'^[^{]*({.*})[^}]*$', r'\1', text, flags=re.DOTALL)
        text = text.strip()

        # fixing common quote issue
        text = re.sub(r'([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', text)

        return text
    
    def _create_repair_prompt(self, malformed_json: str) -> Dict[str, Any]:
        """
        create a repair prompt for the LLM
        """
        return f"""
        The following JSON is malformed. Please repair it and return only the valid JSON:

        Malformed JSON:
        {malformed_json}

        Requirements:
        - Fix syntax errors
        - Ensure proper quotes and brackets
        - Maintain the original data structure and content
        - Return only the repaired JSON, no explanations

        Repaired JSON:
        """
    
    def _extract_json_from_response(self, response: str) -> Dict[str, Any]:
        """
        extract JSON object from LLM response
        """
        try:
            json_match = re.search(r'({.*})', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                return json.loads(json_str)
        except:
            pass

        try:
            return json.loads(response)
        except:
            pass

        return None
            