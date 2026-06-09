import networkx as nx
import re

class Operators:
    def get_triples(self, graph, sort=True):
        """
        :param graph: current graph state, usually the subgraph; class: python networkx graph
        :param sort: sort the triples alphabetically
        :return: triples: (row_value, column_edge, cell_value); list: a list of triples tuples
        """
        triples = []
        for u, v, d in graph.edges(data=True):
            if graph.nodes[u]['ntype'] == 'meta' or graph.nodes[v]['ntype'] == 'meta':
                continue

            if graph.nodes[u]['ntype'] == 'row':
                triples.append((graph.nodes[u]['value'], d['etype'], graph.nodes[v]['value'], d['eindex']))
            else:
                triples.append((graph.nodes[v]['value'], d['etype'], graph.nodes[u]['value'], d['eindex']))

        if sort:
            triples.sort(key=lambda x: (int(x[0].replace('row', '')), x[3]))

        return [t[:3] for t in triples]


    def select_columns(self, graph, columns):
        """
        :param graph: current graph state, usually the full graph; class: python networkx graph
        :param columns: columns (edge) to select; list: a list of string column name
        :return: subgraph: subgraph with selected columns; class: python networkx graph
        """
        nodes_on_edge = [(u, v) for u, v, d in graph.edges(data=True) if d.get('etype') in columns]
        subgraph = graph.edge_subgraph(nodes_on_edge).copy()
        if not subgraph:
            return graph
        else:
            return subgraph



    def add_column(self, graph, column_set, num_rows, column, values):
        """
        :param graph: current graph state; class: python networkx graph
        :param column_set: column set of the table; list: a list of string column name
        :param num_rows: number of rows in the table; int: number of rows
        :param column: the extended column; string: the column name
        :param values: the column value for each row; list: column values set
        :return: extended graph, triples, success
        """
        if column in column_set:
            return graph, self.get_triples(graph), 'Column {} already exists'.format(column)
        elif column == '':
            return graph, self.get_triples(graph), 'The added column is null'
        elif len(values) != num_rows:
            return graph, self.get_triples(graph), 'No enough cell values for each row'

        try:
            eindex = len(column_set) + 1
            for i, cell_value in enumerate(values):
                cell_id = "{}-{}".format(column, cell_value)
                if cell_id not in graph:
                    graph.add_node(cell_id, ntype="cell", value=cell_value, layer=2)
                graph.add_edge("row{}".format(i+1), cell_id, etype=column, eindex=eindex)

            return graph, self.get_triples(graph), 'success'

        except Exception as e:
            return graph, self.get_triples(graph), 'execute error'


    def select_rows(self, graph, rows):
        """
        :param graph: current graph state, usually the full graph; class: python networkx graph
        :param rows: rows (node) to select; list: a list of string row name
        :return: subgraph: subgraph with selected rows; class: python networkx graph
        """
        if '*' in rows:
            return graph
        else:
            target_rows = set(rows)
            nodes_on_edges = [(u, v) for u, v, d in graph.edges(data=True) if u in target_rows or v in target_rows]
            subgraph = graph.edge_subgraph(nodes_on_edges).copy()
            if not subgraph:
                return graph
            else:
                return subgraph

    def filter_by_string(self, graph, column_set, column, conditions):
        """
        :param graph: current graph state, usually the subgraph; class: python networkx graph
        :param column_set: column set of the table; list: a list of string column name
        :param column: column (edge) to select; string: the column name
        :param conditions: the cell value(string) set; list: a list of conditions
        :return: subgraph, filtered_triples, success
        """
        if column not in column_set:
            return graph, self.get_triples(graph), 'Column {} is not in column set'.format(column)
        try:

            conds = [str(conditions).lower()] if isinstance(conditions, str) else [str(c).lower() for c in conditions]


            matched_rows = set()
            for u, v, d in graph.edges(data=True):
                if d.get('etype') == column:

                    cell_node = v if graph.nodes[u]['ntype'] == 'row' else u
                    cell_val = str(graph.nodes[cell_node].get('value', '')).lower()


                    if any(c in cell_val for c in conds):
                        matched_rows.add(u if cell_node == v else v)

            triples = []
            nodes_on_edge = []
            for u, v, d in graph.edges(data=True):
                if graph.nodes[u]['ntype'] == 'meta' or graph.nodes[v]['ntype'] == 'meta':
                    continue

                row, cell = (u, v) if graph.nodes[u]['ntype'] == 'row' else (v, u)
                if row in matched_rows:
                    nodes_on_edge.append((row, cell))
                    row_num = int(graph.nodes[row]['value'].replace('row', ''))
                    triples.append((
                        (graph.nodes[row]['value'], d['etype'], graph.nodes[cell]['value']),
                        row_num,
                        d.get('eindex', float('-inf'))
                    ))

            if nodes_on_edge:
                subgraph = graph.edge_subgraph(nodes_on_edge).copy()
                triples.sort(key=lambda x: (x[1], x[2]))
                return subgraph, [t[0] for t in triples], 'success'
            else:
                return graph, self.get_triples(graph), 'nodes is null'

        except Exception as e:
            return graph, self.get_triples(graph), 'execute error'


    def filter_by_numeric(self, graph, column_set, column, compare, condition):
        """
        :param graph: current graph state, usually the subgraph; class: python networkx graph
        :param column_set: column set of the table; list: a list of string column name
        :param column: column (edge) to select; string: the column name
        :param compare: '>', '<', '>=', '<=', '==', '!='; string: the relation operator
        :param condition: the threshold value; string: the numeric string
        :return: subgraph, filtered_triples, success
        """
        rels = {
            '>': lambda a, b: a > b,
            '<': lambda a, b: a < b,
            '>=': lambda a, b: a >= b,
            '<=': lambda a, b: a <= b,
            '==': lambda a, b: a == b,
            '!=': lambda a, b: a != b
        }

        if column not in column_set:
            return graph, self.get_triples(graph), 'Column {} is not in column set'.format(column)
        elif compare not in rels:
            return graph, self.get_triples(graph), 'Compare {} is not in relation set'.format(compare)

        try:

            def _parse_numeric(v):
                match = re.search(r'-?\d+\.?\d*', str(v).replace(',', ''))
                return float(match.group()) if match else float('-inf')

            target_threshold = _parse_numeric(condition)
            compare_func = rels[compare]
            if target_threshold is None:
                return graph, self.get_triples(graph), 'Targeted threshold {} is null'.format(target_threshold)

            matched_rows = set()
            for u, v, d in graph.edges(data=True):
                if d.get('etype') == column:

                    cell_node = v if graph.nodes[u]['ntype'] == 'row' else u
                    cell_val_num = _parse_numeric(graph.nodes[cell_node].get('value'))


                    if cell_val_num is not None and compare_func(cell_val_num, target_threshold):
                        matched_rows.add(u if cell_node == v else v)


            triples = []
            nodes_on_edge = []
            for u, v, d in graph.edges(data=True):
                if graph.nodes[u]['ntype'] == 'meta' or graph.nodes[v]['ntype'] == 'meta':
                    continue

                row, cell = (u, v) if graph.nodes[u]['ntype'] == 'row' else (v, u)
                if row in matched_rows:
                    nodes_on_edge.append((row, cell))
                    row_num = int(graph.nodes[row]['value'].replace('row', ''))
                    triples.append((
                        (graph.nodes[row]['value'], d['etype'], graph.nodes[cell]['value']),
                        row_num,
                        d.get('eindex', float('-inf'))
                    ))

            if nodes_on_edge:
                triples.sort(key=lambda x: (x[1], x[2]))
                subgraph = graph.edge_subgraph(nodes_on_edge).copy()
                return subgraph, [t[0] for t in triples], 'success'
            else:
                return graph, self.get_triples(graph), 'nodes is null'

        except Exception as e:
            return graph, self.get_triples(graph), 'execute error'



    def group_by(self, graph, column_set, column, order='asce'):
        """
        :param graph: current graph state; class: python networkx graph
        :param column_set: column set of the table; list: a list of string column name
        :param column: column (edge) to select; string: the column name
        :param order: the sorted order; string 'asce' (A-Z/0-9) or 'desc' (Z-A/9-0)
        :return: subgraph, sorted_triples, success
        """
        if column not in column_set:
            return graph, self.get_triples(graph), 'Column {} is not in column set'.format(column)

        try:

            row_group_vals = {}
            for n, attr in graph.nodes(data=True):
                if attr.get('ntype') == 'row':

                    cell_val = next((graph.nodes[nb]['value'] for nb in graph.neighbors(n)
                                     if graph.get_edge_data(n, nb).get('etype') == column), "")
                    row_group_vals[n] = cell_val.lower()


            triples = []
            nodes_on_edge = []
            for u, v, d in graph.edges(data=True):
                if graph.nodes[u]['ntype'] == 'meta' or graph.nodes[v]['ntype'] == 'meta':
                    continue

                row, cell = (u, v) if graph.nodes[u]['ntype'] == 'row' else (v, u)
                row_num = int(graph.nodes[row]['value'].replace('row', ''))

                nodes_on_edge.append((u, v))
                triples.append({
                    'triple': (graph.nodes[row]['value'], d['etype'], graph.nodes[cell]['value']),
                    'group_val': row_group_vals.get(row, ""),
                    'row_num': row_num,
                    'eindex': d.get('eindex', 999)
                })

            if not triples:
                return graph, self.get_triples(graph), 'triples is null'


            rev = (order == 'desc')


            triples.sort(key=lambda x: (
                (0, x['group_val'] if not rev else -x['group_val']) if isinstance(x['group_val'], (int, float))
                else (1, x['group_val'] if not rev else x['group_val'][::-1]),
                x['row_num'],
                x['eindex']
            ))

            results = [item['triple'] for item in triples]
            subgraph = graph.edge_subgraph(nodes_on_edge).copy()

            return subgraph, results, 'success'

        except Exception as e:
            return graph, self.get_triples(graph), 'execute error'



    def sort_by(self, graph, column_set, column, order="desc"):
        """
        :param graph: current graph state, usually the subgraph; class: python networkx graph
        :param column_set: column set of the table; list: a list of string column name
        :param column: column (edge) to select; string: the column name
        :param order: the sorted order; string: 'desc'(for max and top-k) or 'asc'(for min)
        :return: subgraph, sorted_triples, success
        """

        if column not in column_set:
            return graph, self.get_triples(graph), 'Column {} is not in column set'.format(column)

        try:
            def _parse_numeric(v):
                match = re.search(r'-?\d+\.?\d*', str(v).replace(',', ''))
                return float(match.group()) if match else float('-inf')


            row_vals = {}
            for n, attr in graph.nodes(data=True):
                if attr.get('ntype') == 'row':

                    cell_val = next((graph.nodes[nb]['value'] for nb in graph.neighbors(n)
                                     if graph.get_edge_data(n, nb).get('etype') == column), None)
                    row_vals[n] = _parse_numeric(cell_val)


            triples = []

            for u, v, d in graph.edges(data=True):

                if graph.nodes[u]['ntype'] == 'meta' or graph.nodes[v]['ntype'] == 'meta':
                    continue

                row, cell = (u, v) if graph.nodes[u]['ntype'] == 'row' else (v, u)

                row_num = int(graph.nodes[row]['value'].replace('row', ''))

                triples.append((
                    (graph.nodes[row]['value'], d['etype'], graph.nodes[cell]['value']),
                    row_vals.get(row, float('-inf')),
                    row_num,
                    d.get('eindex', float('-inf'))
                ))


            rev = (order == 'desc')
            triples.sort(key=lambda x: (x[1] if not rev else -x[1], x[2], x[3]))

            return graph, [t[0] for t in triples], 'success'

        except Exception as e:

            return graph, self.get_triples(graph), 'execute error'
