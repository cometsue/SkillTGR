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
from prompt import raw_skill_decision_prompt, skill_merge_prompt
from few_shot_demo import raw_skill_decision_demo
from retrieve_skill import hybrid_retrieve


def load_raw_skill(file_path):
    result_dict = {}
    skill_files = [f for f in os.listdir(file_path) if os.path.isfile(os.path.join(file_path, f))]
    skill_files.sort(key=lambda x: int(x.split("-")[1].split(".")[0]))

    for skill_file in skill_files:
        try:
            with open(os.path.join(file_path, skill_file), "r", encoding='utf-8') as f:
                skill_text = f.read()

                skill_json = json5.loads(skill_text)
            result_dict[skill_file] = skill_json
        except Exception as e:

            continue

    return result_dict


def read_pkl_file(file_path):
    with open(file_path, "rb") as f:
        skill_dict = pickle.load(f)

    return skill_dict


def gen_skill_decision(raw_skill, retrieved_skill, llm, llm_options, mode="success"):
    prompt = raw_skill_decision_prompt.replace("[raw_skill_decision_demo]", raw_skill_decision_demo)
    prompt = prompt.replace("[success_or_failure]", mode)
    prompt = prompt.replace("[current_raw_skill]", raw_skill)
    prompt = prompt.replace("[retrieved_skill]", retrieved_skill)
    responses = llm.generate_plus_with_score(prompt, llm_options)
    decision = responses[0][0].split("**Decision**:")[-1].strip()

    return decision


