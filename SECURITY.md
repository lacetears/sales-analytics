# Data and security notes

The source workbook is public UCI data but may contain customer identifiers; raw data stays ignored under `retail/source/`. Published aggregates omit CustomerID. Use only trusted workbooks; XLSX parsing is not a sandbox. Input errors are classified; monetary ranges are bounded for exact dashboard integers.

The report embeds JSON with `<` escaped and displays product descriptions with textContent. The pipeline does not evaluate spreadsheet formulas (`data_only=True`). No credentials or remote databases are required. Reconciliation validates implementation consistency, not the truth of the source records or accounting compliance. Dependency vulnerability scanning and browser accessibility auditing were not performed.
