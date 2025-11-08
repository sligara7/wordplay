#!/bin/bash
# Wordplay Demo - Complete workflow demonstration

echo "=============================================="
echo "WORDPLAY - Language Structure Analysis Demo"
echo "=============================================="
echo ""

# Change to wordplay directory
cd "$(dirname "$0")"

echo "Step 1: Generate word graphs for example books"
echo "----------------------------------------------"
python3 src/batch_process_books.py books/ \
  -o output/graphs \
  --pattern "*.txt" \
  --remove-stopwords

echo ""
echo "Step 2: Analyze Nature book"
echo "----------------------------"
python3 src/analyze_word_graph.py \
  output/graphs/nature_book_graph.json \
  --summary-only

echo ""
echo "Step 3: Analyze Technology book"
echo "--------------------------------"
python3 src/analyze_word_graph.py \
  output/graphs/technology_book_graph.json \
  --summary-only

echo ""
echo "Step 4: Merge Nature + Technology (orthogonal books)"
echo "-----------------------------------------------------"
python3 src/merge_word_graphs.py \
  output/graphs/nature_book_graph.json \
  output/graphs/technology_book_graph.json \
  -o output/merged_demo.json

echo ""
echo "Step 5: Analyze merged graph"
echo "-----------------------------"
python3 src/analyze_word_graph.py \
  output/merged_demo.json \
  --summary-only

echo ""
echo "=============================================="
echo "Demo complete! Check these files:"
echo "  - output/graphs/*.json (individual graphs)"
echo "  - output/merged_demo.json (merged graph)"
echo "  - output/merged_demo_analysis.json (detailed analysis)"
echo "=============================================="
