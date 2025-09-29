import json
import re
from typing import Dict, Any

class ParseLLMResponse:
    """
    utility class containing methods to parse LLM response
    """
    @staticmethod
    def _extract_json_from_markdown_response(response: str) -> Dict[str, Any]:
        """
        extract JSON object from markdown formatted LLM response
        """
        try:
            json_match = re.search(r'```json(.*?)```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1).strip()
                return json.loads(json_str)
        except:
            pass

        try:
            return json.loads(response)
        except:
            return {}

    