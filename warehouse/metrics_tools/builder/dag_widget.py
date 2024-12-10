import networkx as nx
from pyvis.network import Network
from ipywidgets import Output, VBox, HTML, interact
from IPython.display import display
import typing as t


def create_dag_widget(dag_dict: t.Dict[str, t.Set[str]]) -> None:
    """
    Create an interactive DAG widget using IPyWidgets and Pyvis.

    Parameters:
        dag_dict (Dict[str, Set[str]]): A dictionary representing the DAG.
                                        Keys are node names, and values are sets of parent node names.
    """
    # Create a directed graph
    G = nx.DiGraph()
    for node, parents in dag_dict.items():
        for parent in parents:
            G.add_edge(parent, node)
        if not parents:  # Add nodes with no parents
            G.add_node(node)

    # Create Pyvis Network
    net = Network(notebook=True, directed=True, cdn_resources="in_line")

    net.from_nx(G)

    # Add click event handlers
    node_html: t.Dict[str, str] = {}
    for node in G.nodes():
        node_html[node] = f"Clicked on node: {node}"
        net.add_node(node, title=f"Click to select {node}")

    # Render to HTML file
    net.show("dag.html")

    # Create widgets for interaction
    output = Output()
    html_view = HTML(value=net.html)
    html_view.layout.height = "500px"

    # Display output on click
    @output.capture(clear_output=True)
    def on_node_click(node: str) -> None:
        if node in node_html:
            print(node_html[node])

    # Interactive handling of clicks
    def handle_node_click(node_name: str) -> None:
        on_node_click(node_name)

    interact(handle_node_click, node_name=list(G.nodes()))

    # Combine the widgets
    display(VBox([html_view, output]))


def create_dag_map_widget(dag_dict: t.Dict[str, t.Set[str]]) -> None:
    """
    Create an interactive DAG widget displayed like a map using Pyvis.

    Parameters:
        dag_dict (Dict[str, Set[str]]): A dictionary representing the DAG.
                                        Keys are node names, and values are sets of parent node names.
    """
    # Create a directed graph
    G = nx.DiGraph()
    for node, parents in dag_dict.items():
        for parent in parents:
            G.add_edge(parent, node)
        if not parents:  # Add nodes with no parents
            G.add_node(node)

    # Create Pyvis Network
    net = Network(height="600px", width="100%", directed=True, cdn_resources="in_line")
    net.from_nx(G)

    # Use physics for map-like layout
    net.set_options(
        """
    var options = {
      "physics": {
        "enabled": true,
        "barnesHut": {
          "gravitationalConstant": -20000,
          "springLength": 150,
          "springConstant": 0.05,
          "damping": 0.1
        }
      },
      "nodes": {
        "shape": "box",
        "font": {
          "size": 16,
          "align": "center"
        },
        "color": {
          "background": "#D2E5FF",
          "border": "#2B7CE9",
          "highlight": {
            "background": "#FFAA55",
            "border": "#FF5722"
          }
        },
        "borderWidth": 2
      },
      "edges": {
        "arrows": {
          "to": {
            "enabled": true
          }
        },
        "color": {
          "color": "#848484",
          "highlight": "#FFAA55"
        },
        "smooth": true
      }
    }
    """
    )

    # Add custom labels and tooltips for nodes
    for node in G.nodes():
        net.add_node(node, label=node, title=f"Node: {node}")

    # Generate and display the HTML for the graph
    net_html = net.generate_html()
    display(HTML(net_html))
