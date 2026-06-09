import networkx as nx
import json
import re
import pickle

def table_to_graph(sample):

    # load data
    table_caption = sample["table_caption"] # str
    table_text = sample["table_text"] # 2D list
    columns = table_text[0]
    records = table_text[1:]

    # record by columns
    records_col = {}
    for i, column in enumerate(columns):
        col_values = []
        for record in records:
            col_values.append(record[i])
        records_col[column] = col_values

    # init table graph
    TG = nx.Graph()
    # add meta node
    TG.add_node('meta', ntype='meta', value=table_caption, layer=0)
    # add row nodes & meta-row edge
    for i in range(len(records)):
        row_id = 'row{}'.format(i + 1)
        TG.add_node(row_id, ntype='row', value=row_id, layer=1)
        TG.add_edge('meta', row_id, etype='has', eindex=0)
    # add cell nodes & row-cell edges
    eindex = 1
    for column, cells in records_col.items():
        for i, cell in enumerate(cells):
            cell_id = "{}-{}".format(column, cell)
            if cell_id not in TG:
                TG.add_node(cell_id, ntype='cell', value=cell, layer=2)
            TG.add_edge('row{}'.format(i + 1), cell_id, etype=column, eindex=eindex)
        eindex += 1
    return TG


if __name__ == '__main__':
    # data_path = './wikitq/test_lower_extended.jsonl'
    # save_path = './wikitq/graphs/{}-{}.pkl'

    # # wikitq table_id: csv/203-csv/733.tsv
    # data_path = './wikitq/train_lower_extended.jsonl'
    # save_path = './wikitq/train_graphs/{}-{}.pkl'
    #
    # data = []
    # with open(data_path, 'r') as f:
    #     for line in f.readlines():
    #         data.append(json.loads(line))
    # f.close()
    # print(len(data))
    #
    # table_list = []
    # for sample in data:
    #     if sample["table_id"] not in table_list:
    #         table_graph = table_to_graph(sample)
    #         table_list.append(sample["table_id"])
    #
    #         csv_num, tsv_num = re.findall(r'\d+', sample["table_id"])
    #         with open(save_path.format(csv_num, tsv_num), 'wb') as f:
    #             pickle.dump(table_graph, f)
    #         f.close()
    #     else:
    #         continue

    # tabfact table_id: 2-12206617-3.html.csv
    data_path = './tabfact/test_lower_refined.jsonl'
    save_path = './tabfact/graphs/{}.pkl'

    data = []
    with open(data_path, 'r') as f:
        for line in f.readlines():
            data.append(json.loads(line))
    f.close()
    print(len(data))

    table_list = []
    for sample in data:
        if sample["table_id"] not in table_list:
            table_graph = table_to_graph(sample)
            table_list.append(sample["table_id"])

            table_id = sample["table_id"].split('.html.csv')[0]
            with open(save_path.format(table_id), 'wb') as f:
                pickle.dump(table_graph, f)
            f.close()
        else:
            continue
