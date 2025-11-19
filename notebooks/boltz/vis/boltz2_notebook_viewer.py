"""
Notebook-friendly Boltz-2 3D viewer using py3Dmol + ipywidgets.

Usage in Jupyter:

    from boltz2_notebook_viewer import view_boltz2
    view_boltz2(["pred_1.pdb", "pred_2.pdb"], title="My complex")

Requires:
    pip install py3Dmol ipywidgets
Enable widgets:
    jupyter nbextension enable --py widgetsnbextension
"""
from pathlib import Path
from ipywidgets import Dropdown, HBox, VBox, ToggleButtons, FloatSlider, Button, HTML, Layout
from IPython.display import display
import py3Dmol

NUC = {'A','U','G','C','DA','DT','DG','DC','I','DI','5MC','PSU'}
AA3 = {"ALA","ARG","ASN","ASP","CYS","GLN","GLU","GLY","HIS","ILE","LEU","LYS","MET","PHE","PRO","SER","THR","TRP","TYR","VAL"}

def _analyze(pdb):
    chains = {}
    for line in pdb.splitlines():
        if not (line.startswith("ATOM") or line.startswith("HETATM")):
            continue
        if len(line) < 22:
            continue
        resn = line[17:20].strip().upper()
        ch = line[21:22]
        d = chains.setdefault(ch, {"aa":0, "nucl":0})
        if resn in AA3:
            d["aa"] += 1
        if resn in NUC:
            d["nucl"] += 1
    t = {}
    for c,d in chains.items():
        t[c] = "RNA" if d["nucl"]>d["aa"] else ("Protein" if d["aa"]>0 else "Other")
    return list(chains.keys()), t

def view_boltz2(pdb_paths, title="Boltz-2 Protein–RNA (py3Dmol)"):
    models = []
    for i, p in enumerate(pdb_paths):
        pt = Path(p)
        pdb = pt.read_text()
        chains, types = _analyze(pdb)
        models.append({"id": i, "name": pt.name, "pdb": pdb, "chains": chains, "types": types})

    viewer = py3Dmol.view(width=900, height=600)
    info = HTML()
    dd_model = Dropdown(options=[(m["name"], m["id"]) for m in models], description="Model:", layout=Layout(width="260px"))
    dd_color = Dropdown(options=[("Chain","chain"),("Secondary","ss"),("B-factor","bfactor")], description="Color:", layout=Layout(width="220px"))
    tb_from = Dropdown(options=models[0]["chains"], description="From:", layout=Layout(width="160px"))
    tb_to   = Dropdown(options=models[0]["chains"], description="To:", layout=Layout(width="160px"))
    sl_dist = FloatSlider(value=5.0, min=2.0, max=12.0, step=0.5, description="Interface Å:", readout_format=".1f", layout=Layout(width="280px"))
    btn_iface = Button(description="Highlight", tooltip="Highlight interface within Å", layout=Layout(width="120px"))
    btn_reset = Button(description="Reset view", layout=Layout(width="120px"))

    def chain_items(m):
        return [ToggleButtons(options=[("on","on"),("off","off")], value="on", description=f"Chain {c} ({m['types'][c]})", layout=Layout(width="220px")) for c in m["chains"]]

    chain_toggles = chain_items(models[0])

    def set_styles():
        viewer.setStyle({}, {})  # clear
        viewer.setStyle({"resn": list(NUC)}, {"stick": {}})
        scheme = dd_color.value
        if scheme == "chain":
            prot_style = {"cartoon":{"color":"spectrum"}}
        elif scheme == "ss":
            prot_style = {"cartoon":{"arrows":True}}
        else:
            prot_style = {"cartoon":{"colorfunc":"b"}}
        viewer.setStyle({"not":{"resn": list(NUC)}}, prot_style)

        m = next(mm for mm in models if mm["id"]==dd_model.value)
        for tog, c in zip(chain_toggles, m["chains"]):
            if tog.value == "off":
                viewer.setStyle({"chain": c}, {})
        viewer.zoomTo()
        viewer.render()

    def load_model(change=None):
        m = next(mm for mm in models if mm["id"]==dd_model.value)
        viewer.removeAllModels()
        viewer.addModel(m["pdb"], "pdb")
        nonlocal chain_toggles
        chain_toggles = chain_items(m)
        tb_from.options = m["chains"]
        tb_to.options   = m["chains"]
        if len(m["chains"])>1 and tb_to.value == tb_from.value:
            tb_to.value = m["chains"][1]
        info.value = "<b>" + title + "</b> &nbsp; " + " &nbsp; ".join([f"{c}:{m['types'][c]}" for c in m["chains"]])
        set_styles()

    def highlight_iface(_):
        set_styles()
        dist = float(sl_dist.value)
        m = next(mm for mm in models if mm["id"]==dd_model.value)
        fromC, toC = tb_from.value, tb_to.value
        if not fromC or not toC or fromC==toC:
            viewer.render(); return
        viewer.setStyle({"within":{"distance": dist, "sel": {"chain": toC}}, "chain": fromC}, {"stick":{"radius":0.2}})
        viewer.setStyle({"within":{"distance": dist, "sel": {"chain": fromC}}, "chain": toC}, {"stick":{"radius":0.2}})
        viewer.render()

    btn_iface.on_click(highlight_iface)
    btn_reset.on_click(lambda _: (viewer.zoomTo(), viewer.render()))
    dd_model.observe(load_model, names="value")
    dd_color.observe(lambda change: set_styles(), names="value")

    load_model()
    top = HBox([dd_model, dd_color, sl_dist, tb_from, tb_to, btn_iface, btn_reset])
    chains_box = HBox(chain_toggles)
    display(VBox([info, top, chains_box]))
    display(viewer.show())
