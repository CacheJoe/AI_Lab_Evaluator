import pandas as pd
from pyvis.network import Network
import os

def build_graph_html(who_df):
    """
    Builds a stable plagiarism similarity network
    based on UNIQUE undirected pairs:
    Student_1 <-> Student_2
    """

    if who_df is None or who_df.empty:
        return None

    net = Network(
        height="700px",
        width="100%",
        bgcolor="#ffffff",
        font_color="black",
        directed=False   # similarity is undirected
    )

    # -------------------------------------------------
    # Stable physics (stabilize once, then freeze)
    # -------------------------------------------------
    net.set_options("""
    {
      "nodes": {
        "shape": "dot",
        "size": 16,
        "font": { "size": 14 }
      },
      "edges": {
        "font": { "size": 12 }
      },
      "physics": {
        "enabled": true,
        "barnesHut": {
          "gravitationalConstant": -3000,
          "springLength": 120
        },
        "stabilization": {
          "enabled": true,
          "iterations": 300,
          "fit": true
        }
      }
    }
    """)

    # -------------------------------------------------
    # Add nodes & edges (NEW SCHEMA)
    # -------------------------------------------------
    for _, row in who_df.iterrows():
        a = row["Student_1"]
        b = row["Student_2"]
        sim = float(row["Similarity"])
        risk = row.get("Risk_Level", "Similarity")

        # color by risk
        edge_color = (
            "#dc2626" if risk == "Near Duplicate" else
            "#f59e0b" if risk == "High Risk" else
            "#2563eb"
        )

        net.add_node(a, label=a)
        net.add_node(b, label=b)

        net.add_edge(
            a,
            b,
            value=sim,
            title=f"{risk} – {sim}%",
            color=edge_color
        )

    output = "reports/plagiarism_network.html"
    net.write_html(output, notebook=False)

    # -------------------------------------------------
    # HARD FREEZE via JS (pyvis-version safe)
    # -------------------------------------------------
    with open(output, "r", encoding="utf-8") as f:
        html = f.read()

    html = html.replace(
        "network = new vis.Network(container, data, options);",
        """
        network = new vis.Network(container, data, options);
        network.once("stabilizationIterationsDone", function () {
            network.setOptions({ physics: false });
        });
        """
    )

    with open(output, "w", encoding="utf-8") as f:
        f.write(html)

    return html
