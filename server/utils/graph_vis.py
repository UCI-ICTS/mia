import json
import textwrap
from graphviz import Digraph

data = json.load(open("utils/PMGRC_Consent.json"))
g = Digraph("consent", graph_attr={ "rankdir": "TB", "bgcolor": "white" },
            node_attr={"shape":"box","style":"rounded,filled","fontname":"Calibri", "fontsize":"20"},
            edge_attr={"color":"#444","arrowsize":"0.8"})

def short_text(msgs, maxlen=80):
    for m in msgs or []:
        t = m.strip()
        if t:
            return (t.replace("\n"," ")[:maxlen] + "…") if len(t)>maxlen else t
    return ""

def wrap_text(msgs, width=40):
    """
    Take the first non-empty message, and wrap it
    so Graphviz shows it as multi-line text.
    """
    for m in msgs or []:
        t = m.strip()
        if t:
            return textwrap.fill(t.replace("\n", " "), width=width)
    return ""

for node_id, node in data.items():
    ttype = node.get("type","")
    child_ids = node.get("child_ids","")
    parent_ids = node.get("parent_ids","")
    title = wrap_text(node.get("messages", []), width=30)
    label = f" {title}"
    # label = f"Node ID: {node_id}\
    #      \nparent IDs: {parent_ids}\
    #      \nchild IDs: {child_ids}\
    #     \nMessage: {title}"
        # \n{textwrap.shorten(title, width=70)}"
    labeljust="l"
    attrs = {}
    if ttype == "start":
        attrs = {"shape":"circle", "fillcolor":"#f0f0f0"}
    if ttype =="bot":
        attrs = {
            "fillcolor":"#255799",
            "fontcolor": "#f8cf56"
        }
    if ttype =="user":
        attrs = {
            "fillcolor":"#6aa2b8",
            "fontcolor": "#002244"
        }

    g.node(node_id, label, **attrs)

# Edges from child_ids
for node_id, node in data.items():
    for cid in node.get("child_ids", []) or []:
        g.edge(node_id, cid)

    # Form routing by field id_value
    render = node.get("render",{}) or {}
    if render.get("form_type") == "checkbox_form":
        for f in render.get("fields", []):
            tgt = f.get("id_value")
            if tgt:
                g.edge(node_id, tgt, label=f.get("label",""))
    # Text form submit/skip
    if render.get("form_type") in ("text_fields","contact_other_adult"):
        sub = render.get("submit_node_id")
        skp = render.get("skip_node_id")
        if sub: g.edge(node_id, sub, label="Submit")
        if skp: g.edge(node_id, skp,  label="Skip")

g.render("consent_graph", format="svg")
