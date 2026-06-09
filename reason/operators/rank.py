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

from utils.helper import table2string
from utils.prompt import sort_column_demo
from operators.graph_operators import Operators



def only_keep_num_and_first_dot(s):
    if s.strip() and s.strip()[0] == "-":
        minus = True
    else:
        minus = False
    ns = ""
    dot = False
    for c in s:
        if c in "0123456789":
            ns += c
        if c == ".":
            if dot == False:
                ns += c
                dot = True
    if ns == ".":
        return ""
    if ns == "":
        return ""
    if minus:
        ns = "-" + ns
    return ns


def sort_column_build_prompt(table_text, statement, table_caption=None, num_rows=100):
    table_str = table2string(table_text, caption=table_caption, num_rows=num_rows).strip()
    prompt = "/*\n" + table_str + "\n*/\n"
    prompt += "Question: " + statement + "\n"
    prompt += "The existing columns are: "
    prompt += ", ".join(table_text[0]) + ".\n"
    prompt += "Explanation:"
    return prompt


def sort_column_func(sample, table_info, llm, llm_options=None, debug=False, skip_op=[]):

    table_text = table_info["table_text"]

    statement = sample["statement"]
    prompt = "" + sort_column_demo.rstrip() + "\n\n"
    prompt += sort_column_build_prompt(table_text, statement, num_rows=3)
    responses = llm.generate_plus_with_score(prompt, options=llm_options)

    if debug:
        print(prompt)
        print(responses)

    sort_info_and_conf = {}

    headers = table_text[0]
    rows = table_text[1:]
    for res, score in responses:
        try:

            datatype = re.findall(r"The datatype is (\w*).", res, re.S)[0].strip()
            sort_order = re.findall(r'the order is "(.*)"\.', res, re.S)[0].strip()
            sort_column = re.findall(r"f_sort_column\((.*?)\)", res, re.S)[0].strip()
        except:
            continue

        if sort_order not in ["small to large", "large to small"]:
            continue
        if sort_column not in headers:
            continue
        sort_key = (sort_column, sort_order, datatype)
        if sort_key not in sort_info_and_conf:
            sort_info_and_conf[sort_key] = 0
        sort_info_and_conf[sort_key] += np.exp(score)

    sort_param_and_conf_list = []

    for (sort_column, sort_order, datatype), conf in sort_info_and_conf.items():
        sort_column_contents = []
        index = headers.index(sort_column)
        for row in rows:
            sort_column_contents.append(row[index])

        vs_to_sort = []
        vs_not_to_sort = []
        if datatype == "Numerical":
            for i in range(len(sort_column_contents)):
                v_str = sort_column_contents[i]
                v_str = only_keep_num_and_first_dot(v_str)
                if v_str == "" or v_str == ".":
                    vs_not_to_sort.append((sort_column_contents[i], i))
                else:
                    vs_to_sort.append((float(v_str), i))
        else:
            for i in range(len(sort_column_contents)):
                v_str = sort_column_contents[i]
                v_str = v_str.strip()
                if v_str == "":
                    vs_not_to_sort.append((sort_column_contents[i], i))
                else:
                    vs_to_sort.append((v_str, i))

        pure_vs_to_sort = [x[0] for x in vs_to_sort]
        if (
                sorted(pure_vs_to_sort) == pure_vs_to_sort
                or sorted(pure_vs_to_sort, reverse=True) == pure_vs_to_sort
        ):
            continue


        if sort_order == "small to large":
            vs_to_sort = sorted(vs_to_sort, key=lambda x: x[0])
        else:
            vs_to_sort = sorted(vs_to_sort, reverse=True, key=lambda x: x[0])
        index_order = [x[1] for x in vs_to_sort] + [x[1] for x in vs_not_to_sort]


        sort_param_and_conf_list.append(
            (
                sort_column,
                sort_order,
                datatype,
                index_order,
                max([x[0] for x in vs_to_sort]),
                min([x[0] for x in vs_to_sort]),
                conf,
            )
        )


    sort_param_and_conf_list = sorted(sort_param_and_conf_list, key=lambda x: x[-1])

    thought = responses[0][0].split("Answer:")[0].strip() if "Answer:" in responses[0][0] else responses[0][0].strip() + "\n"

    operator = {
        "operator_name": "sort_column",
        "parameter_and_conf": sort_param_and_conf_list,
        "thought": thought,
    }

    sample_copy = copy.deepcopy(sample)
    sample_copy["chain"].append(operator)

    if debug:
        print(sort_param_and_conf_list)

    return sample_copy


def sort_column_act(table_info, operator, strategy="top", filter="Only Numerical", skip_op=[]):
    table_info = copy.deepcopy(table_info)

    failure_table_info = copy.deepcopy(table_info)
    failure_table_info["act_chain"].append("skip f_sort_column()")

    if "sort_column" in skip_op:
        return failure_table_info
    if len(operator["parameter_and_conf"]) == 0:
        return failure_table_info

    if strategy == "top":
        sort_column, sort_order, datatype, index_order, max_v, min_v = operator["parameter_and_conf"][0][:-1]
    else:
        raise NotImplementedError()

    if filter == "Only Numerical":
        if datatype != "Numerical":
            return failure_table_info
    else:
        raise NotImplementedError()

    table_text = table_info["table_text"]
    headers = table_text[0]
    rows = table_text[1:]
    new_rows = [rows[i] for i in index_order]
    new_table_text = [headers] + new_rows

    table_info["sort_table_text"] = new_table_text
    table_info["sort_sub_table"] = (sort_column, sort_order, datatype, index_order, max_v, min_v)
    table_info["act_chain"].append(f"f_sort_column({sort_column})")


    return table_info