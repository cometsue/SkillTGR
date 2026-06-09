# Copyright 2024 The Chain-of-Table authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import json
import pickle
from tqdm import tqdm
import os
import re
import networkx as nx
import chromadb
from sentence_transformers import SentenceTransformer


def load_wikitq_dataset(dataset_name, dataset_path, first_n=-1):
    dataset = []
    if first_n != -1:
        all_lines = []
        for line in open(dataset_path):
            all_lines.append(line)
            if len(all_lines) >= first_n: break
    else:
        all_lines = open(dataset_path).readlines()

    for i, line in tqdm(enumerate(all_lines), total=len(all_lines), desc=f"Loading {dataset_name} dataset"):
        info = json.loads(line)
        dataset.append(info)

    return dataset


def read_table_graphs(pkl_file_path):
    table_graphs = {}
    for filename in tqdm(os.listdir(pkl_file_path), total=len(os.listdir(pkl_file_path)), desc=f"Loading table graphs"):
        file = os.path.join(pkl_file_path, filename)
        with open(file, 'rb') as f:
            table_graph = pickle.load(f)
            table_graphs[filename] = table_graph
        f.close()

    return table_graphs


def match_sample_graph(dataset_name, dataset, table_graphs):
    for sample in tqdm(dataset, total=len(dataset), desc="Aligning Table and Graph"):
        table_id = sample["table_id"]
        if dataset_name == "wikitq":
            csv_num, tsv_num = re.findall(r'\d+', table_id)
            table_graph = table_graphs['{}-{}.pkl'.format(csv_num, tsv_num)]
        elif dataset_name == "tabfact":
            table_graph = table_graphs['{}.pkl'.format(table_id.split('.html.csv')[0])]
        sample["table_graph"] = table_graph
        sample["chain"] = []

    return dataset


def load_dataset(dataset_name, dataset_path='../data/wikitq/test_lower_refined.jsonl', first_n=-1, pkl_file_path='../data/wikitq/graphs'):
    dataset = load_wikitq_dataset(dataset_name, dataset_path, first_n)
    table_graphs = read_table_graphs(pkl_file_path)
    all_samples = match_sample_graph(dataset_name, dataset, table_graphs)

    return all_samples



def load_skillbank(chromadb_path="skill/skillbank/testset/skill_db", vectordb_pkl_path="skill/skillbank/testset/semantic_data.pkl", lexicondb_pkl_path="skill/skillbank/testset/lexical_data.pkl", rebulid=False):
    if rebulid:
        print("Rebuilding Skillbank...")
        client = chromadb.PersistentClient(path=chromadb_path)
        # client.delete_collection(name="testset")
        client.delete_collection(name="trainset_evolve_init")
        # vectordb = client.get_or_create_collection(name="testset", metadata={"hnsw:space": "cosine"})
        vectordb = client.get_or_create_collection(name="trainset_evolve_init", metadata={"hnsw:space": "cosine"})
        with open(vectordb_pkl_path, 'rb') as f:
            vectordb_data = pickle.load(f)
        vectordb.add(
            ids=vectordb_data["ids"],
            embeddings=vectordb_data["embeddings"],
            documents=vectordb_data["documents"],
            metadatas=vectordb_data["metadatas"],
        )

        with open(lexicondb_pkl_path, 'rb') as f:
            lexicondb = pickle.load(f)

        skillbank = (vectordb, lexicondb)

    else:
        client = chromadb.PersistentClient(path=chromadb_path)
        # vectordb = client.get_or_create_collection(name="testset", metadata={"hnsw:space": "cosine"})
        vectordb = client.get_or_create_collection(name="trainset_evolve_init", metadata={"hnsw:space": "cosine"})
        lexicondb_pkl_path = "skill/skillbank/trainset/bm25_skill.pkl"
        with open(lexicondb_pkl_path, 'rb') as f:
            lexicondb = pickle.load(f)


        skillbank = (vectordb, lexicondb)

    return skillbank


def load_statement_embs(all_samples, statement_embs_path="reason/data/wikitq/test_statement_embs.pkl", model_path = "skill/sentencebert", device = "cuda:3"):
    if os.path.exists(statement_embs_path):
        print("Loading Statement Embeddings...", end="")
        statement_embs = pickle.load(open(statement_embs_path, "rb"))
        print("Successfully!")

    else:
        SentenceBERT = SentenceTransformer(model_path, device=device)
        statements = [sample["statement"] for sample in all_samples]
        statement_embs = []
        for statement in tqdm(statements, total=len(statements), desc="Embedding Statements"):
            embedding = SentenceBERT.encode([statement]).tolist()
            statement_embs.append(embedding)

        pickle.dump(statement_embs, open(statement_embs_path, "wb"))

    return statement_embs