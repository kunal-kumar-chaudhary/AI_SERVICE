from typing import List, Tuple
from agents.schemas.state_schema import TripletState
from agents.nodes.analyzer_node import AnalyzerAgent
from agents.nodes.semantic_cleaner_agent import SemanticCleanerAgent
from agents.nodes.triplet_validator_agent import TripletValidatorAgent
from agents.nodes.aggregator_node import AggregatorAgent
from agents.nodes.json_repair_agent import JSONRepairAgent


class TripletOrchestrator:
    """
    orchestrates the triplet processing pipeline
    """

    def __init__(self):
        self.analyzer = AnalyzerAgent()
        self.cleaner = SemanticCleanerAgent()
        self.validator = TripletValidatorAgent()
        self.aggregator = AggregatorAgent()
        self.json_repair = JSONRepairAgent()

    async def preprocess_text_chunk(self, text_chunk: str) ->TripletState:
        """
        process a single text chunk through the multi agent pipeline

        args: 
            text_chunk: text to extract triplets from
        returns:
            list of triplets as (subject, predicate, object) tuples
        """

        # initializing state
        state = TripletState(raw_text=text_chunk)
        try:
            # stage 1: initial analysis
            while True:
                state = await self.analyzer.process(state)
                if not self._should_retry(state):
                    break
                state.retry_count += 1

            # stage 2: semantic cleaning
            if state.initial_triplets and not self._has_critical_errors(state):
                stage_retry_count = 0
                while True:
                    state = await self.cleaner.process(state)
                    if not self._should_retry(state):
                        break
                    state.retry_count += 1
                    stage_retry_count += 1

            # stage 3: validation (if cleaning succeeded or was skipped)
            if (state.cleaned_triplets or state.initial_triplets) and not self._has_critical_errors(state):
                
                while True:
                    state = await self.validator.process(state)
                    if not self._should_retry(state):
                        break
                    state.retry_count += 1

            # stage 4: aggregation (if validation succeeded or was skipped)
            # doesn't need retrying logic as it is simple aggregation
            state = self.aggregator.process(state)

            # converting to tuple format for compatibility
            final_triplets = [tuple(triplet) for triplet in state.final_triplets]

            return final_triplets
        
        except Exception as e:
            print(f"Orchestrator exception: {str(e)}")
            return []
    

    async def process_corpus(self, corpus: List[str]) -> List[List[Tuple[str, str, str]]]:
        """
        process entire corpus through the multi agent pipeline using async concurrency
        """
        if not corpus:
            return []
        
        results = []

        for i, text_chunk in enumerate(corpus):
            print(f"processing chunk {i+1}/{len(corpus)}")

            try:
                chunk_triplets = await self.preprocess_text_chunk(text_chunk)
                results.append(chunk_triplets)
            except Exception as e:
                print(f"Error processing chunk {i}: {e}")
                results.append([])

        return results
    

    def _has_critical_errors(self, state: TripletState) -> bool:
        """
        determine if state has critical errors that should halt further processing
        """
        return len(state.error_messages) > state.max_retries
    

    def _should_retry(self, state: TripletState) -> bool:
        """
        determine if we should retry a failed agent based on error messages and retry count
        """
        return (
            state.retry_count < state.max_retries and 
            not state.final_triplets and
            state.error_messages
        )