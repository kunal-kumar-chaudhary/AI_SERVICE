from typing import List, Dict, Any
from agents.schemas.state_schema import TripletState
from agents.utils.parse_llm_response import ParseLLMResponse
from services.llm_service import get_llm_response_async
import json

class SemanticCleanerAgent:
    """
    cleans and standardizes triplets for consistency
    """

    async def process(self, state: TripletState) -> TripletState:
        """
        cleans and standardizes triplets
        """

        try:
            if not state.initial_triplets:
                state.error_messsages.append("No initial triplets to clean.")
                return state

            prompt = self._create_cleaning_prompt(state.initial_triplets)
            response = await get_llm_response_async(prompt)
            llm_response_parsed = ParseLLMResponse._extract_json_from_markdown_response(response)
            cleaning_result = self._parse_response(llm_response_parsed)
            print("Cleaning Result:", cleaning_result)

            if cleaning_result["success"]:
                state.cleaned_triplets = cleaning_result["cleaned_triplets"]
                state.quality_scores["cleaner"] = cleaning_result["quality_score"]
                state.cleaner_feedback = cleaning_result["feedback"]
                state.processing_state = "cleaned"
            
            else:
                state.error_messages.append(f"Cleaner failed: {cleaning_result['error']}")
                state.cleaned_triplets = state.initial_triplets  # fallback to initial triplets
        
        except Exception as e:
            state.error_messages.append(f"Cleaner exception: {str(e)}")
            state.cleaned_triplets = state.initial_triplets  # fallback to initial triplets
        
        return state
    

    def _create_cleaning_prompt(self, triplets: List[List[str]]) -> str:
        triplets_str = json.dumps(triplets)
        return f"""
        Clean and standardize the following triplets for better semantic consistency.

        CLEANING TASKS:
        1. Normalize entity names (remove extra spaces, fix capitalization)
        2. Standardize predicates (use consistent naming like "is_a", "has_property", "located_in")
        3. Remove duplicate or very similar triplets
        4. Fix obvious semantic issues
        5. Ensure subjects and objects are meaningful entities

        REQUIREMENTS:
        - Maintain factual accuracy
        - Use snake_case for predicates
        - Remove triplets with generic or meaningless entities
        - Return valid JSON with this structure:

        {{
            "cleaned_triplets": [["subject", "predicate", "object"]],
            "cleaning_actions": ["List of actions taken"],
            "quality_score": 0.9,
            "feedback": "Summary of cleaning performed"
        }}

        Original triplets: {triplets_str}

        JSON Response:
        """
    
    def _parse_response(self, data: Dict[str, Any]) -> Dict[str, Any]:  # Changed parameter type
        """
        parse cleaning response - expects already parsed dict
        """
        try:
            required_fields = ["cleaned_triplets", "cleaning_actions", "quality_score", "feedback"]
            if not all(key in data for key in required_fields):
                return {
                    "success": False,
                    "error": "Missing required fields in cleaner response"
                }

            # validating triplet response
            triplets = data["cleaned_triplets"]
            if not isinstance(triplets, list):
                return {"success": False, "error": "cleaned_triplets should be a list"}
            
            for triplet in triplets:
                if not isinstance(triplet, list) or len(triplet) != 3:
                    return {"success": False, "error": f"Invalid triplet format: {triplet}"}
            
            return {
                "success": True,
                "cleaned_triplets": triplets,
                "cleaning_actions": data["cleaning_actions"],
                "quality_score": float(data["quality_score"]),
                "feedback": data["feedback"]
            }

        except Exception as e:
            return {"success": False, "error": f"Unexpected error: {str(e)}"}