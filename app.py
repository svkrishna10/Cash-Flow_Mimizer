import io
from flask import Flask, render_template, request, Response
import heapq
from collections import defaultdict
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

app = Flask(__name__)

class SplitwiseUI:
    def __init__(self):
        self.transactions = []
        self.net_amounts = defaultdict(float)
        self.graph = nx.DiGraph()
        self.minimized_graph = nx.DiGraph()
        self.fig = plt.figure(figsize=(10, 4))
        self.ax1 = self.fig.add_subplot(211)
        self.ax2 = self.fig.add_subplot(212)

    def add_transaction(self, payer, amount, payee):
        self.transactions.append((payer, payee, amount))
        self.net_amounts[payer] -= amount
        self.net_amounts[payee] += amount

    def build_graph(self):
        print("transactions")
        print(self.transactions)
        for payer, payee, amount in self.transactions:
            self.graph.add_edge(payer, payee, weight=amount)

    def calculate_cash_flow(self):
        self.build_graph()
        cashflow = []
        elements = set()
        for tup in self.transactions:
            elements.add(tup[0])
            elements.add(tup[1])

        # Create a dictionary to map elements to their indices
        element_indices = {element: index for index, element in enumerate(elements)}
        
        people = list(elements)
        # Initialize the result list with zeros
        graph = [[0] * len(elements) for _ in range(len(elements))]

        # Populate the result list with the values from the input tuples
        for tup in self.transactions:
            payer_index = element_indices[tup[0]]
            payee_index = element_indices[tup[1]]
            amount = tup[2]
            graph[payer_index][payee_index] = amount

        
        n = len(graph)
        amt = [0] * n
        for p in range(n):
            for i in range(n):
                amt[p] += graph[i][p] - graph[p][i]

        pq = []
        for i in range(n):
            heapq.heappush(pq, (amt[i], i))

        print("initial pq:", pq)

        while pq:
            max_debtor_amt, max_debtor = heapq.heappop(pq)
            print("pq after first pop",pq)
            min_creditor_amt, min_creditor = heapq.heappop(pq)
            print("pq after ssecond pop", pq)

            if max_debtor_amt == 0 and min_creditor_amt == 0:
                break

            min_value = min(-max_debtor_amt, min_creditor_amt)
            max_debtor_amt += min_value
            min_creditor_amt -= min_value

            cashflow.append((people[max_debtor],min_value,people[min_creditor]))

            if max_debtor_amt != 0:
                heapq.heappush(pq, (max_debtor_amt, max_debtor))
            if min_creditor_amt != 0:
                heapq.heappush(pq, (min_creditor_amt, min_creditor))

        print("cashflow")
        print(cashflow) 
        self.build_minimized_graph(cashflow)       
        return cashflow

    def build_minimized_graph(self, cash_flow):
        for transaction in cash_flow:
            payer, amount, payee = transaction
            self.minimized_graph.add_edge(payer, payee, weight=amount)

    def plot_graph(self):
        pos1 = nx.spring_layout(self.graph)
        pos2 = nx.spring_layout(self.minimized_graph)

        edge_labels1 = nx.get_edge_attributes(self.graph, 'weight')
        edge_labels2 = nx.get_edge_attributes(self.minimized_graph, 'weight')

        self.ax1.clear()
        self.ax2.clear()

        # Main Graph
        nx.draw_networkx(self.graph, pos1, with_labels=True, node_color='lightblue', node_size=300, font_size=10,
                         arrows=True, ax=self.ax1)
        nx.draw_networkx_edge_labels(self.graph, pos1, edge_labels=edge_labels1, font_size=8, ax=self.ax1)
        self.ax1.set_title('Given Transaction Graph')
        self.ax1.axis('off')

        # Minimized Graph
        nx.draw_networkx(self.minimized_graph, pos2, with_labels=True, node_color='lightblue', node_size=300,
                         font_size=10, arrows=True, ax=self.ax2)
        nx.draw_networkx_edge_labels(self.minimized_graph, pos2, edge_labels=edge_labels2, font_size=8, ax=self.ax2)
        self.ax2.set_title('Minimized Transaction Graph')
        self.ax2.axis('off')

    def clear_data(self):
        self.transactions = []
        self.net_amounts.clear()
        self.graph.clear()
        self.minimized_graph.clear()

splitwise_ui = SplitwiseUI()

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        payer = request.form['payer']
        amount = float(request.form['amount'])
        payee = request.form['payee']
        splitwise_ui.add_transaction(payer, amount, payee)
        return render_template('index.html', message="Transaction added successfully.")
    else:
        return render_template('index.html')

@app.route('/calculate', methods=['GET'])
def calculate():
    cash_flow = splitwise_ui.calculate_cash_flow()
    return render_template('result.html', cash_flow=cash_flow)

@app.route('/plot_graph', methods=['GET'])
def plot_graph():
    splitwise_ui.plot_graph()
    canvas = FigureCanvas(splitwise_ui.fig)
    output = io.BytesIO()
    canvas.print_png(output)
    return Response(output.getvalue(), mimetype='image/png')

if __name__ == '__main__':
    app.run(debug=True)
