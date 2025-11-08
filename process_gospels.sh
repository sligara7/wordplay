#!/bin/bash

# We'll download gospels using curl since we have the URLs
BASE_URL="https://raw.githubusercontent.com/aruljohn/Bible-kjv/master"

for gospel in Matthew Mark Luke John; do
    echo "Processing $gospel..."
    
    # Fetch and extract text from JSON
    curl -s "$BASE_URL/$gospel.json" | \
    python3 -c "
import json, sys
data = json.load(sys.stdin)
verses = [v['text'] for chapter in data['chapters'] for v in chapter['verses']]
print(' '.join(verses))
" > books/gospels/${gospel,,}.txt
    
    echo "Saved books/gospels/${gospel,,}.txt"
done

echo "All gospels downloaded!"
