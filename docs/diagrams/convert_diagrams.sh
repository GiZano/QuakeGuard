#!/bin/bash

RAW_DIR="./raw"
OUT_DIR="./sanitized"

mkdir -p "$OUT_DIR"
shopt -s nullglob

for f in "$RAW_DIR"/*.drawio; do
    filename=$(basename "$f" .drawio)
    out_pdf="$OUT_DIR/${filename}.pdf"

    echo "Esportazione in PDF di $filename..."

    # Esporta direttamente in PDF vettoriale tagliando i bordi vuoti (--crop)
    flatpak run --filesystem=host com.jgraph.drawio.desktop -x -f pdf --crop -o "$out_pdf" "$f" 2>/dev/null

    echo "Completato: $out_pdf"
done
