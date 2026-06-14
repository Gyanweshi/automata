import os
import re
from pathlib import Path

def patch_file(path):
    with open(path, "r") as f:
        content = f.read()

    # We want to replace:
    # except Exception:
    #     pass
    # With:
    # except Exception as e:
    #     import os
    #     if os.environ.get("AGENCY_DEBUG") == "1":
    #         import logging
    #         logging.getLogger(__name__).error(e, exc_info=True)

    # Let's match any indentation
    # Regex: (^[ \t]*)except Exception:(\s*)pass
    # Note: we also have cases with `except TimeoutError:`, etc.
    
    def replacer(match):
        indent = match.group(1)
        # Using string format to preserve indentation
        return (
            f"{indent}except Exception as e:\n"
            f"{indent}    import os, logging\n"
            f"{indent}    if os.environ.get(\"AGENCY_DEBUG\") == \"1\":\n"
            f"{indent}        logging.getLogger(__name__).error(e, exc_info=True)"
        )
        
    new_content = re.sub(r'(^[ \t]*)except Exception:[\s\n]*pass', replacer, content, flags=re.MULTILINE)
    
    if new_content != content:
        with open(path, "w") as f:
            f.write(new_content)
        print(f"Patched {path}")

for root, dirs, files in os.walk("packages"):
    for file in files:
        if file.endswith(".py"):
            patch_file(os.path.join(root, file))

