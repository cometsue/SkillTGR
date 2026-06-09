import json
import copy
import re
import numpy as np

from utils.helper import table2string, triple2table
from utils.prompt import select_column_fs, critic_columns_fs
from operators.graph_operators import Operators


def select_column_build_prompt(triples, statement, table_caption=None, num_rows=100):

    prompt = select_column_fs.rstrip() + "\n\n"
    table_schema = triple2table(triples, num_rows)
    prompt += "Step1: Observation\nTable schema:\n" + "/*\n" + table_schema + "\n*/\n"
    prompt += "Question: " + statement + "\n\n"
    prompt += "Step2: Thought\n"

    return prompt



def select_column_func(sample, table_info, llm, llm_options, debug=False, num_rows=3):
    table_text = table_info["table_text"]
    table_graph = table_info["table_graph"]
    triples = table_info["triples"]
    statement = sample["statement"]
    table_caption = sample["table_caption"]

    select_column_prompt = select_column_build_prompt(triples, statement, table_caption, num_rows)
    responses = llm.generate_plus_with_score(select_column_prompt, options=llm_options)

    if debug:
        print(select_column_prompt)
        print(responses)

    pattern_col = r"f_select_column\(\[(.*?)\]\)"
    pred_conf_dict = {}
    for res, score in responses:
        try:
            pred = re.findall(pattern_col, res, re.S)[0].strip()
        except Exception:
            continue
        pred = pred.replace('"', '').split(", ")
        pred = [i.strip() for i in pred]
        pred = sorted(pred)
        pred = str(pred)
        if pred not in pred_conf_dict:
            pred_conf_dict[pred] = 0
        pred_conf_dict[pred] += np.exp(score)


    select_col_rank = sorted(pred_conf_dict.items(), key=lambda x: x[1], reverse=True)

    thought = responses[0][0].split("Step3: Action")[0].strip() if "Step3: Action" in responses[0][0] else responses[0][0].strip()  + "\n"

    operator = {
        "operator_name": "select_column",
        "parameter_and_conf": select_col_rank,
        "thought": thought,
    }

    sample_copy = copy.deepcopy(sample)
    sample_copy["chain"].append(operator)

    return sample_copy


def select_column_act(table_info, operator, union_num=2, skip_op=[]):
    table_info = copy.deepcopy(table_info)
    table_text = table_info["table_text"]
    table_graph = table_info["table_graph"]

    failure_table_info = copy.deepcopy(table_info)
    failure_table_info["act_chain"].append("skip f_select_column()")

    if "select_column" in skip_op:
        return failure_table_info

    def union_lists(to_union):
        return list(set().union(*to_union))

    selected_columns_info = operator["parameter_and_conf"]
    selected_columns_info = sorted(selected_columns_info, key=lambda x: x[1], reverse=True)
    selected_columns_info = selected_columns_info[:union_num]
    selected_columns = [x[0] for x in selected_columns_info]
    selected_columns = [eval(x) for x in selected_columns]
    selected_columns = union_lists(selected_columns)

    real_selected_columns = []
    columns = table_text[0]

    for selected_column in selected_columns:
        if selected_column in columns:
            real_selected_columns.append(selected_column)

    if len(real_selected_columns) == 0:
        real_selected_columns = ["*"]

    ops = Operators()
    subgraph = ops.select_columns(graph=table_graph, columns=real_selected_columns)
    triples = ops.get_triples(subgraph)

    table_info["table_graph"] = subgraph
    table_info["triples"] = triples
    table_info["act_chain"].append(f"f_select_column({', '.join(real_selected_columns)})")
    table_info["select_columns"] = real_selected_columns

    return table_info
