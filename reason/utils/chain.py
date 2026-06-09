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

import copy
import re
from tqdm import tqdm
import numpy as np
import pickle
import os
import multiprocessing as mp
from collections import defaultdict

from utils.helper import table2string
from operators import *
from utils.setup import *
from utils.prompt import reason_fs
from utils.load_data import load_skillbank

from tools import semantic_retrieve, BM25_retrieve, hybrid_retrieve

ops = Operators()


def get_act_func(name):
    try:
        return eval(f"{name}_act")
    except:
        def _default_act(table_text, *args, **kwargs):
            return copy.deepcopy(table_text)

        if "query" not in name:
            print("Unknown operator: ", name)
        return _default_act


def get_table_info(sample, skip_op=[], first_n_op=None):
    table_text = sample["table_text"]
    table_graph = sample["table_graph"]
    chain = sample["chain"]

    if first_n_op is not None:
        chain = chain[:first_n_op]


    table_info = {
        "table_text": table_text,
        "table_graph": table_graph,
        "triples": ops.get_triples(table_graph),
        "act_chain": []
    }


    for operator in chain:
        operator_name = operator["operator_name"]

        act_func = get_act_func(operator_name)

        table_info = act_func(table_info, operator, skip_op=skip_op)

    return table_info


def get_operator_name(string):

    res = re.findall(r"f_(.*?)\(.*\)", string)[0]
    return res


def get_all_operator_names(string):
    operator_names = []
    parts = string.split("->")
    for part in parts:
        part = part.strip()
        if part == "<END>":
            operator_names.append("<END>")
        else:

            res = re.findall(r"f_(.*?)\(.*\)", part)
            if res:
                operator_names.append(res[0])
    return operator_names


def generate_next_operator(
    sample,
    llm=None,
    llm_options=None,
    strategy="top",
    debug=False,
    use_skill=False,
    skills=("None", "None")
):

    table_info = get_table_info(sample)
    act_chain = table_info["act_chain"]

    if debug:
        print("Act Chain: ", act_chain, flush=True)


    kept_act_chain = [x for x in act_chain if not x.startswith("skip")]
    kept_act_chain_str = " -> ".join(kept_act_chain)
    if kept_act_chain_str:
        kept_act_chain_str += " ->"


    skip_act_chain = [x for x in act_chain if x.startswith("skip")]
    skip_act_chain_op_names = []

    for op in skip_act_chain:
        op = op[len("skip ") :]
        op_name = get_operator_name(op)
        skip_act_chain_op_names.append(op_name)

    if debug:
        print("Kept Act Chain: ", kept_act_chain, flush=True)
        print("Skip Act Chain: ", skip_act_chain, flush=True)


    last_operator = (
        "<init>" if not kept_act_chain else get_operator_name(kept_act_chain[-1])
    )


    possible_next_operators = possible_next_operator_dict[last_operator]
    possible_next_operators = [
        x for x in possible_next_operators if x not in skip_act_chain_op_names
    ]

    if debug:
        print("Last Operator: ", last_operator, flush=True)
        print("Possible Next Operators: ", possible_next_operators, flush=True)


    if len(possible_next_operators) == 1:
        log = {
            "act_chain": act_chain,
            "last_operator": last_operator,
            "possible_next_operators": possible_next_operators,
            "prompt": None,
            "response": None,
            "generate_operators": None,
            "next_operator": possible_next_operators[0],
        }
        return possible_next_operators[0], log


    prompt = ""
    for operator in possible_next_operators:
        if operator == "<END>":
            continue

        prompt += eval(f"plan_{operator}_demo") + "\n\n"

    prompt += plan_full_demo_simple + "\n\n"


    if use_skill:
        (success_skills_str, failure_skills_str) = skills
        prompt += (
            f"Here are some Successful Skills to help plan the the next operator:\n"
            f"{success_skills_str}"
            f"Use Successful Skills as references for possible reasoning patterns and operator transitions. "
            f"Adapt rather than copy, and decide the next operator based on the current table context and question.\n\n"
        )
    prompt += "Now, using the operations to answer the following question:\n\n"


    prompt += "/*\n" + table2string(table_info["table_text"]) + "\n*/\n"
    prompt += "Question: " + sample["statement"] + "\n"


    _possible_next_operators_str = " or ".join(
        [f"f_{op}()" if op != "<END>" else op for op in possible_next_operators]
    )

    if len(possible_next_operators) > 1:
        prompt += (
            f"The next operator must be one of {_possible_next_operators_str}.\n"
        )
    else:
        prompt += f"The next operator must be {_possible_next_operators_str}.\n"


    prompt += "Function Chain: " + kept_act_chain_str

    responses = llm.generate_plus_with_score(
        prompt, options=llm_options, end_str="\n\n"
    )


    if strategy == "top":
        response = responses[0][0]

        generate_operators = get_all_operator_names(response)
        if debug:
            print('Prompt:', prompt.split("\n\n")[-1])
            print('Response:', response)
            print("Generated Operators: ", generate_operators)
        next_operator = "<END>"
        for operator in generate_operators:

            if operator in possible_next_operators:
                next_operator = operator
                break

    elif strategy == "voting":
        next_operator_conf_dict = defaultdict(float)

        for response, score in responses:
            generate_operators = get_all_operator_names(response)
            next_operator = None
            for operator in generate_operators:
                if operator in possible_next_operators:
                    next_operator = operator
                    break
            if next_operator:
                next_operator_conf_dict[next_operator] += np.exp(score)

        if len(next_operator_conf_dict) != 0:
            next_operator_conf_pairs = sorted(
                next_operator_conf_dict.items(), key=lambda x: x[1], reverse=True
            )
            next_operator = next_operator_conf_pairs[0][0]
        else:
            next_operator = "<END>"

    log = {
        "act_chain": act_chain,
        "last_operator": last_operator,
        "possible_next_operators": possible_next_operators,
        "prompt": prompt,
        "response": response,
        "generate_operators": generate_operators,
        "next_operator": next_operator,
    }

    return next_operator, log


