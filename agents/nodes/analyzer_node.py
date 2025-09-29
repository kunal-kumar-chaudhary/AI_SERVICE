from typing import Dict, Any
from agents.schemas.state_schema import TripletState
from agents.schemas.agent_schemas import AnalyzerResponse
from services.llm_service import get_llm_response_async
import json

class AnalyzerAgent:
    """
    Analyzes text and extracts initial triplets with quality assessment
    """
    async def process(self, state: TripletState) -> TripletState:
        """
        extracts triplets and assesses their quality
        """
        try:
            prompt = self._create_analysis_prompt(state.raw_text)
            response = await get_llm_response_async(prompt)

            # parsing LLM response
            analysis_result = self._parse_response(response)

            if analysis_result["success"]:
                state.initial_triplets = analysis_result["triplets"]
                state.quality_scores["analyzer"] = analysis_result["quality_score"]
                state.analyzer_feedback = analysis_result["feedback"]
                state.processing_state = "analyzed"
            else:
                state.error_messages.append(f"Analyzer failed: {analysis_result['error']}")

        except Exception as e:
            state.error_messages.append(f"Analyzer exception: {str(e)}")
        
        return state
    

    def _create_analysis_prompt(self, text: str) -> str:
        return f"""
        Analyze the following text and extract RDF triplets. Also provide a quality assessment.

        REQUIREMENTS:
        1. Extract factual statements as [subject, predicate, object] triplets
        2. Use clear, specific predicates (e.g., "is_located_in", "has_property", "works_for")
        3. Ensure subjects and objects are meaningful entities
        4. Provide a quality score (0-1) based on clarity and factual content
        5. Return valid JSON with this structure:
        {{
            "triplets": [["subject", "predicate", "object"]],
            "quality_score": 0.8,
            "feedback": "Assessment of triplet quality and text complexity"
        }}

        Text: "{text}"

        JSON Response:
        """
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """
        parse LLM response and validate structure
        """

        try: 
            data = json.loads(response)

            # validating required fields
            if not all(key in data for key in ["triplets", "quality_score", "feedback"]):
                return {"success": False, "error": "Missing required fields in response"}
            
            # validare triplet structure
            triplets = data["triplets"]
            if not isinstance(triplets, list):
                return {"success": False, "error": "Triplets should be a list"}

            for triplet in triplets:
                if not isinstance(triplet, list) or len(triplet) !=3:
                    return {"success": False, "error": f"Invalid triplet format: {triplet}"}
            
            return {
                "success": True,
                "triplets": triplets,
                "quality_score": float(data["quality_score"]),
                "feedback": data["feedback"]
            }
        
        except json.JSONDecodeError as e:
            return {"success": False, "error": f"JSON decode error: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"Unexpected error: {str(e)}"}
