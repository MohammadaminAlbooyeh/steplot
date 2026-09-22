"""Export steplot runs to Mermaid flowcharts and standalone HTML files."""

from __future__ import annotations

from steplot.models import Run, Step, StepStatus

# Color palette per status (Tailwind-ish CSS variables for HTML, hex for Mermaid)
_STATUS_STYLE = {
    StepStatus.SUCCESS: {"fill": "#10b981", "stroke": "#047857", "text": "#fff"},
    StepStatus.FAILED: {"fill": "#ef4444", "stroke": "#991b1b", "text": "#fff"},
    StepStatus.RUNNING: {"fill": "#f59e0b", "stroke": "#b45309", "text": "#fff"},
}


def _escape_mermaid(text: str) -> str:
    """Escape text for safe inclusion in a Mermaid node label."""
    return text.replace('"', "'").replace("\n", " ")


def _step_id(step: Step) -> str:
    """Return a stable Mermaid node id from the step id."""
    return f"N{step.id[:8]}"


def _render_node(step: Step, indent: str = "    ") -> str:
    """Render a single Mermaid node definition."""
    nid = _step_id(step)
    label = _escape_mermaid(step.name)
    style = _STATUS_STYLE.get(step.status, _STATUS_STYLE[StepStatus.RUNNING])
    return (
        f'{indent}{nid}["{label}"]:::s{step.status.value.title()}\n'
        f"{indent}style {nid} fill:{style['fill']},stroke:{style['stroke']},color:{style['text']}"
    )


def _render_edges(step: Step, parent_id: str | None = None) -> str:
    """Render edges connecting this step to its parent and children."""
    lines: list[str] = []
    nid = _step_id(step)
    if parent_id is not None:
        lines.append(f"    {parent_id} --> {nid}")
    for sub in step.children:
        lines.append(_render_edges(sub, parent_id=nid))
    return "\n".join(lines)


def _collect_nodes(step: Step, lines: list[str]) -> None:
    """Recursively collect node definitions."""
    lines.append(_render_node(step))
    for sub in step.children:
        _collect_nodes(sub, lines)


def to_mermaid(run: Run) -> str:
    """Convert a Run to a Mermaid flowchart TD string.

    Example output:
        flowchart TD
            Nabc123["fetch_data"]:::sSuccess
            style Nabc123 fill:#10b981,stroke:#047857,color:#fff
            root --> Nabc123
    """
    lines: list[str] = ["flowchart TD"]
    lines.append(f'    root["Run: {_escape_mermaid(run.name)}"]:::sRun')
    lines.append("    style root fill:#6366f1,stroke:#4338ca,color:#fff")

    node_lines: list[str] = []
    edge_lines: list[str] = []
    for step in run.steps:
        _collect_nodes(step, node_lines)
        edge_lines.append(_render_edges(step, parent_id="root"))

    lines.extend(node_lines)
    if edge_lines:
        lines.append("")
        lines.append("    %% Edges")
        lines.extend(edge_lines)

    # Class definitions
    lines.append("")
    lines.append("    classDef sSuccess fill:#10b981,stroke:#047857,color:#fff")
    lines.append("    classDef sFailed fill:#ef4444,stroke:#991b1b,color:#fff")
    lines.append("    classDef sRunning fill:#f59e0b,stroke:#b45309,color:#fff")
    lines.append("    classDef sRun fill:#6366f1,stroke:#4338ca,color:#fff")

    return "\n".join(lines) + "\n"


def _escape_html(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _build_mermaid_body(run: Run) -> str:
    """Return the Mermaid diagram definition for embedding in HTML."""
    return to_mermaid(run).strip()


def to_html(run: Run, path: str = "steplot.html") -> str:
    """Save a standalone HTML file with an embedded Mermaid diagram.

    The HTML loads mermaid.js from CDN and renders the run as a flowchart.
    Node colors reflect StepStatus.

    Args:
        run: The Run to render.
        path: Output file path.

    Returns:
        The absolute path of the written file.
    """
    import os

    mermaid_body = _build_mermaid_body(run)
    html = _HTML_TEMPLATE.format(
        title=_escape_html(run.name),
        run_id=_escape_html(run.id),
        mermaid=_escape_html(mermaid_body),
    )
    path = os.path.abspath(path)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    return path


_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} — steplot</title>
<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
<style>
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    margin: 2rem;
    background: #f8fafc;
  }}
  h1 {{ color: #1e293b; }}
  .meta {{ color: #64748b; font-size: 0.9rem; margin-bottom: 1rem; }}
  .diagram {{ background: #fff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 1.5rem; }}
</style>
</head>
<body>
  <h1>{title}</h1>
  <div class="meta">Run ID: {run_id}</div>
  <div class="diagram">
    <div class="mermaid">
{mermaid}
    </div>
  </div>
  <script>
    mermaid.initialize({{ startOnLoad: true, theme: 'base', themeVariables: {{ primaryColor: '#6366f1' }} }});
  </script>
</body>
</html>
"""