def reasoning_one_sample(
    sample,
    llm,
    llm_options=None,
    strategy="top",
    statement_emb=None,
    debug=False,
):
    dynamic_chain_log = []
    current_sample = copy.deepcopy(sample)


    nu_ids = sample["ids"]
    try:
        (vectordb, lexicondb) = load_skillbank()
        statement = sample["statement"]
        qtype_map = {"conditional lookup": "cl", "comparison": "comp", "extremum": "ext", "aggregation": "agg", "arithmetic": "arith"}
        statement_type = qtype_map[sample["qtype"]]
        modes = ["success", "failure"]

        skills = []
        for mode in modes:
            conds = {"$and": [{"type": {"$eq": statement_type}}, {"mode": {"$eq": mode}}]}
            branch_skill_nums = len(vectordb.get(where=conds, include=[])["ids"])
            lexicondb_branch = lexicondb[statement_type][mode]

            assert branch_skill_nums == len(lexicondb_branch)
            retrieved_skills, _, _ = hybrid_retrieve(vectordb, lexicondb_branch, statement, statement_emb, conds, branch_skill_nums, k=3, alpha=0.8, threshold=0.7)
            skills.append(retrieved_skills)

        success_skills_str = ""
        failure_skills_str = ""
        (success_skills, failure_skill) = skills


        if len(success_skills) > 0:
            for i, skill in enumerate(success_skills):
                success_skills_str += f"Success Skill {i + 1}:\n{str(skill)}\n\n"
        else:
            success_skills_str = "Success Skills: None\n"

        if len(failure_skill) > 0:
            for i, skill in enumerate(failure_skill):
                failure_skills_str += f"Failure Skill {i + 1}:\n{str(skill)}\n\n"
        else:
            failure_skills_str = "Failure Skills: None\n"


    except Exception as e:
        print(f"Use Skill Error in {nu_ids}: {str(e)}", flush=True)
        success_skills_str = "Success Skills: None\n"
        failure_skills_str = "Failure Skills: None\n"

    while True:

        next_operator, log = generate_next_operator(
            sample=current_sample,
            llm=llm,
            llm_options=llm_options,
            strategy=strategy,
            debug=debug,
            use_skill=True,
            skills=(success_skills_str, failure_skills_str)
        )
        dynamic_chain_log.append(log)

        if debug:
            print(next_operator)

        if next_operator == "<END>":
            break


        op_name, op_func, kargs, op_llm_options = operator_parameter_dict[next_operator]

        table_info = get_table_info(current_sample)

        current_sample = op_func(
            current_sample, table_info, llm=llm, llm_options=op_llm_options, **kargs
        )

    statement = sample["statement"]
    table_caption = sample["table_caption"]
    table_info = get_table_info(current_sample)
    triples = table_info["triples"]

    add_column_info = table_info["add_column_info"] if "add_column_info" in table_info else 'None'
    selected_rows = table_info["select_rows"] if "select_rows" in table_info else 'None'
    selected_columns = table_info["select_columns"] if "select_columns" in table_info else 'None'
    if "group_sub_table" in table_info:
        (group_column, group_info) = table_info["group_sub_table"]
        group_info_str = "group the column '{}', and compute the count of each unique value: {}".format(group_column, group_info)
    else:
        group_info_str = 'None'

    if "sort_sub_table" in table_info:
        sort_column, sort_order, datatype, index_order, max_v, min_v = table_info["sort_sub_table"]
        index_order_str = [f"row{x+1}" for x in index_order]
        sort_info_str = "sort the '{}' column '{}' with '{}' order, the rank with row id is {}, the max cell value is {}, the min cell value is {}.".format(datatype, sort_column, sort_order, index_order_str, max_v, min_v)
    else:
        sort_info_str = 'None'



    reason_prompt = reason_fs.rstrip() + "\n\n"
    reason_prompt += f"Question: {statement}\nTable caption: {table_caption}\nKnowledge triples: {triples}\nSalient rows: {selected_rows}\nGroup Info: {group_info_str}\nSort Info: {sort_info_str}\nSkills:\n{success_skills_str}{failure_skills_str}Output:\n"
    result_dict = llm.generate_graph_reason(reason_prompt, options=llm_options)[0]

    sample_copy = copy.deepcopy(current_sample)
    sample_copy["final_triples"] = table_info["triples"]
    sample_copy["act_chain"] = table_info["act_chain"]


    sample_copy["add_column_info"] = add_column_info
    sample_copy["select_rows_info"] = selected_rows
    sample_copy["select_columns_info"] = selected_columns
    sample_copy["group_column_info"] = group_info_str
    sample_copy["sort_column_info"] = sort_info_str

    sample_copy["results"] = result_dict


    return sample_copy, dynamic_chain_log


