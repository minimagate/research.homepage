# Geometry of Meaning archive

A minimal [Zola](https://www.getzola.org/) archive for the Geometry of Meaning research project.

An optimized 736×232 AVIF crop at `static/images/research-header.avif`, taken from the upper portion of the source image, appears above the shared primary navigation.

The archive summarises the research without duplicating its source of truth: every experiment,
dataset, run, and notebook page links to the corresponding file in the
[research repository](https://github.com/minimagate/geometry-of-meaning).

## Local development

```sh
zola serve
```

## Production check

```sh
zola check
zola build
```

## Observation chart pipeline

Observation reports declare their reproducible Plotly exports in
`data/observation-charts/<observation-slug>.json`. Generate the figures in the research
repository first, then import one report's declared charts into `static/charts/`:

```sh
python3 scripts/sync_observation_charts.py --observation <observation-slug>
```

Run the command without `--observation` to validate and sync every report manifest. The sync
rejects missing artifacts, duplicate public filenames, paths outside the research showcase
artifact tree, and HTML that does not contain Plotly output.

Public website of the Geometry of Meaning research.
