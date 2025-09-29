from typing import List, Dict, Any
from agents.schemas.state_schema import TripletState

class AggregatorAgent:
    """
    aggregates results from all the agents and determines final output
    """

    def process(self, state: TripletState) -> TripletState:

        try:
            # determine best triplets based on the quality scores and processing stages
            final_triplets = self._select_best_triplets(state)
            state.final_triplets = final_triplets
            state.processing_state = "completed"

            # calculating overall quality score
            overall_score = self._calculate_overall_quality(state)
            state.quality_scores["overall"] = overall_score
            print("Final Triplets:", state.final_triplets)
        
        except Exception as e:
            state.error_messages.append(f"Aggregator exception: {str(e)}")
            state.final_triplets = state.validated_triplets or state.cleaned_triplets or state.initial_triplets or []
        
        return state
    

    def _select_best_triplets(self, state: TripletState) -> List[List[str]]:
        """
        select the best quality triplets from processing pipeline
        """
        if state.validated_triplets:
            return state.validated_triplets
        elif state.cleaned_triplets:
            return state.cleaned_triplets
        elif state.initial_triplets:
            return state.initial_triplets
        else:
            return []
        
    def _calculate_overall_quality(self, state: TripletState) -> float:
        """
        calculate overall quality score based on individual agent scores
        """
        scores = [score for score in state.quality_scores.values() if isinstance(score, (int, float))]
        if not scores:
            return 0.0

        # weighted average (validator has higher weight)
        weights = {
            "analyzer": 0.3,
            "cleaner": 0.3,
            "validator": 0.4
        }

        weighted_sum = 0.0
        total_weight = 0.0

        for agent, weight in weights.items():
            if agent in state.quality_scores:
                weighted_sum += state.quality_scores[agent] * weight
                total_weight += weight

        return weighted_sum / total_weight if total_weight > 0 else 0.0
    