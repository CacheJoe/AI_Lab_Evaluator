import pandas as pd
from pyvis.network import Network
import os

def build_graph_html(who_df):
    """
    Builds a stable, non-wiggling plagiarism similarity network.

    Expected schema of who_df:
    - Student_1
    - Student_2
    - Similarity (percentage, numeric)
    - Risk_Level (Suspicious | High Risk | Near Duplicate)

    Returns:
    - HTML string for Streamlit embedding
    """

    # -----------------------------------------
    # Guard conditions
    # -----------------------------------------
    if who_df is None or who_df.empty:
        return None

    # -----------------------------------------
    # Ensure output directory exists (Cloud-safe)
    # -----------------------------------------
    os.makedirs("reports", exist_ok=True)

    # -----------------------------------------
    # Create network (undirected similarity)
    # -----------------------------------------
    net = Network(
        height="700px",
        width="100%",
        bgcolor="#ffffff",
        font_color="black",
        directed=False
    )

    # -----------------------------------------
    # Stable physics configuration
    # -----------------------------------------
    net.set_options("""
    {
      "nodes": {
        "shape": "dot",
        "size": 16,
        "font": { "size": 14 }
      },
      "edges": {
        "font": { "size": 12 },
        "smooth": true
      },
      "physics": {
        "enabled": true,
        "barnesHut": {
          "gravitationalConstant": -3000,
          "springLength": 120,
          "springConstant": 0.04
        },
        "stabilization": {
          "enabled": true,
          "iterations": 300,
          "fit": true
        }
      },
      "interaction": {
        "hover": true,
        "tooltipDelay": 200
      }
    }
    """)

    # -----------------------------------------
    # Add nodes & edges (NEW schema)
    # -----------------------------------------
    for _, row in who_df.iterrows():
        a = row["Student_1"]
        b = row["Student_2"]
        sim = float(row["Similarity"])
        risk = row.get("Risk_Level", "Suspicious")

        # Edge color by risk
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

    # -----------------------------------------
    # Write HTML
    # -----------------------------------------
    output_path = "reports/plagiarism_network.html"
    net.write_html(output_path, notebook=False)

    # -----------------------------------------
    # HARD FREEZE (pyvis-version agnostic)
    # Disable physics AFTER stabilization
    # -----------------------------------------
    with open(output_path, "r", encoding="utf-8") as f:
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

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    return html
