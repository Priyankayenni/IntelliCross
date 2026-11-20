import urllib.request, json

print("=== BACKEND ===")
r = urllib.request.urlopen("http://localhost:8000/")
data = r.read().decode("utf-8")
print("Status: %d" % r.status)
for k, v in json.loads(data).items():
    print("  %s: %s" % (k, v))

print("")
print("=== FRONTEND ===")
r2 = urllib.request.urlopen("http://localhost:5173/")
print("Status: %d" % r2.status)
html = r2.read().decode("utf-8")
print("Has title tag: %s" % ("<title>" in html))
print("Has root div: %s" % ("id=\"root\"" in html))
print("Page size: %d bytes" % len(html))