def _reasoning_with_cache_mp_core(arg):
    idx, sample, llm, llm_options, strategy, cache_dir, statement_emb = arg

    cache_filename = "case-{}.pkl"
    try:
        sample_id = sample["ids"]
        cache_path = os.path.join(cache_dir, cache_filename.format(idx))
        if os.path.exists(cache_path):
            _, proc_sample, log = pickle.load(open(cache_path, "rb"))
        else:
            proc_sample, log = reasoning_one_sample(
                sample=sample, llm=llm, llm_options=llm_options, strategy=strategy, statement_emb=statement_emb
            )
            pickle.dump((sample, proc_sample, log), open(cache_path, "wb"))
        return idx, proc_sample, log
    except Exception as e:
        print(f"Error in {sample_id}: {e}", flush=True)
        return idx, None, None


def reasoning_with_cache_mp(
    all_samples,
    statement_embs,
    llm,
    llm_options=None,
    strategy="top",
    cache_dir="./results/debug",
    n_proc=10,
    chunk_size=50
):
    os.makedirs(cache_dir, exist_ok=True)
    result_samples = [None for _ in range(len(all_samples))]
    reasoning_log_list = [None for _ in range(len(all_samples))]
    args = [
        (idx, sample, llm, llm_options, strategy, cache_dir, statement_embs[idx])
        for idx, sample in enumerate(all_samples)
    ]

    with mp.Pool(n_proc) as p:
        for idx, proc_sample, log in tqdm(
            p.imap_unordered(
                _reasoning_with_cache_mp_core, args, chunksize=chunk_size
            ),
            total=len(all_samples),
            desc=f"Table Graph Reasoning"
        ):
            result_samples[idx] = proc_sample
            reasoning_log_list[idx] = log

    return result_samples, reasoning_log_list