def gen_merged_skill(existing_skill, candidate_skill, llm, llm_options):
    prompt = skill_merge_prompt.replace("[retrieved_skill]", existing_skill)
    prompt = prompt.replace("[current_raw_skill]", candidate_skill)
    responses = llm.generate_plus_with_score(prompt, llm_options)
    merged_skill = responses[0][0]

    return merged_skill



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
    SBERT = SentenceTransformer(model_path, device=device)

    base_url = 'http://localhost:8001/v1'
    openai_api_key = 'EMPTY'
    model_name = 'qwen3.5-9b'
    llm = LLM(model=model_name, key=openai_api_key, base_url=base_url)
    llm_options = llm.get_model_options(temperature=0.0, top_p=1.0, max_tokens=2048, n=1)

    success_raw_skill_path = "./skill/data/raw_skill/trainset/success_raw_skill.pkl"
    failure_raw_skill_path = "./skill/data/raw_skill/trainset/failure_raw_skill.pkl"

    failure_raw_skills = read_pkl_file(failure_raw_skill_path)
    client = chromadb.PersistentClient(path="./skill/skillbank/trainset/skill_db")
    collection = client.get_or_create_collection(name="SkillBank", metadata={"hnsw:space": "cosine"})

    with open("./skill/skillbank/trainset/bm25_skill.pkl", "rb") as f:
        bm25_skillbank = pickle.load(f)

    bm25_data = {}
    collection_data = {}
    bm25_data_save_dir = "./skill/skillbank/trainset/bm25_skill.pkl"
    collection_data_save_dir = "./skill/skillbank/trainset/chroma_skill.pkl"

    error_logs_dir = "./skill/skillbank/trainset/error_logs.txt"

    skill_types = ["conditional lookup", "comparison", "extremum", "aggregation", "arithmetic"]
    skill_types_map = {"conditional lookup": "cl", "comparison": "comp", "extremum": "ext", "aggregation": "agg", "arithmetic": "arith"}
    skill_modes = ["success", "failure"]

    for skill_file_name, skill_json in tqdm(failure_raw_skills.items(), total=len(failure_raw_skills), desc="Processing Trainset Failure Skill"):
        try:
            mode = "failure"
            skill_type = skill_types_map[skill_json["Tag"]] if skill_json["Tag"] in skill_types else "ErrorType"
            if skill_type == "ErrorType":
                print(f"{skill_file_name} is ErrorType")
                continue

            skill_semantic_text = get_skill_semantic_text(skill_json, mode)
            skill_semantic_text_embs = SBERT.encode([skill_semantic_text]).tolist()
            skill_lexical_text = get_skill_lexical_text(skill_json, mode)

            skill_chromadb = collection
            count_num = len(collection.get(where={"$and": [{"type": {"$eq": skill_type}}, {"mode": {"$eq": mode}}]}, include=[])["ids"])
            bm25_skill_branch = bm25_skillbank[skill_type][mode]

            if count_num != len(bm25_skill_branch):
                raise ValueError(f"Mismatch between chromadb ({count_num}) and bm25 ({len(bm25_skill_branch)})")

            if count_num == 0:
                retrieved_skill = "None"
                decision = gen_skill_decision(str(skill_json), retrieved_skill, llm, llm_options, mode)

            else:

                conds = {"$and": [{"type": {"$eq": skill_type}}, {"mode": {"$eq": mode}}]}
                retrieved_skills, top_k_scores, top_k_indices = hybrid_retrieve(skill_chromadb, bm25_skill_branch, skill_lexical_text, skill_semantic_text_embs, conds, count_num, k=1, alpha=0.7, threshold=None)
                retrieved_skill = retrieved_skills[0]
                decision = gen_skill_decision(str(skill_json), str(retrieved_skill), llm, llm_options, mode)

            if "add" in decision.lower():

                skill_id = f"{skill_type}_{mode}_{count_num}"
                source_files = [f"{skill_file_name}"]
                add_bm25_skill = {
                    "skill_id": skill_id,
                    "source_files": source_files,
                    "type": skill_type,
                    "mode": mode,
                    "skill_json": skill_json,
                    "skill_lexical_text": skill_lexical_text
                }
                bm25_skillbank[skill_type][mode].append(add_bm25_skill)

                add_chromadb_metadatas = [{
                    "source_files": source_files,
                    "type": skill_type,
                    "mode": mode,
                    "skill_semantic_text": skill_semantic_text
                }]
                collection.add(ids=[skill_id], documents=[str(skill_json)], embeddings=skill_semantic_text_embs, metadatas=add_chromadb_metadatas)


                bm25_data = bm25_skillbank
                collection_data = collection.get(include=["documents", "embeddings", "metadatas"])
                with open(bm25_data_save_dir, "wb") as f:
                    pickle.dump(bm25_data, f)

                with open(collection_data_save_dir, "wb") as f:
                    pickle.dump(collection_data, f)



            elif "merge" in decision.lower() and count_num != 0:
                merge_skill_json = json5.loads(gen_merged_skill(str(retrieved_skill), str(skill_json), llm, llm_options))

                top1_index = top_k_indices[0]
                skill_id = bm25_skill_branch[top1_index]["skill_id"]
                source_files = bm25_skill_branch[top1_index]["source_files"]
                source_files.append(f"{skill_file_name}")
                merge_skill_lexical_text = get_skill_lexical_text(merge_skill_json, mode=mode)
                merge_skill_semantic_text = get_skill_semantic_text(merge_skill_json, mode=mode)
                merge_skill_semantic_text_embs = SBERT.encode([merge_skill_semantic_text]).tolist()

                update_chromadb_metadatas = [{
                    "source_files": source_files,
                    "type": skill_type,
                    "mode": mode,
                    "skill_semantic_text": merge_skill_semantic_text
                }]

                bm25_skillbank[skill_type][mode][top1_index] = {
                    "skill_id": skill_id,
                    "source_files": source_files,
                    "type": skill_type,
                    "mode": mode,
                    "skill_json": merge_skill_json,
                    "skill_lexical_text": merge_skill_lexical_text
                }

                collection.update(ids=[skill_id], documents=[str(merge_skill_json)], embeddings=merge_skill_semantic_text_embs, metadatas=update_chromadb_metadatas)

                bm25_data = bm25_skillbank
                collection_data = collection.get(include=["documents", "embeddings", "metadatas"])
                with open(bm25_data_save_dir, "wb") as f:
                    pickle.dump(bm25_data, f)

                with open(collection_data_save_dir, "wb") as f:
                    pickle.dump(collection_data, f)


            elif "discard" in decision.lower():
                continue

            else:
                continue

        except Exception as e:
            os.makedirs(os.path.dirname(error_logs_dir), exist_ok=True)
            with open(error_logs_dir, "a", encoding="utf-8") as f:
                f.write("\n" + "=" * 80 + "\n")
                f.write(f"Error File: {skill_file_name}\n")
                f.write(f"Error Type: {type(e).__name__}\n")
                f.write(f"Error Repr: {repr(e)}\n")
                f.write("Traceback:\n")
                f.write(traceback.format_exc())
                f.write("=" * 80 + "\n")

            print(f"Error in {skill_file_name}", flush=True)

