"""Download the original CC BY 4.0 workbook from UCI, without credentials."""

from pathlib import Path
from urllib.request import urlopen
from zipfile import ZipFile
from io import BytesIO

url = "https://archive.ics.uci.edu/static/public/352/online+retail.zip"
target = Path(__file__).parent / "source"
target.mkdir(exist_ok=True)
with urlopen(url, timeout=60) as response:
    archive = ZipFile(BytesIO(response.read()))
    (target / "Online Retail.xlsx").write_bytes(archive.read("Online Retail.xlsx"))
print(target / "Online Retail.xlsx")
