#!/bin/bash
output="code_dump.txt"
> "$output"

git ls-files | while read file; do
    if [ -f "$file" ]; then   # Nur wenn Datei existiert
        echo "=== $file ===" >> "$output"
        cat "$file" >> "$output"
        echo -e "\n\n" >> "$output"
    else
        echo "WARN: $file existiert nicht (übersprungen)" >&2
    fi
done