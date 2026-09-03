import base64
import requests
import os
import glob
import re

def get_mermaid_png(mermaid_code, output_path):
    encoded = base64.b64encode(mermaid_code.encode('utf-8')).decode('utf-8')
    url = f"https://mermaid.ink/img/{encoded}?type=png&bgColor=ffffff"
    print(f"Fetching {url}")
    response = requests.get(url)
    if response.status_code == 200:
        with open(output_path, "wb") as f:
            f.write(response.content)
        print(f"Saved {output_path}")
    else:
        print(f"Failed to generate {output_path}: {response.status_code}")

os.makedirs("assets", exist_ok=True)

# Also fetch hardcoded AI flowchart
ai_code = """flowchart LR
    Start(("Alert Triggered"))
    Start --> PENDING["PENDING"]
    PENDING -- "Ollama Processing" --> Split{" "}
    Split -- Success --> COMPLETED["COMPLETED"]
    Split -- Error --> FAILED["FAILED"]
    COMPLETED --> End1(("WebSocket Push"))
    FAILED --> End2(("DLQ Retry"))
    
    style PENDING fill:#fbb,stroke:#333,stroke-width:2px
    style COMPLETED fill:#bfb,stroke:#333,stroke-width:2px
    style FAILED fill:#f9f,stroke:#333,stroke-width:2px
"""
get_mermaid_png(ai_code, "assets/08-ai.png")

# Fetch diagrams from docs/diagrams/
diagram_files = glob.glob("../diagrams/*.md")
for df in diagram_files:
    basename = os.path.basename(df).replace(".md", "")
    if basename == "README":
        continue
    with open(df, "r") as f:
        content = f.read()
    
    match = re.search(r'```mermaid(.*?)```', content, re.DOTALL)
    if match:
        code = match.group(1).strip()
        # For C4 we just need the C4Context or C4Container. 
        # But mermaid.ink handles C4 well if we just pass the block.
        # Actually in c4-context.md there are two mermaid blocks. Let's get both!
        blocks = re.findall(r'```mermaid(.*?)```', content, re.DOTALL)
        if len(blocks) == 1:
            get_mermaid_png(blocks[0].strip(), f"assets/{basename}.png")
        else:
            for i, block in enumerate(blocks):
                get_mermaid_png(block.strip(), f"assets/{basename}_{i+1}.png")
