import subprocess
import fire
import os
import pandas as pd
import pickle
import sys
sys.path.append("reason")
sys.path.append("skill")

from utils.load_data import load_dataset, load_skillbank, load_statement_embs
from utils.llm import LLM
from utils.chain import reasoning_with_cache_mp
from utils.evaluate import *

date = '260513'

def main(
    dataset_name: str = "wikitq",
    dataset_path: str = "reason/data/wikitq/test_lower_refined.jsonl",
    table_graphs_path: str = "reason/data/wikitq/graphs",
    statement_embs_path: str = "reason/data/wikitq/test_statement_embs.pkl",
    results_dir: str = "results/wikitq/qwen3.5-9b",
    base_url="http://localhost:8001/v1",
    openai_api_key="EMPTY",
    model_name="qwen3.5-9b",
    first_n=-1,
    n_proc=10,
    chunk_size=4
):
    print(f"Dateset: {dataset_name}")
    print(f"LLM: {model_name}")
    dataset = load_dataset(dataset_name, dataset_path, first_n, table_graphs_path) # wikitq: 4344; tabfact: 2024
    statement_embs = load_statement_embs(dataset, statement_embs_path)

    gpt_llm = LLM(model=model_name, key=openai_api_key, base_url=base_url)
    os.makedirs(results_dir, exist_ok=True)

    final_results, _ = reasoning_with_cache_mp(
        dataset,
        statement_embs,
        llm=gpt_llm,
        llm_options=gpt_llm.get_model_options(temperature=0.0, top_p=1.0, max_tokens=4096, n=1),
        strategy="top",
        cache_dir=os.path.join(results_dir, "cache"),
        n_proc=n_proc,
        chunk_size=chunk_size,
    )
    # print(final_results)

    # eval
    acc, samples_dict = wikitq_match_func_for_samples(dataset_name, dataset, final_results, tagged_dataset_path='reason/data/wikitq/tagged_data')
    print("Accuracy:", acc)

    df = pd.DataFrame({
        "ID": list(samples_dict.keys()),
        "Correct": list(samples_dict.values())
    })
    df = df.sort_values(by="ID", key=lambda x: x.apply(lambda s: int(s.split('-')[1])))
    output_file = results_dir + "/TGQA-{}.xlsx".format(date)
    df.to_excel(output_file, index=False)
    print("Saved successfully:", output_file)

    print(
        f'Accuracy: {acc}',
        file=open(os.path.join(results_dir, "TGQA-result-{}.txt".format(date)), "w")
    )

    pickle.dump(
        final_results, open(os.path.join(results_dir, "TGQA-final_result-{}.pkl".format(date)), "wb")
    )


if __name__ == "__main__":
    fire.Fire(main)

