import json, csv, pathlib
src = pathlib.Path(r"c:\Users\Apoor\ai-account-coding-engine\ai-account-coding-engine\3_examples\all_Invoice_fields.json")
out = pathlib.Path(r"c:\Users\Apoor\ai-account-coding-engine\ai-account-coding-engine\data\all_items.csv")
data = json.loads(src.read_text(encoding="utf-8"))
rows = []
for fname, doc in data.items():
    items = doc.get("Fields", {}).get("Artikel", []) or []
    for i, it in enumerate(items, start=1):
        rows.append({
            "source_file": fname,
            "index": i,
            "Anzahl": it.get("Anzahl",""),
            "Art-Nr": it.get("Art-Nr",""),
            "Bezeichnung": it.get("Bezeichnung",""),
            "Preis": it.get("Preis",""),
            "Betrag": it.get("Betrag",""),
            "Pos": it.get("Pos","")
        })
with out.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["source_file","index","Anzahl","Art-Nr","Bezeichnung","Preis","Betrag","Pos"])
    writer.writeheader()
    writer.writerows(rows)
print("total_items=", len(rows))