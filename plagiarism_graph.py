import pandas as pd
from pyvis.network import Network
import os

def build_graph(csv_file):
    if not os.path.exists(csv_file):
        print("❌ who_copied_from_whom.csv not found")
        return

    df = pd.read_csv(csv_file)

    if df.empty:
        print("⚠️ No plagiarism pairs found")
        return

    net = Network(
        height="700px",
        width="100%",
        bgcolor="#ffffff",
        font_color="black",
        directed=True
    )

    net.set_options("""
    {
      "nodes": {
        "shape": "dot",
        "size": 16,
        "font": { "size": 14 }
      },
      "edges": {
        "arrows": { "to": { "enabled": true } },
        "font": { "size": 12 }
      },
      "physics": {
        "barnesHut": {
          "gravitationalConstant": -3000,
          "springLength": 120
        }
      }
    }
    """)

    for _, row in df.iterrows():
        copier = row["Suspected_Copier"]
        source = row["Likely_Source"]
        sim = float(row["Similarity"])

        net.add_node(copier, label=copier, color="#ef4444")   # red
        net.add_node(source, label=source, color="#3b82f6")  # blue

        net.add_edge(copier, source, value=sim, title=f"{sim}% similarity")

    output = "reports/plagiarism_network.html"

    net.write_html(output, notebook=False)   # CRITICAL FIX
    print("✅ Plagiarism network written to", output)
