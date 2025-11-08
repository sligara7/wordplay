#!/usr/bin/env python3
"""
Hybrid Tokenizer - Synchronize lyrics with MIDI melodies.

This module creates unified graphs that combine textual and musical information,
allowing analysis of how words and notes interact in songs.
"""

import argparse
import json
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class SyncToken:
    """A synchronized word-note pair."""
    word: str
    note: str
    timestamp: float

    def to_hybrid_token(self) -> str:
        """Create a hybrid token combining word and note."""
        return f"{self.word}-{self.note}"

    def to_word_token(self) -> str:
        """Extract just the word."""
        return self.word

    def to_note_token(self) -> str:
        """Extract just the note."""
        return self.note


class HybridTokenizer:
    """
    Tokenize songs with both lyrics and melody into synchronized sequences.

    Supports multiple tokenization strategies:
    - 'hybrid': Combined word-note tokens (e.g., "love-C4")
    - 'parallel': Separate word and note sequences
    - 'layered': Graph with both types of nodes and cross-layer edges
    """

    def __init__(self, mode='hybrid'):
        """
        Initialize the hybrid tokenizer.

        Args:
            mode: Tokenization mode
                - 'hybrid': Single sequence of word-note pairs
                - 'parallel': Two aligned sequences
                - 'layered': Graph with word and note nodes
        """
        self.mode = mode
        self.sync_tokens: List[SyncToken] = []

    def load_from_aligned_file(self, file_path: str) -> List[SyncToken]:
        """
        Load lyrics and notes from a pre-aligned file.

        File format (JSON):
        {
            "title": "Song Title",
            "aligned_tokens": [
                {"word": "twinkle", "note": "C4", "timestamp": 0.0},
                {"word": "twinkle", "note": "C4", "timestamp": 0.5},
                ...
            ]
        }

        Args:
            file_path: Path to aligned JSON file

        Returns:
            List of SyncToken objects
        """
        with open(file_path, 'r') as f:
            data = json.load(f)

        tokens = []
        for item in data.get('aligned_tokens', []):
            token = SyncToken(
                word=item['word'],
                note=item['note'],
                timestamp=item.get('timestamp', 0.0)
            )
            tokens.append(token)

        self.sync_tokens = tokens
        return tokens

    def load_from_simple_format(self, file_path: str) -> List[SyncToken]:
        """
        Load from a simple text format (one word-note pair per line).

        File format:
        twinkle C4
        twinkle C4
        little G4
        star G4

        Args:
            file_path: Path to simple text file

        Returns:
            List of SyncToken objects
        """
        tokens = []
        timestamp = 0.0

        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                parts = line.split()
                if len(parts) >= 2:
                    word = parts[0].lower()
                    note = parts[1]

                    token = SyncToken(
                        word=word,
                        note=note,
                        timestamp=timestamp
                    )
                    tokens.append(token)
                    timestamp += 1.0

        self.sync_tokens = tokens
        return tokens

    def align_lyrics_and_midi(self,
                             lyrics: List[str],
                             notes: List[str],
                             alignment: Optional[List[Tuple[int, int]]] = None) -> List[SyncToken]:
        """
        Align lyrics and MIDI notes into synchronized tokens.

        Args:
            lyrics: List of words
            notes: List of note names
            alignment: Optional list of (word_idx, note_idx) pairs.
                      If None, assumes 1:1 alignment.

        Returns:
            List of SyncToken objects
        """
        tokens = []

        if alignment is None:
            # Simple 1:1 alignment (truncate to shorter length)
            for i, (word, note) in enumerate(zip(lyrics, notes)):
                token = SyncToken(
                    word=word.lower(),
                    note=note,
                    timestamp=float(i)
                )
                tokens.append(token)
        else:
            # Custom alignment
            for i, (word_idx, note_idx) in enumerate(alignment):
                if word_idx < len(lyrics) and note_idx < len(notes):
                    token = SyncToken(
                        word=lyrics[word_idx].lower(),
                        note=notes[note_idx],
                        timestamp=float(i)
                    )
                    tokens.append(token)

        self.sync_tokens = tokens
        return tokens

    def tokenize_hybrid(self) -> List[str]:
        """
        Create hybrid tokens combining word and note.

        Returns:
            List of hybrid tokens (e.g., ["love-C4", "me-D4", ...])
        """
        return [token.to_hybrid_token() for token in self.sync_tokens]

    def tokenize_parallel(self) -> Tuple[List[str], List[str]]:
        """
        Create parallel word and note sequences.

        Returns:
            Tuple of (word_tokens, note_tokens)
        """
        words = [token.to_word_token() for token in self.sync_tokens]
        notes = [token.to_note_token() for token in self.sync_tokens]
        return words, notes

    def tokenize(self) -> Dict:
        """
        Tokenize according to the selected mode.

        Returns:
            Dictionary with tokenization results based on mode
        """
        if self.mode == 'hybrid':
            return {
                'type': 'hybrid',
                'tokens': self.tokenize_hybrid()
            }
        elif self.mode == 'parallel':
            words, notes = self.tokenize_parallel()
            return {
                'type': 'parallel',
                'word_tokens': words,
                'note_tokens': notes
            }
        elif self.mode == 'layered':
            words, notes = self.tokenize_parallel()
            hybrids = self.tokenize_hybrid()
            return {
                'type': 'layered',
                'word_tokens': words,
                'note_tokens': notes,
                'hybrid_tokens': hybrids,
                'sync_tokens': self.sync_tokens
            }
        else:
            raise ValueError(f"Unknown mode: {self.mode}")

    def get_statistics(self) -> Dict:
        """Get statistics about the synchronized tokens."""
        if not self.sync_tokens:
            return {}

        words = [t.word for t in self.sync_tokens]
        notes = [t.note for t in self.sync_tokens]
        hybrids = [t.to_hybrid_token() for t in self.sync_tokens]

        from collections import Counter
        word_counts = Counter(words)
        note_counts = Counter(notes)
        hybrid_counts = Counter(hybrids)

        # Find word-note associations
        word_note_map = {}
        for token in self.sync_tokens:
            if token.word not in word_note_map:
                word_note_map[token.word] = []
            word_note_map[token.word].append(token.note)

        return {
            'total_tokens': len(self.sync_tokens),
            'unique_words': len(word_counts),
            'unique_notes': len(note_counts),
            'unique_hybrids': len(hybrid_counts),
            'most_common_words': word_counts.most_common(10),
            'most_common_notes': note_counts.most_common(10),
            'most_common_hybrids': hybrid_counts.most_common(10),
            'word_note_associations': {
                word: list(set(notes_list))
                for word, notes_list in word_note_map.items()
            }
        }

    def export_for_graph_builder(self, output_path: str):
        """
        Export tokenized data for graph building.

        Args:
            output_path: Base path for output files
        """
        output_path = Path(output_path)
        result = self.tokenize()

        if result['type'] == 'hybrid':
            # Single file with hybrid tokens
            text = ' '.join(result['tokens'])
            with open(output_path, 'w') as f:
                f.write(text)
            print(f"Exported hybrid tokens to {output_path}")

        elif result['type'] == 'parallel':
            # Two separate files
            words_path = output_path.parent / f"{output_path.stem}_words.txt"
            notes_path = output_path.parent / f"{output_path.stem}_notes.txt"

            with open(words_path, 'w') as f:
                f.write(' '.join(result['word_tokens']))

            with open(notes_path, 'w') as f:
                f.write(' '.join(result['note_tokens']))

            print(f"Exported word tokens to {words_path}")
            print(f"Exported note tokens to {notes_path}")

        elif result['type'] == 'layered':
            # All three formats
            hybrid_path = output_path.parent / f"{output_path.stem}_hybrid.txt"
            words_path = output_path.parent / f"{output_path.stem}_words.txt"
            notes_path = output_path.parent / f"{output_path.stem}_notes.txt"

            with open(hybrid_path, 'w') as f:
                f.write(' '.join(result['hybrid_tokens']))

            with open(words_path, 'w') as f:
                f.write(' '.join(result['word_tokens']))

            with open(notes_path, 'w') as f:
                f.write(' '.join(result['note_tokens']))

            print(f"Exported hybrid tokens to {hybrid_path}")
            print(f"Exported word tokens to {words_path}")
            print(f"Exported note tokens to {notes_path}")


