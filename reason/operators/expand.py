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
import copy
import re
import numpy as np

from utils.helper import table2string, triple2table
from utils.prompt import add_column_demo, add_column_react
from operators.graph_operators import Operators


def add_column_build_prompt(table_text, statement, table_caption=None, num_rows=100):
    table_str = table2string(table_text, caption=table_caption, num_rows=num_rows)
    prompt = "/*\n" + table_str + "\n*/\n"
    prompt += "Question: " + statement + "\n"
    prompt += "The existing columns are: "
    prompt += ", ".join(table_text[0]) + ".\n"
    prompt += "Explanation: "
    return prompt


def add_column_func(sample, table_info, llm, llm_options=None, debug=False, skip_op=[], strategy="top"):

    operator = {
        "operator_name": "add_column",
        "parameter_and_conf": [],
    }

    failure_sample_copy = copy.deepcopy(sample)
    failure_sample_copy["chain"].append(operator)

    table_text = table_info["table_text"]
    table_graph = table_info["table_graph"]
    triples = table_info["triples"]

    statement = sample["statement"]
    cleaned_statement = sample["statement"]
    cleaned_statement = re.sub(r"\d+", "_", cleaned_statement)

    prompt = "" + add_column_demo.rstrip() + "\n\n"
    prompt += add_column_build_prompt(table_text, cleaned_statement, num_rows=3)

    if llm_options is None:
        llm_options = llm.get_model_options()
    llm_options["n"] = 1

    responses = llm.generate_plus_with_score(prompt, options=llm_options)

    add_column_and_conf = {}

    for res, score in responses:
        try:
            f_add_func = re.findall(r"f_add_column\(.*\)", res, re.S)[0].strip()
            left = f_add_func.index("(") + 1
            right = f_add_func.index(")")
            add_column = f_add_func[left:right].strip()
            first_3_values = res.split("The value:")[-1].strip().split("|")
            first_3_values = [v.strip() for v in first_3_values]
            assert len(first_3_values) == 3
        except:
            continue

        add_column_key = str((add_column, first_3_values, res))
        if add_column_key not in add_column_and_conf:
            add_column_and_conf[add_column_key] = 0
        add_column_and_conf[add_column_key] += np.exp(score)

    if len(add_column_and_conf) == 0:
        return failure_sample_copy

    add_column_and_conf_list = sorted(add_column_and_conf.items(), key=lambda x: x[1], reverse=True)
    if strategy == "top":
        selected_add_column_key = add_column_and_conf_list[0][0]
        selected_add_column_conf = add_column_and_conf_list[0][1]
    else:
        raise NotImplementedError()

    add_column, first_3_values, llm_response = eval(selected_add_column_key)

    existing_columns = table_text[0]
    if add_column in existing_columns:
        return failure_sample_copy

    add_column_contents = [] + first_3_values


    try:
        left_index = llm_response.index("We extract the value from")
        right_index = llm_response.index("The value:")
        explanaiton_beginning = llm_response[left_index:right_index] + "The value:"
    except:
        return failure_sample_copy

    def _sample_to_simple_prompt_header(table_text, num_rows=3):
        x = ""
        x += "/*\n"
        x += table2string(table_text, num_rows=num_rows) + "\n"
        x += "*/\n"
        x += "Explanation: "
        return x

    new_prompt = ""
    new_prompt += (_sample_to_simple_prompt_header(table_text, num_rows=3) + llm_response[left_index:])

    headers = table_text[0]
    rows = table_text[1:]
    for i in range(3, len(rows)):
        partial_table_text = [headers] + rows[i : i + 1]
        cur_prompt = (
            new_prompt
            + "\n\n"
            + _sample_to_simple_prompt_header(partial_table_text)
            + explanaiton_beginning
        )

        cur_response = llm.generate(cur_prompt, options=llm.get_model_options(temperature=0.0, top_p=1.0, max_tokens=150, n=1)).strip()
        if debug:
            print(cur_prompt)
            print(cur_response)
            print("---")
            print()

        contents = cur_response
        if "|" in contents:
            contents = contents.split("|")[0].strip()

        add_column_contents.append(contents)

    if debug:
        print("New col contents: ", add_column_contents)

    add_column_info = [(str((add_column, add_column_contents)), selected_add_column_conf)]

    thought = "Add necessary columns to the table.\n" + responses[0][0].split("Answer:")[0].strip() if "Answer:" in responses[0][0] else responses[0][0].strip() + "\n"

    operator = {
        "operator_name": "add_column",
        "parameter_and_conf": add_column_info,
        "thought": thought,
    }

    sample_copy = copy.deepcopy(sample)
    sample_copy["chain"].append(operator)

    return sample_copy


def add_column_act(table_info, operator, skip_op=[], debug=False):
    table_info = copy.deepcopy(table_info)

    failure_table_info = copy.deepcopy(table_info)
    failure_table_info["act_chain"].append("skip f_add_column()")
    if "add_column" in skip_op:
        return failure_table_info
    if len(operator["parameter_and_conf"]) == 0:
        return failure_table_info

    add_column_key, _ = operator["parameter_and_conf"][0]
    add_column, add_column_contents = eval(add_column_key)

    table_text = table_info["table_text"]
    headers = table_text[0]
    rows = table_text[1:]

    header2contents = {}

    for i, header in enumerate(headers):
        header2contents[header] = []
        for row in rows:
            header2contents[header].append(row[i])


    if add_column.startswith("number of"):

        if debug:
            print("remove number of")
        return failure_table_info

    if len(set(add_column_contents)) == 1:

        if debug:
            print("all same")
        return failure_table_info

    for x in add_column_contents:
        if x.strip() == "":

            if debug:
                print("empty cell")
            return failure_table_info

    if add_column in headers:

        if debug:
            print("same column header")
        return failure_table_info

    for header in header2contents:
        if add_column_contents == header2contents[header]:

            if debug:
                print("different header, same content")
            return failure_table_info

    exist_flag = False


    for header, contents in header2contents.items():
        current_column_exist_flag = True

        for i in range(len(contents)):
            if add_column_contents[i] not in contents[i]:
                current_column_exist_flag = False
                break

        if current_column_exist_flag:
            exist_flag = True
            break
    if not exist_flag:
        if debug:
            print(add_column, add_column_contents)
            print("not substring of a column")
        return failure_table_info

    if debug:
        print("default")
    new_headers = headers + [add_column]
    new_rows = []
    for i, row in enumerate(rows):
        row.append(add_column_contents[i])
        new_rows.append(row)

    new_table_text = [new_headers] + new_rows
    table_info["table_text"] = new_table_text

    table_graph = table_info["table_graph"]
    ops = Operators()

    new_table_graph, new_graph_triples, _ = ops.add_column(table_graph, headers, len(rows), add_column, add_column_contents)
    table_info["table_graph"] = new_table_graph
    table_info["triples"] = new_graph_triples
    table_info["act_chain"].append(f"f_add_column({add_column})")
    table_info["add_column_info"] = (add_column, add_column_contents)

    return table_info