from pyvis.network import Network
import pandas as pd
import tempfile
import os

def build_graph_html(who_df):

    if who_df is None or who_df.empty:
        return "<h4>No plagiarism relationships detected</h4>"

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

    for _, row in who_df.iterrows():
        copier = row["Suspected_Copier"]
        source = row["Likely_Source"]
        sim = float(row["Similarity"])

        net.add_node(copier, label=copier, color="#ef4444")
        net.add_node(source, label=source, color="#3b82f6")
        net.add_edge(copier, source, value=sim, title=f"{sim}% similarity")

    # PyVis requires a temp file even in Cloud
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".html")
    net.write_html(tmp.name)
    tmp.close()

    with open(tmp.name, "r", encoding="utf-8") as f:
        html = f.read()

    os.unlink(tmp.name)

    return html
