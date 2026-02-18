import re, json, sys

in_path = r"d:/TDS/GA Solutions/GA1/Q30/broken.json"
out_path = r"d:/TDS/GA Solutions/GA1/Q30/fixed.json"

t = open(in_path, "r", encoding="utf-8").read()
orig = t

# Fix specific observed issues:
# 1) Extra closing brace before description: replace '}}\n    "description"' -> '},\n    "description"'
t = re.sub(r"}}\n(\s*)\"description\"", r'},\n\1"description"', t)
# Handle case where extra brace is followed by a comma before description
t = re.sub(r"}},\n(\s*)\"description\"", r'},\n\1"description"', t)

# 2) Missing comma between top-level objects: '}' followed by newline and two-space indent and '{' -> '},\n  {'
t = re.sub(r"\}\n(\s{2})\{", r'},\n\1{', t)

# 3) Single-quoted keys -> double-quoted keys (e.g. 'status': -> "status":)
t = re.sub(r"'([A-Za-z_][A-Za-z0-9_]*)'\s*:", r'"\1":', t)

# 4) Single-quoted string values -> double-quoted values (e.g. 'inactive' -> "inactive")
# Only match simple single-quoted values without embedded single quotes
t = re.sub(r":\s*'([^'\\n]*)'", r': "\1"', t)

# 5) Missing quotes around specific key names observed (e.g. category: -> "category":)
# Apply to a handful of likely keys
for key in ("category", "status", "metadata", "description", "timestamp", "name", "id", "value"): 
    t = re.sub(r"\n(\s+)" + key + r"\s*:", r'\n\1"' + key + r'":', t)

# 6) Missing comma after an "id" property when next property starts on following line
t = re.sub(r'("id"\s*:\s*"[^"]+")\n(\s+"name"\s*:)', r'\1,\n\2', t)

# Try parsing
try:
    data = json.loads(t)
except Exception as e:
    print("JSON parse failed after automated fixes:\n", e)
    sys.exit(2)

# Write pretty fixed JSON
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("Fixed JSON written to:", out_path)
