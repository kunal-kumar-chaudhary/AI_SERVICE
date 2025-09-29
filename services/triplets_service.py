import re
from typing import List, Tuple
import spacy

_nlp = None


def get_nlp():
    global _nlp
    if _nlp is None:
        _nlp = spacy.load("en_core_web_sm")
    return _nlp


def clean(text: str) -> str:
    """
    Basic text cleaning function
    """
    return re.sub(r"\s+", " ", text).strip()


def extract_svo_spacy(sentence: str):
    nlp = get_nlp()
    doc = nlp(sentence)
    triplets = []
    for token in doc:
        if token.pos_ == "VERB":  # processing every verb
            # subject can be to the left or as a child
            subj = [w for w in token.children if w.dep_ in ("nsubj", "nsubjpass")]
            objs = [w for w in token.children if w.dep_ in ("dobj", "attr", "dative", "oprd")]

            # prepositional objects
            for prep in [w for w in token.children if w.dep_ == "prep"]:
                pobj = [w for w in prep.children if w.dep_ == "pobj"]
                objs.extend(pobj)

            if subj and objs:
                for o in objs:
                    triplets.append((clean(subj[0].text), clean(token.lemma_), clean(o.text)))
    return triplets

def extract_corpus_triplets(corpus: List[str]) -> List[List[Tuple[str, str, str]]]:
    """
    extracting triplets from a list of text chunks
    """
    results = []
    for text in corpus:
        sent = text.strip()
        if not sent:
            continue
        triplets = extract_svo_spacy(sent)
        results.append(triplets)
    return results
