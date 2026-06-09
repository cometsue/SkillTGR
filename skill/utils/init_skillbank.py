import os
import json
import json5
import re
import pickle
import numpy as np
from tqdm import tqdm
import traceback

from rank_bm25 import BM25Okapi
import chromadb
from sentence_transformers import SentenceTransformer

from llm import LLM


def read_pkl_file(file_path):
    with open(file_path, "rb") as f:
        skill_dict = pickle.load(f)

    return skill_dict


def get_skill_lexical_text(skill, mode='success'):

    if mode == 'success':
        try:
            desc = skill.get("Description", "")
            patterns = " ".join(skill.get("Question pattern", [])).replace("[", "").replace("]", "")
            trigger = skill.get("Trigger", {})
            trigger_semantic = " ".join(trigger.get("semantic", [])).replace("[", "").replace("]", "")
            lexical_success_skill = f"{desc}\n{patterns}\n{trigger_semantic}"

            return lexical_success_skill

        except Exception as e:

            return None

    else:
        try:
            desc = skill.get("Description", "")
            root_cause = skill.get("Root Cause", "")
            constraints = " ".join(skill.get("Constraints", [])).replace("[", "").replace("]", "")
            lexical_failure_skill  = f"{desc}\n{root_cause}\n{constraints}"

            return lexical_failure_skill

        except Exception as e:

            return None


def get_skill_semantic_text(skill, mode='success'):

    if mode == 'success':
        try:
            desc = skill.get("Description", "")
            patterns = " ".join(skill.get("Question pattern", [])).replace("[", "").replace("]", "")
            trigger = skill.get("Trigger", {})
            trigger_semantic = ", ".join(trigger.get("semantic", [])).replace("[", "").replace("]", "")
            semantic_success_skill = f"Description: {desc}\nTrigger words: {trigger_semantic}\nQuestion patterns: {patterns}"

            return semantic_success_skill

        except Exception as e:

            return None

    else:
        try:
            desc = skill.get("Description", "")
            root_cause = skill.get("Root Cause", "")
            constraints = "; ".join(skill.get("Constraints", [])).replace("[", "").replace("]", "")
            semantic_failure_skill  = f"Description: {desc}\nRoot cause: {root_cause}\nConstraints: {constraints}"

            return semantic_failure_skill

        except Exception as e:

            return None


if __name__ == '__main__':

    model_path = "../sentencebert"
    device = "cuda:0"
    SentenceBERT = SentenceTransformer(model_path, device=device)

    success_raw_skill_path = "./skill/data/raw_skill/trainset/success_raw_skill.pkl"
    failure_raw_skill_path = "./skill/data/raw_skill/trainset/failure_raw_skill.pkl"

    success_raw_skills = read_pkl_file(success_raw_skill_path)
    failure_raw_skills = read_pkl_file(failure_raw_skill_path)

    client = chromadb.PersistentClient(path="./skill/skillbank/trainset_all/skill_db")
    VectorDB = client.get_or_create_collection(name="trainset_all", metadata={"hnsw:space": "cosine"})

    LexiconDB = {
        "cl": {"success":[], "failure":[]},
        "comp": {"success":[], "failure":[]},
        "ext": {"success":[], "failure":[]},
        "agg": {"success":[], "failure":[]},
        "arith": {"success":[], "failure":[]}
    }

    skill_types = ["conditional lookup", "comparison", "extremum", "aggregation", "arithmetic"]
    skill_types_map = {"conditional lookup": "cl", "comparison": "comp", "extremum": "ext", "aggregation": "agg", "arithmetic": "arith"}
    file_mode_pairs = [(success_raw_skills, "success"), (failure_raw_skills, "failure")]
    for raw_skill_file, mode in file_mode_pairs:
        for skill_file_name, skill_json in tqdm(raw_skill_file.items(), total=len(raw_skill_file), desc="Init Trainset_All SkillBank"):
            try:
                skill_type = skill_types_map[skill_json["Tag"]] if skill_json["Tag"] in skill_types else "ErrorType"
                if skill_type == "ErrorType":
                    print(f"{skill_file_name} is ErrorType")
                    continue

                skill_lexical_text = get_skill_lexical_text(skill_json, mode)
                skill_semantic_text = get_skill_semantic_text(skill_json, mode)
                skill_semantic_text_embs = SentenceBERT.encode([skill_semantic_text]).tolist()

                count_num = len(VectorDB.get(where={"$and": [{"type": {"$eq": skill_type}}, {"mode": {"$eq": mode}}]}, include=[])["ids"])
                if count_num != len(LexiconDB[skill_type][mode]):
                    raise ValueError(f"Mismatch between chromadb ({count_num}) and bm25 ({len(LexiconDB[skill_type][mode])})")

                skill_id = f"{skill_type}_{mode}_{count_num}"
                source_files = [f"{skill_file_name}"]
                skill_lexical_info = {
                    "skill_id": skill_id,
                    "source_files": source_files,
                    "type": skill_type,
                    "mode": mode,
                    "skill_json": skill_json,
                    "skill_lexical_text": skill_lexical_text
                }
                LexiconDB[skill_type][mode].append(skill_lexical_info)

                skill_semantic_metadatas = [{
                    "source_files": source_files,
                    "type": skill_type,
                    "mode": mode,
                    "skill_semantic_text": skill_semantic_text
                }]
                VectorDB.add(ids=[skill_id], documents=[str(skill_json)], embeddings=skill_semantic_text_embs, metadatas=skill_semantic_metadatas)

            except Exception as e:
                print(f"Error in {skill_file_name}, {str(e)}", flush=True)
                continue


    lexical_data_dir = "./skill/skillbank/trainset_all/lexical_data.pkl"
    semantic_data_dir = "./skill/skillbank/trainset_all/semantic_data.pkl"
    with open(lexical_data_dir, "wb") as f:
        pickle.dump(LexiconDB, f)

    semantic_data = VectorDB.get(include=["documents", "embeddings", "metadatas"])
    with open(semantic_data_dir, "wb") as f:
        pickle.dump(semantic_data, f)
