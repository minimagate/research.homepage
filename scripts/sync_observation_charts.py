#!/usr/bin/env python3
"""Sync declared observation charts from research artifacts into the Zola site."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


SITE_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RESEARCH_ROOT = SITE_ROOT.parent / "geometry-of-meaning"
MANIFEST_DIR = SITE_ROOT / "data" / "observation-charts"
CHART_DIR = SITE_ROOT / "static" / "charts"
PUBLICATION_STYLE = """<style id="gom-publication-style">
/* Match the warm editorial page without muting the chart's restrained palette. */
html,
body {
  margin: 0;
  background: #f6f6ef;
}
</style>"""
HEIGHT_BRIDGE = """<script>
(() => {
  const reportHeight = () => {
    const height = Math.ceil(Math.max(
      document.body.scrollHeight,
      document.body.offsetHeight,
      document.documentElement.scrollHeight,
      document.documentElement.offsetHeight
    ));
    window.parent.postMessage({ type: "gom-plot-height", height }, window.location.origin);
  };
  new ResizeObserver(reportHeight).observe(document.body);
  window.addEventListener("load", reportHeight);
  requestAnimationFrame(() => requestAnimationFrame(reportHeight));
})();
</script>"""


def _load_manifest(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as source:
        value: object = json.load(source)
    if not isinstance(value, dict):
        raise ValueError(f"manifest must contain a JSON object: {path}")
    return value


def _manifest_paths(observation: str | None) -> list[Path]:
    if observation:
        path = MANIFEST_DIR / f"{observation}.json"
        if not path.is_file():
            raise FileNotFoundError(f"observation manifest not found: {path}")
        return [path]
    paths = sorted(MANIFEST_DIR.glob("*.json"))
    if not paths:
        raise FileNotFoundError(f"no observation manifests found below {MANIFEST_DIR}")
    return paths


def sync_manifest(path: Path, research_root: Path, seen_outputs: set[str]) -> list[Path]:
    manifest = _load_manifest(path)
    observation = manifest.get("observation")
    artifact_dir = manifest.get("artifact_dir")
    charts = manifest.get("charts")
    if not isinstance(observation, str) or observation != path.stem:
        raise ValueError(f"observation must equal manifest filename stem in {path}")
    if not isinstance(artifact_dir, str) or Path(artifact_dir).is_absolute():
        raise ValueError(f"artifact_dir must be a relative path in {path}")
    if not isinstance(charts, list) or not charts:
        raise ValueError(f"charts must be a non-empty list in {path}")

    artifact_root = (research_root / artifact_dir).resolve()
    allowed_root = (research_root / "artifacts" / "showcases").resolve()
    if not artifact_root.is_relative_to(allowed_root):
        raise ValueError(f"artifact_dir must remain below {allowed_root}: {path}")

    copied: list[Path] = []
    for chart in charts:
        if not isinstance(chart, dict):
            raise ValueError(f"chart entries must be JSON objects in {path}")
        source_name = chart.get("source")
        output_name = chart.get("output")
        if not isinstance(source_name, str) or Path(source_name).name != source_name:
            raise ValueError(f"chart source must be a filename in {path}")
        if not isinstance(output_name, str) or Path(output_name).name != output_name:
            raise ValueError(f"chart output must be a filename in {path}")
        if not source_name.endswith(".html") or not output_name.endswith(".html"):
            raise ValueError(f"only self-contained Plotly HTML charts are supported in {path}")
        if output_name in seen_outputs:
            raise ValueError(f"duplicate chart output declared: {output_name}")

        source = artifact_root / source_name
        if not source.is_file():
            raise FileNotFoundError(f"declared chart artifact not found: {source}")
        html = source.read_text(encoding="utf-8", errors="strict")
        html = html.replace("\u2014", ",")
        if "plotly" not in html.lower():
            raise ValueError(f"chart does not appear to contain Plotly output: {source}")

        if "</body>" not in html.lower():
            raise ValueError(f"chart HTML has no closing body element: {source}")
        if "id=\"gom-publication-style\"" in html:
            raise ValueError(f"chart already contains the publication style: {source}")
        closing_head = html.lower().rfind("</head>")
        if closing_head == -1:
            raise ValueError(f"chart HTML has no closing head element: {source}")
        html = html[:closing_head] + PUBLICATION_STYLE + html[closing_head:]
        closing_body = html.lower().rfind("</body>")
        html = html[:closing_body] + HEIGHT_BRIDGE + html[closing_body:]

        destination = CHART_DIR / output_name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(html, encoding="utf-8")
        seen_outputs.add(output_name)
        copied.append(destination)
    return copied


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--observation", help="Sync one observation manifest by slug")
    parser.add_argument(
        "--research-root",
        type=Path,
        default=DEFAULT_RESEARCH_ROOT,
        help="Path to the geometry-of-meaning research repository",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    research_root = args.research_root.resolve()
    seen_outputs: set[str] = set()
    copied: list[Path] = []
    for path in _manifest_paths(args.observation):
        copied.extend(sync_manifest(path, research_root, seen_outputs))
    for path in copied:
        print(path.relative_to(SITE_ROOT))


if __name__ == "__main__":
    main()
