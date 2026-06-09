import pickle
import os
import pandas as pd
import re


def read_pkl(pkl_file):
    with open(pkl_file, 'rb') as pkl_f:
        data = pickle.load(pkl_f)
    return data


def table2df(table_text, num_rows=100):
    header, rows = table_text[0], table_text[1:]
    rows = rows[:num_rows]
    df = pd.DataFrame(data=rows, columns=header)
    return df


def table2string(table_text, num_rows=100, caption=None):
    df = table2df(table_text, num_rows)
    linear_table = ""
    if caption is not None:
        linear_table += "table caption : " + caption + "\n"

    header = "column : " + " | ".join(df.columns) + "\n"
    linear_table += header
    rows = df.values.tolist()
    for row_idx, row in enumerate(rows):
        row = [str(x) for x in row]
        line = "row{} : ".format(row_idx + 1) + " | ".join(row)
        if row_idx != len(rows) - 1:
            line += "\n"
        linear_table += line
    return linear_table


def get_operator_info(operator_name, sample_result):
    parameter_and_info = ""

    if "add_column" in operator_name:
        (add_column, add_column_contents) = sample_result[1]["add_column_info"]
        parameter_and_info = f"Add the '{add_column}' column, the cell value for each row is {add_column_contents}."

    elif "select_row" in operator_name:
        selected_rows = sample_result[1]["select_rows_info"]
        if '*' in selected_rows:
            parameter_and_info = "all rows are salient rows relevant to the question"
        else:
            parameter_and_info = f"{selected_rows} are salient rows relevant to the question"

    elif "select_column" in operator_name:
        selected_columns = sample_result[1]["select_columns_info"]
        if '*' in selected_columns:
            parameter_and_info = "all columns are salient columns relevant to the question"
        else:
            parameter_and_info = f"{selected_columns} are relevant columns to the question"

    elif "group_column" in operator_name:
        parameter_and_info = sample_result[1]["group_column_info"]

    elif "sort_column" in operator_name:
        parameter_and_info = sample_result[1]["sort_column_info"]

    return parameter_and_info


def generate_trajectory(pkl_file_path, first_n=-1):

    pkl_files = [f for f in os.listdir(pkl_file_path) if os.path.isfile(os.path.join(pkl_file_path, f))]
    pkl_files.sort(key=lambda x: int(x.split('-')[1].split('.')[0]))
    pkl_files = pkl_files if first_n == -1 else pkl_files[:first_n]


    trajectories = {}
    for pkl_file in pkl_files:
        try:
            sample_result = read_pkl(os.path.join(pkl_file_path, pkl_file))

            statement = sample_result[0]['statement']
            ids = sample_result[0]['ids']
            table_text = sample_result[0]['table_text']
            table_caption = sample_result[0]['table_caption']
            linear_table = table2string(table_text, num_rows=100, caption=table_caption)
            table_info = "**Table**:\n/*\n{}\n*/\n\n**Question**:\n{}\n".format(linear_table, statement)


            action_chain = []
            action_chain_func = []
            for operator in sample_result[2][-1]["act_chain"]:
                if "skip" in operator:
                    continue
                operator_func = re.sub(r'\(.*?\)', '()', operator)
                action_chain_func.append(operator_func)
                action_chain.append(operator)

            dynamic_chain = '**Dynamic chain**:\n' + ' -> '.join(action_chain_func) + "\n"

            step = 0
            action_info = []
            for operator in sample_result[1]["chain"]:
                if operator["operator_name"] in dynamic_chain:
                    step += 1
                    action = action_chain[step - 1]

                    parameter_and_info = get_operator_info(operator["operator_name"], sample_result)
                    thought = operator["thought"]

                    step_info = f"Execution {step}:\nOperator: {action}\nParameter and Info: {parameter_and_info}\nThought: \n{thought}"
                    action_info.append(step_info)

            operator_info = f"**Operator Execution**:\n" + "\n\n".join(action_info)
            reason_path = sample_result[1]["results"]["paths"]
            reason_thought = sample_result[1]["results"]["thought"]
            reason_answer = sample_result[1]["results"]["answer"]
            reason_info = f"**Final Reason**:\nReason paths:\n{reason_path}\nThought:\n{reason_thought}\n\nPrediction Answer:\n{reason_answer}"

            trace_info = table_info + "\n" + dynamic_chain + "\n" + operator_info + "\n\n" + reason_info
            trajectories[ids] = trace_info

        except Exception as e:
            print(f"Error in {ids}", str(e))
            continue

    return trajectories


