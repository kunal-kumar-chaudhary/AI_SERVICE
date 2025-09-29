from typing import List, Dict, Any
from agents.schemas.state_schema import TripletState
from agents.utils.parse_llm_response import ParseLLMResponse
from agents.utils.parse_llm_response import ParseLLMResponse
from services.llm_service import get_llm_response_async
import json


class TripletValidatorAgent:
    """
    validates triplets for factual accuracy and relevance
    """

    async def process(self, state: TripletState) -> TripletState:
        """
        validate triplets for accuracy and consistency
        """
        try:
            triplets_to_validate = state.cleaned_triplets or state.initial_triplets
            if not triplets_to_validate:
                state.error_messages.append("No triplets to validate.")
                return state

            prompt = self._create_validation_prompt(
                triplets_to_validate, state.raw_text
            )
            response = await get_llm_response_async(prompt)
            llm_response_parsed = ParseLLMResponse._extract_json_from_markdown_response(response)
            validation_result = self._parse_response(llm_response_parsed)

            if validation_result["success"]:
                state.validated_triplets = validation_result["validated_triplets"]
                state.quality_scores["validator"] = validation_result["quality_score"]
                state.validator_feedback = validation_result["feedback"]
                state.processing_state = "validated"
            else:
                state.error_messages.append(
                    f"Validator failed: {validation_result['error']}"
                )
                state.validated_triplets = (
                    triplets_to_validate  # fallback to input triplets
                )

        except Exception as e:
            state.error_messages.append(f"Validator exception: {str(e)}")
            state.validated_triplets = (
                triplets_to_validate  # fallback to input triplets
            )

        return state

    def _create_validation_prompt(
        self, triplets: List[List[str]], original_text: str
    ) -> str:
        triplets_str = json.dumps(triplets)
        return f"""
        Validate the following triplets against the original text for factual accuracy and semantic correctness.

        VALIDATION CRITERIA:
        1. Factual accuracy: Are the relationships stated correctly?
        2. Semantic validity: Do the predicates make sense between subject and object?
        3. Completeness: Are important facts missing?
        4. Consistency: Are there contradictions?
        5. Relevance: Are all triplets relevant to the source text?

        TASKS:
        - Remove factually incorrect triplets
        - Fix semantic issues if possible
        - Add missing important relationships if evident
        - Ensure consistency across all triplets

        Original text: "{original_text}"

        Triplets to validate: {triplets_str}

        Return JSON with this structure:
        {{
            "validated_triplets": [["subject", "predicate", "object"]],
            "validation_issues": ["List of issues found and fixed"],
            "quality_score": 0.85,
            "feedback": "Summary of validation process"
        }}

        JSON Response:
        """

    def _parse_response(self, response: str) -> Dict[str, Any]:
        """
        parse validation response
        """

        try:
            data = json.loads(response)
            required_fields = [
                "validated_triplets",
                "validation_issues",
                "quality_score",
                "feedback",
            ]
            if not all(key in data for key in required_fields):
                return {
                    "success": False,
                    "error": "Missing required fields in validator response",
                }

            # validating triplet structure
            triplets = data["validated_triplets"]
            if not isinstance(triplets, list):
                return {"success": False, "error": "Validated triplets must be a list"}

            for triplet in triplets:
                if not isinstance(triplet, list) or len(triplet) != 3:
                    return {
                        "success": False,
                        "error": "Each triplet must have exactly 3 elements",
                    }

            return {
                "success": True,
                "validated_triplets": triplets,
                "validation_issues": data["validation_issues"],
                "quality_score": float(data["quality_score"]),
                "feedback": data["feedback"],
            }

        except json.JSONDecodeError as e:
            return {"success": False, "error": f"JSON decode error: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"Unexpected error: {str(e)}"}
