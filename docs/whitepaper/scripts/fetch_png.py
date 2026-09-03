import base64
import requests
import os
import glob
import re
import subprocess

def get_mermaid_png_api(mermaid_code, output_path):
    """Render via mermaid.ink API."""
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

def get_plantuml_png(puml_file, output_path):
    """Render PlantUML via local plantuml binary directly to SVG."""
    try:
        with open(puml_file, "r") as f:
            puml_code = f.read()
            
        result = subprocess.run(
            ["plantuml", "-tsvg", "-pipe"],
            input=puml_code.encode("utf-8"),
            capture_output=True, timeout=30
        )
        if result.returncode == 0:
            with open(output_path, "wb") as f:
                f.write(result.stdout)
            print(f"Saved {output_path} (local PlantUML)")
        else:
            print(f"PlantUML failed for {output_path}:")
            print(result.stderr.decode("utf-8"))
    except Exception as e:
        print(f"PlantUML error: {e}")

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
get_mermaid_png_api(ai_code, "assets/08-ai.png")

# Fetch PlantUML diagrams
puml_files = glob.glob("../diagrams/*.puml")
for df in puml_files:
    basename = os.path.basename(df).replace(".puml", "")
    get_plantuml_png(df, f"assets/{basename}.svg")

# Fetch Mermaid diagrams
diagram_files = glob.glob("../diagrams/*.md")
for df in diagram_files:
    basename = os.path.basename(df).replace(".md", "")
    if basename == "README":
        continue
    with open(df, "r") as f:
        content = f.read()
    
    blocks = re.findall(r'```mermaid(.*?)```', content, re.DOTALL)
    if not blocks:
        continue
        
    if len(blocks) == 1:
        get_mermaid_png_api(blocks[0].strip(), f"assets/{basename}.png")
    else:
        for i, block in enumerate(blocks):
            get_mermaid_png_api(block.strip(), f"assets/{basename}_{i+1}.png")
