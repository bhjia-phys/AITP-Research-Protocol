#!/usr/bin/env python3
"""Generate an interactive HTML visualization of the AITP L2 knowledge graph.

Usage:
    python scripts/generate_l2_viz.py [--output L2/graph/index.html]

Reads nodes, edges, and towers from L2/graph/ and produces a self-contained
HTML file with an interactive force-directed network graph using vis.js.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# — Domain colors —
DOMAIN_COLORS = {
    "electronic-structure": "#4C72B0",
    "quantum-many-body": "#55A868",
    "qft": "#C44E52",
    "condensed-matter": "#8172B2",
    "quantum-gravity": "#937860",
    "generalized-symmetries": "#DA8BC3",
    "quantum-information": "#8C8C8C",
    "statistical-mechanics": "#CCB974",
    "aitp-protocol": "#64B5CD",
}

NODE_SHAPES = {
    "concept": "dot",
    "theorem": "diamond",
    "technique": "box",
    "derivation_chain": "triangle",
    "result": "star",
    "approximation": "hexagon",
    "open_question": "ellipse",
    "regime_boundary": "square",
}

EDGE_STYLES = {
    "uses": ("solid", False),
    "derives_from": ("solid", True),
    "specializes": ("dashed", True),
    "generalizes": ("dashed", True),
    "approximates": ("dotted", False),
    "limits_to": ("dotted", True),
    "component_of": ("solid", False),
    "equivalent_to": ("double", False),
    "contradicts": ("dashed", False),
    "matches_onto": ("dotted", False),
    "decouples_at": ("dotted", False),
    "emerges_from": ("dashed", True),
    "refines": ("solid", True),
    "motivates": ("dashed", False),
    "proven_by": ("solid", True),
    "assumes": ("dotted", False),
}


def _parse_md(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}, text
    end = text.find("---", 3)
    if end == -1:
        return {}, text
    import yaml
    try:
        fm = yaml.safe_load(text[3:end]) or {}
    except Exception:
        fm = {}
    return fm, text[end + 3:]


def build_graph(l2_root: Path) -> dict:
    nodes_dir = l2_root / "graph" / "nodes"
    edges_dir = l2_root / "graph" / "edges"
    towers_dir = l2_root / "graph" / "towers"

    nodes = []
    edges = []
    node_ids = set()

    if nodes_dir.is_dir():
        for f in sorted(nodes_dir.glob("*.md")):
            fm, _ = _parse_md(f)
            nid = fm.get("node_id", f.stem)
            node_ids.add(nid)
            domain = fm.get("domain", "")
            nodes.append({
                "id": nid,
                "label": fm.get("title", nid),
                "type": fm.get("type", "concept"),
                "domain": domain,
                "color": DOMAIN_COLORS.get(domain, "#999999"),
                "shape": NODE_SHAPES.get(fm.get("type", "concept"), "dot"),
                "trust": fm.get("trust_basis", ""),
                "expression": fm.get("mathematical_expression", ""),
                "meaning": fm.get("physical_meaning", ""),
                "regime": fm.get("regime_of_validity", ""),
                "source": fm.get("source_candidate", fm.get("source_ref", "")),
                "energy": fm.get("energy_scale", ""),
                "version": fm.get("version", 1),
            })

    valid_edges = []
    if edges_dir.is_dir():
        for f in sorted(edges_dir.glob("*.md")):
            fm, body = _parse_md(f)
            eid = fm.get("edge_id", f.stem)
            frm = fm.get("from_node", "")
            to = fm.get("to_node", "")
            etype = fm.get("type", "uses")
            evidence = fm.get("evidence", "")
            source = fm.get("source_ref", "")
            style, arrows = EDGE_STYLES.get(etype, ("solid", False))
            edge = {
                "id": eid,
                "from": frm,
                "to": to,
                "type": etype,
                "label": etype,
                "evidence": evidence,
                "source": source,
                "dashes": (style == "dashed"),
                "arrows": "to" if arrows else "",
            }
            # Only include if both nodes exist
            if frm in node_ids and to in node_ids:
                valid_edges.append(edge)

    towers = []
    if towers_dir.is_dir():
        for f in sorted(towers_dir.glob("*.md")):
            fm, body = _parse_md(f)
            towers.append({
                "name": fm.get("name", f.stem),
                "energy_range": fm.get("energy_range", ""),
                "layers": fm.get("layers", []),
            })

    return {"nodes": nodes, "edges": valid_edges, "towers": towers}


def generate_html(graph: dict, output_path: Path) -> None:
    nodes_json = json.dumps(graph["nodes"], ensure_ascii=False)
    edges_json = json.dumps(graph["edges"], ensure_ascii=False)
    towers_json = json.dumps(graph["towers"], ensure_ascii=False)
    domains_json = json.dumps(
        {k: v for k, v in DOMAIN_COLORS.items() if any(n["domain"] == k for n in graph["nodes"])},
        ensure_ascii=False,
    )

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AITP L2 Knowledge Graph</title>
<script src="https://unpkg.com/vis-network@9.1.6/dist/vis-network.min.js"></script>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
<script src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js"></script>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #1a1a2e; color: #e0e0e0; display: flex; height: 100vh; }}
#graph {{ flex: 1; }}
#sidebar {{ width: 380px; background: #16213e; padding: 20px; overflow-y: auto; border-left: 1px solid #0f3460; }}
#sidebar h2 {{ color: #e94560; margin-bottom: 8px; font-size: 16px; }}
#sidebar .field {{ margin-bottom: 12px; }}
#sidebar .field-label {{ color: #888; font-size: 11px; text-transform: uppercase; letter-spacing: 1px; }}
#sidebar .field-value {{ color: #e0e0e0; font-size: 14px; line-height: 1.5; }}
#sidebar .expression {{ background: #1a1a2e; padding: 8px 12px; border-radius: 4px; font-family: 'Courier New', monospace; font-size: 13px; color: #4C72B0; overflow-x: auto; }}
#header {{ position: absolute; top: 12px; left: 20px; z-index: 10; }}
#header h1 {{ font-size: 20px; color: #e94560; }}
#header .stats {{ font-size: 12px; color: #888; margin-top: 4px; }}
#legend {{ position: absolute; bottom: 12px; left: 20px; z-index: 10; display: flex; flex-wrap: wrap; gap: 8px; max-width: calc(100% - 420px); }}
.legend-item {{ display: flex; align-items: center; gap: 4px; font-size: 11px; color: #aaa; }}
.legend-dot {{ width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }}
#filter-bar {{ position: absolute; top: 12px; right: 400px; z-index: 10; display: flex; gap: 6px; }}
#filter-bar button {{ padding: 3px 10px; border: 1px solid #0f3460; border-radius: 3px; cursor: pointer; font-size: 11px; }}
#filter-bar button.active {{ background: #e94560; color: white; border-color: #e94560; }}
#filter-bar button {{ background: #16213e; color: #aaa; }}
#no-selection {{ color: #666; font-style: italic; margin-top: 40px; text-align: center; }}
#tower-section {{ margin-top: 20px; border-top: 1px solid #0f3460; padding-top: 16px; }}
.tower-layer {{ background: #1a1a2e; padding: 6px 10px; margin: 4px 0; border-radius: 4px; font-size: 12px; border-left: 3px solid #e94560; }}
</style>
</head>
<body>

<div id="graph"></div>

<div id="header">
  <h1>AITP L2 Knowledge Graph</h1>
  <div class="stats" id="stats"></div>
</div>

<div id="filter-bar"></div>

<div id="legend"></div>

<div id="sidebar">
  <div id="no-selection">Click a node to see details</div>
  <div id="node-detail" style="display:none;">
    <h2 id="detail-title"></h2>
    <div class="field"><div class="field-label">Type</div><div class="field-value" id="detail-type"></div></div>
    <div class="field"><div class="field-label">Domain</div><div class="field-value" id="detail-domain"></div></div>
    <div class="field"><div class="field-label">Trust</div><div class="field-value" id="detail-trust"></div></div>
    <div class="field"><div class="field-label">Energy Scale</div><div class="field-value" id="detail-energy"></div></div>
    <div class="field"><div class="field-label">Physical Meaning</div><div class="field-value" id="detail-meaning"></div></div>
    <div class="field"><div class="field-label">Mathematical Expression</div><div class="expression" id="detail-expr"></div></div>
    <div class="field"><div class="field-label">Regime of Validity</div><div class="field-value" id="detail-regime"></div></div>
    <div class="field"><div class="field-label">Source</div><div class="field-value" id="detail-source" style="font-size:12px;color:#888;"></div></div>
  </div>
  <div id="tower-section"></div>
</div>

<script>
var nodes = new vis.DataSet({nodes_json});
var edges = new vis.DataSet({edges_json});
var towers = {towers_json};
var domains = {domains_json};

document.getElementById('stats').textContent =
  nodes.length + ' nodes · ' + edges.length + ' edges · ' +
  Object.keys(domains).length + ' domains · ' + towers.length + ' towers';

// Legend
var legend = document.getElementById('legend');
Object.entries(domains).forEach(([d, c]) => {{
  var item = document.createElement('span');
  item.className = 'legend-item';
  item.innerHTML = '<span class="legend-dot" style="background:' + c + '"></span>' + d;
  legend.appendChild(item);
}});

// Domain filter buttons
var filterBar = document.getElementById('filter-bar');
var allBtn = document.createElement('button');
allBtn.textContent = 'All';
allBtn.className = 'active';
allBtn.onclick = function() {{ resetFilter(); }};
filterBar.appendChild(allBtn);
Object.keys(domains).forEach(function(d) {{
  var btn = document.createElement('button');
  btn.textContent = d;
  btn.onclick = function() {{ filterDomain(d); }};
  filterBar.appendChild(btn);
}});

var container = document.getElementById('graph');
var network = new vis.Network(container, {{nodes: nodes, edges: edges}}, {{
  physics: {{ solver: 'forceAtlas2Based', forceAtlas2Based: {{ gravitationalConstant: -40, centralGravity: 0.005, springLength: 150, springConstant: 0.08 }} }},
  nodes: {{ font: {{ color: '#ccc', size: 13 }}, borderWidth: 1.5 }},
  edges: {{ color: {{ color: '#555', highlight: '#e94560', hover: '#888' }}, smooth: {{ type: 'continuous' }}, font: {{ color: '#666', size: 9, strokeWidth: 0 }} }},
  interaction: {{ hover: true, tooltipDelay: 200 }},
}});

network.on('click', function(params) {{
  if (params.nodes.length > 0) {{
    var nid = params.nodes[0];
    var node = nodes.get(nid);
    if (!node) return;
    document.getElementById('no-selection').style.display = 'none';
    document.getElementById('node-detail').style.display = 'block';
    document.getElementById('detail-title').textContent = node.label;
    document.getElementById('detail-type').innerHTML = '<span style="color:' + node.color + '">' + node.type + '</span>';
    document.getElementById('detail-domain').textContent = node.domain;
    document.getElementById('detail-trust').textContent = node.trust + ' / ' + 'v' + node.version;
    document.getElementById('detail-energy').textContent = node.energy || '—';
    document.getElementById('detail-meaning').textContent = node.meaning || '—';
    var exprEl = document.getElementById('detail-expr');
    var raw = node.expression || '—';
    // Wrap LaTeX in $$ if it contains math but no delimiters
    if (raw !== '—' && raw.indexOf('$$') === -1 && raw.indexOf('\\\\') >= 0) {{
      raw = '$$' + raw + '$$';
    }}
    exprEl.textContent = raw;
    if (raw !== '—') {{
      renderMathInElement(exprEl, {{ throwOnError: false }});
    }}
    document.getElementById('detail-regime').textContent = node.regime || '—';
    document.getElementById('detail-source').textContent = node.source || '—';

    // Connected edges
    var connected = edges.get({{filter: function(e) {{ return e.from === nid || e.to === nid; }}}});
    var edgeList = connected.map(function(e) {{
      var dir = e.from === nid ? '→' : '←';
      var other = e.from === nid ? e.to : e.from;
      return '<div style="font-size:12px;margin:4px 0;color:#888;">' + dir + ' <b style="color:#aaa">' + e.type + '</b> → ' + other + '</div>';
    }});
    if (edgeList.length > 0) {{
      document.getElementById('node-detail').innerHTML +=
        '<div class="field" style="margin-top:16px;border-top:1px solid #0f3460;padding-top:12px;"><div class="field-label">Connections (' + edgeList.length + ')</div>' +
        edgeList.join('') + '</div>';
    }}
    // Render LaTeX in all fields
    renderMathInElement(document.getElementById('node-detail'), {{ throwOnError: false }});
  }}
}});

// Tower visualization
var towerSection = document.getElementById('tower-section');
towers.forEach(function(t) {{
  var div = document.createElement('div');
  div.innerHTML = '<h2>�� ' + t.name + '</h2><div class="field-value" style="font-size:12px;margin-bottom:8px;">' + t.energy_range + '</div>';
  (t.layers || []).forEach(function(l) {{
    div.innerHTML += '<div class="tower-layer"><b>' + (l.energy_scale || '') + '</b>: ' + (l.theories || '') + '</div>';
  }});
  towerSection.appendChild(div);
}});

function filterDomain(domain) {{
  var filtered = nodes.get({{filter: function(n) {{ return n.domain === domain; }}}});
  var ids = filtered.map(function(n) {{ return n.id; }});
  // Also show nodes connected by edges to filtered domain
  var extended = new Set(ids);
  edges.forEach(function(e) {{
    if (ids.indexOf(e.from) >= 0) extended.add(e.to);
    if (ids.indexOf(e.to) >= 0) extended.add(e.from);
  }});
  var allIds = Array.from(extended);
  var shown = nodes.get({{filter: function(n) {{ return allIds.indexOf(n.id) >= 0; }}}});
  var hidden = nodes.get({{filter: function(n) {{ return allIds.indexOf(n.id) < 0; }}}});
  shown.forEach(function(n) {{ nodes.update({{id: n.id, hidden: false}}); }});
  hidden.forEach(function(n) {{ nodes.update({{id: n.id, hidden: true}}); }});
  network.fit();
  // Update button states
  Array.from(document.getElementById('filter-bar').children).forEach(function(b) {{ b.className = ''; }});
  event.target.className = 'active';
}}

function resetFilter() {{
  nodes.forEach(function(n) {{ nodes.update({{id: n.id, hidden: false}}); }});
  network.fit();
  Array.from(document.getElementById('filter-bar').children).forEach(function(b) {{ b.className = ''; }});
  document.getElementById('filter-bar').children[0].className = 'active';
}}
</script>
</body>
</html>'''

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    print(f"Generated {output_path}")
    print(f"  {len(graph['nodes'])} nodes, {len(graph['edges'])} edges, {len(graph['towers'])} towers")


def main():
    repo_root = Path(__file__).resolve().parent.parent
    l2_root = repo_root / "L2"

    if not l2_root.is_dir():
        print(f"L2 directory not found at {l2_root}", file=sys.stderr)
        sys.exit(1)

    output = repo_root / "L2" / "graph" / "index.html"
    if len(sys.argv) > 1 and sys.argv[1] == "--output" and len(sys.argv) > 2:
        output = Path(sys.argv[2])

    graph = build_graph(l2_root)
    generate_html(graph, output)


if __name__ == "__main__":
    main()