def main():
    parser = argparse.ArgumentParser(
        description='Synchronize lyrics and MIDI into hybrid tokens',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Load from simple format
  python3 src/hybrid_tokenizer.py songs/twinkle_aligned.txt -o songs/twinkle_hybrid.txt

  # Load from JSON format
  python3 src/hybrid_tokenizer.py songs/song.json -o songs/song_hybrid.txt --format json

  # Create parallel sequences
  python3 src/hybrid_tokenizer.py songs/song.txt -o songs/song_tokens.txt -m parallel

  # Create layered graph (all formats)
  python3 src/hybrid_tokenizer.py songs/song.txt -o songs/song_tokens.txt -m layered
        """
    )

    parser.add_argument('input_file', help='Path to aligned lyrics+notes file')
    parser.add_argument('-o', '--output', required=True, help='Output file path')
    parser.add_argument(
        '-m', '--mode',
        choices=['hybrid', 'parallel', 'layered'],
        default='hybrid',
        help='Tokenization mode (default: hybrid)'
    )
    parser.add_argument(
        '--format',
        choices=['simple', 'json'],
        default='simple',
        help='Input file format (default: simple)'
    )
    parser.add_argument(
        '--stats-only',
        action='store_true',
        help='Only print statistics, do not export'
    )

    args = parser.parse_args()

    # Validate input
    if not Path(args.input_file).exists():
        print(f"Error: Input file not found: {args.input_file}")
        return 1

    # Create tokenizer
    tokenizer = HybridTokenizer(mode=args.mode)

    # Load data
    print(f"Loading aligned data from: {args.input_file}")
    if args.format == 'json':
        tokenizer.load_from_aligned_file(args.input_file)
    else:
        tokenizer.load_from_simple_format(args.input_file)

    print(f"Loaded {len(tokenizer.sync_tokens)} synchronized tokens")

    # Print statistics
    stats = tokenizer.get_statistics()
    print("\n=== Hybrid Tokenization Statistics ===")
    print(json.dumps(stats, indent=2))

    # Export if not stats-only
    if not args.stats_only:
        tokenizer.export_for_graph_builder(args.output)

        print(f"\nNext steps:")
        if args.mode == 'hybrid':
            print(f"  1. Build graph: python3 src/midi_graph_builder.py {args.output} -o output/hybrid_graph.json")
            print(f"  2. Analyze: python3 src/analyze_word_graph.py output/hybrid_graph.json")
        elif args.mode == 'parallel':
            output_base = Path(args.output).stem
            print(f"  1. Build word graph: python3 src/word_graph_builder.py {output_base}_words.txt -o output/words_graph.json")
            print(f"  2. Build note graph: python3 src/midi_graph_builder.py {output_base}_notes.txt -o output/notes_graph.json")
            print(f"  3. Merge: python3 src/merge_word_graphs.py output/words_graph.json output/notes_graph.json")

    return 0


if __name__ == '__main__':
    exit(main())
