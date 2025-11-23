#!/usr/bin/env python3
"""
Batch Process Books - Generate word graphs for multiple books

Processes multiple text files and generates separate word graphs for each.
Useful for comparing language structure across different books.
"""

import argparse
import json
from pathlib import Path
from word_graph_builder import WordGraphBuilder


def process_book(input_path: Path, output_dir: Path, **kwargs) -> dict:
    """
    Process a single book and generate its word graph

    Args:
        input_path: Path to the text file
        output_dir: Directory to save the graph
        **kwargs: Additional arguments for WordGraphBuilder

    Returns:
        Dictionary with processing results
    """
    # Read the text
    with open(input_path, 'r', encoding='utf-8') as f:
        text = f.read()

    # Get book title from kwargs or use filename
    book_title = kwargs.get('title', input_path.stem)

    # Build the graph
    builder = WordGraphBuilder(
        text=text,
        book_title=book_title,
        min_word_length=kwargs.get('min_length', 2),
        lowercase=not kwargs.get('keep_case', False),
        remove_stopwords=kwargs.get('remove_stopwords', False)
    )

    builder.build_graph()

    # Generate output path
    output_file = output_dir / f"{input_path.stem}_graph.json"
    builder.save_graph(str(output_file))

    return {
        'input_file': str(input_path),
        'output_file': str(output_file),
        'book_title': book_title,
        'num_nodes': len(builder.unique_words),
        'num_edges': sum(len(transitions) for transitions in builder.word_transitions.values()),
        'total_tokens': sum(builder.word_frequencies.values())
    }


def main():
    parser = argparse.ArgumentParser(
        description='Batch process multiple books to generate word graphs'
    )
    parser.add_argument('input_dir', help='Directory containing text files')
    parser.add_argument('-o', '--output-dir', help='Output directory for graphs',
                        default='output/graphs')
    parser.add_argument('-p', '--pattern', default='*.txt',
                        help='File pattern to match (default: *.txt)')
    parser.add_argument('-m', '--min-length', type=int, default=2,
                        help='Minimum word length (default: 2)')
    parser.add_argument('--keep-case', action='store_true',
                        help='Keep original case (default: lowercase all)')
    parser.add_argument('--remove-stopwords', action='store_true',
                        help='Remove common stopwords')

    args = parser.parse_args()

    # Setup paths
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Find all matching files
    files = sorted(input_dir.glob(args.pattern))

    if not files:
        print(f"No files found matching {args.pattern} in {input_dir}")
        return 1

    print(f"Found {len(files)} file(s) to process")
    print(f"Output directory: {output_dir}")
    print()

    results = []

    for i, file_path in enumerate(files, 1):
        print(f"[{i}/{len(files)}] Processing: {file_path.name}")

        try:
            result = process_book(
                file_path,
                output_dir,
                min_length=args.min_length,
                keep_case=args.keep_case,
                remove_stopwords=args.remove_stopwords
            )
            results.append(result)
            print(f"  ✓ Generated graph: {result['num_nodes']} words, {result['num_edges']} transitions")
        except Exception as e:
            print(f"  ✗ Error: {e}")
            results.append({
                'input_file': str(file_path),
                'error': str(e)
            })

        print()

    # Save batch summary
    summary_file = output_dir / 'batch_summary.json'
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump({
            'total_files': len(files),
            'successful': len([r for r in results if 'error' not in r]),
            'failed': len([r for r in results if 'error' in r]),
            'results': results
        }, f, indent=2)

    print(f"Batch summary saved to: {summary_file}")
    print(f"Successfully processed: {len([r for r in results if 'error' not in r])}/{len(files)} files")

    return 0


if __name__ == '__main__':
    exit(main())
