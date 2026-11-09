"""Fail CI if the committed dashboard differs from its report and template."""
import json
import tempfile
from pathlib import Path
from analyze_retail import BASE, render_dashboard

with tempfile.TemporaryDirectory() as directory:
    target=Path(directory)/'dashboard.html'
    render_dashboard(json.loads((BASE/'output/report.json').read_text()),target)
    if target.read_bytes() != (BASE/'output/dashboard.html').read_bytes():
        raise SystemExit('Dashboard is stale; rerun retail/analyze_retail.py')
print('Retail dashboard matches report and template.')
