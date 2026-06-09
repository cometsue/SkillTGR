import os
import json
import numpy as np
import re

from rank_bm25 import BM25Okapi
import chromadb


def semantic_retrieve(skill_branch_db, query_emb, conds, count_num, k=1):
    if len(conds) == 0:
        results = skill_branch_db.query(
            query_embeddings=query_emb,
            n_results=count_num
        )
    else:

        results = skill_branch_db.query(
            query_embeddings=query_emb,
            n_results=count_num,
            where=conds
        )
    topk_skill_ids = results["ids"][0]
    scores = [round(1 - dist, 4) for dist in results["distances"][0]]
    sorted_ids = sorted(int(re.search(r'\d+', x).group()) for x in topk_skill_ids)
    ordered_scores = [s for _, s in sorted(zip(topk_skill_ids, scores), key=lambda x: int(re.search(r'\d+', x[0]).group()))]

    if len(topk_skill_ids) < count_num:
        full_ids = list(range(count_num))
        id_score_map = dict(zip(sorted_ids, scores))
        ordered_scores = [id_score_map.get(iid, 0.0) for iid in full_ids]

    return ordered_scores, topk_skill_ids


def BM25_retrieve(skill_branch, query, k=1):

    corpus = []
    for skill in skill_branch:
        skill_lexical_text = skill['skill_lexical_text']
        corpus.append(skill_lexical_text)

    if len(corpus) > 0:
        tokenized_corpus = [doc.split(" ") for doc in corpus]
        bm25 = BM25Okapi(tokenized_corpus)
        tokenized_query = query.split(" ")
        scores = bm25.get_scores(tokenized_query)
        ordered_scores = [round(score, 4) for score in scores.tolist()]

        return ordered_scores
    else:
        # return None, None, None
        return []

def hybrid_retrieve(skill_branch_db, skill_branch, query, query_emb, conds, count_num, k=3, alpha=0.8, threshold=0.7):
    semantic_scores, _ = semantic_retrieve(skill_branch_db, query_emb, conds, count_num, k)
    lexical_scores = BM25_retrieve(skill_branch, query, k)

    def min_max_norm(scores):
        mn, mx = min(scores), max(scores)
        return [round((s - mn) / (mx - mn + 1e-8), 4) for s in scores]

    assert len(semantic_scores) == len(lexical_scores)
    semantic_scores = min_max_norm(semantic_scores)
    lexical_scores = min_max_norm(lexical_scores)
    hybrid_scores = np.array([alpha * sem + (1-alpha) * lex for sem, lex in zip(semantic_scores, lexical_scores)])


    if threshold is not None and threshold > 0:
        mask = hybrid_scores > threshold
        filtered_indices = np.where(mask)[0]
        filtered_scores = hybrid_scores[mask]

        if len(filtered_indices) == 0:
            return [], [], []

        top_k_idx = np.argsort(filtered_scores)[::-1][:k]
        top_k_indices = filtered_indices[top_k_idx].tolist()
        top_k_scores = filtered_scores[top_k_idx].tolist()
        retrieved_skills = [skill_branch[top_k_idx]["skill_json"] for top_k_idx in top_k_indices]

        return retrieved_skills, top_k_scores, top_k_indices

    else:
        top_k_idx = np.argsort(hybrid_scores)[::-1][:k]
        top_k_indices = top_k_idx.tolist()
        top_k_scores = hybrid_scores[top_k_idx].tolist()
        retrieved_skills = [skill_branch[top_k_idx]["skill_json"] for top_k_idx in top_k_indices]

        return retrieved_skills, top_k_scores, top_k_indices