import re
import sys
import zipfile
import xml.etree.ElementTree as ET

path = sys.argv[1]
with zipfile.ZipFile(path) as z:
    print("zip_bad=", z.testzip())
    bad = []
    negative = []
    for name in z.namelist():
        if name.endswith(".xml") or name.endswith(".rels"):
            data = z.read(name)
            try:
                ET.fromstring(data)
            except Exception as exc:
                bad.append((name, str(exc)))
            if re.search(rb'\b(?:cx|cy|x|y)="-', data):
                negative.append(name)
    slides = [
        name
        for name in z.namelist()
        if name.startswith("ppt/slides/slide") and name.endswith(".xml")
    ]
    print("xml_bad=", bad)
    print("negative_attrs=", negative)
    print("slides=", len(slides))
