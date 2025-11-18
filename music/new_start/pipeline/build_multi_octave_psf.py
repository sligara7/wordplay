"""
Build Multi-Octave PSF Templates

Generates PSF templates for multiple octaves to enable
cross-octave chord detection.

Based on cross-octave testing results:
- Octave-4 templates only work for octave-4 chords
- We need templates for octaves 2-6 to cover real music range
- Total: 12 roots × 11 types × 5 octaves = 660 templates

This matches the coverage of chords.py which creates synthesis
waveforms for all octaves.
"""

import numpy as np
from spectral_analyzer import SpectralAnalyzer
import time
import pickle


# Chord definitions
CHORD_INTERVALS = {
    'major':     [0, 4, 7],
    'minor':     [0, 3, 7],
    'dim':       [0, 3, 6],
    'aug':       [0, 4, 8],
    'sus2':      [0, 2, 7],
    'sus4':      [0, 5, 7],
    'maj7':      [0, 4, 7, 11],
    'min7':      [0, 3, 7, 10],
    'dom7':      [0, 4, 7, 10],
    'dom9':      [0, 4, 7, 10, 14],
    'maj11':     [0, 4, 7, 11, 14, 17],
}

ROOT_NOTES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']


def note_name_to_frequency(note_name, octave=4):
    """Convert note name + octave to frequency."""
    note_offsets = {
        'C': -9, 'C#': -8, 'D': -7, 'D#': -6, 'E': -5, 'F': -4,
        'F#': -3, 'G': -2, 'G#': -1, 'A': 0, 'A#': 1, 'B': 2
    }
    semitones_from_A4 = note_offsets[note_name] + (octave - 4) * 12
    return 440.0 * 2**(semitones_from_A4 / 12.0)


def generate_pure_chord_audio(root_note, chord_type, octave=4,
                              duration_sec=1.0, sample_rate=44100,
                              amplitude=0.5):
    """Generate pure sinusoidal audio for a chord."""
    intervals = CHORD_INTERVALS[chord_type]
    root_freq = note_name_to_frequency(root_note, octave)
    t = np.arange(0, duration_sec, 1.0 / sample_rate)
    chord_audio = np.zeros(len(t), dtype=np.float32)

    for i, interval in enumerate(intervals):
        note_freq = root_freq * 2**(interval / 12.0)
        note_amplitude = amplitude * (0.8 ** i)
        sinusoid = note_amplitude * np.sin(2 * np.pi * note_freq * t)
        chord_audio += sinusoid

    # Normalize
    max_val = np.max(np.abs(chord_audio))
    if max_val > 0:
        chord_audio = chord_audio / max_val * amplitude

    return chord_audio


def generate_chord_psf_via_analyzer(root_note, chord_type, octave=4,
                                    sample_rate=44100, cycles=4):
    """Generate chord PSF by running pure tones through spectral analyzer."""
    A0_freq = 440.0 / 16
    duration_sec = cycles / A0_freq

    # Generate pure chord audio
    chord_audio = generate_pure_chord_audio(
        root_note, chord_type, octave,
        duration_sec=duration_sec,
        sample_rate=sample_rate,
        amplitude=0.5
    )

    # Initialize spectral analyzer
    analyzer = SpectralAnalyzer(
        samplefreq=sample_rate,
        cycles=cycles,
        standard_A4=440.0
    )

    # Analyze chord
    spectral_data = analyzer.dotop(chord_audio)

    # Average across time and normalize
    if spectral_data.shape[1] > 1:
        psf = np.mean(spectral_data, axis=1)
    else:
        psf = spectral_data[:, 0]

    # Normalize
    psf_norm = np.linalg.norm(psf)
    if psf_norm > 0:
        psf = psf / psf_norm

    return psf


def build_multi_octave_psfs(sample_rate=44100, cycles=4,
                             octaves=[2, 3, 4, 5, 6],
                             chord_types=None, root_notes=None,
                             save_path=None):
    """
    Build PSF templates for multiple octaves.

    Args:
        sample_rate: Audio sample rate
        cycles: Spectral analyzer cycles
        octaves: List of octaves to generate templates for
        chord_types: List of chord types (default: all 11)
        root_notes: List of root notes (default: all 12)
        save_path: Optional path to save templates as pickle file

    Returns:
        Dict[chord_name_with_octave, psf_array], frequencies
    """
    if chord_types is None:
        chord_types = list(CHORD_INTERVALS.keys())

    if root_notes is None:
        root_notes = ROOT_NOTES

    print("=" * 80)
    print("BUILDING MULTI-OCTAVE PSF TEMPLATES")
    print("=" * 80)
    print(f"Sample rate: {sample_rate} Hz")
    print(f"Cycles: {cycles}")
    print(f"Octaves: {octaves}")
    print(f"Chord types: {len(chord_types)}")
    print(f"Root notes: {len(root_notes)}")
    print(f"Total templates: {len(chord_types) * len(root_notes) * len(octaves)}")
    print()

    # Initialize analyzer once (for getting frequency bins)
    analyzer = SpectralAnalyzer(
        samplefreq=sample_rate,
        cycles=cycles,
        standard_A4=440.0
    )

    print(f"Frequency bins: {len(analyzer.frequencies)}")
    print(f"Frequency range: {analyzer.frequencies[0]:.2f} - {analyzer.frequencies[-1]:.2f} Hz")
    print()

    # Build all PSFs
    psf_templates = {}
    start_time = time.perf_counter()

    for octave in octaves:
        print(f"\n{'=' * 80}")
        print(f"OCTAVE {octave}")
        print(f"{'=' * 80}")

        octave_start_time = time.perf_counter()

        for chord_type in chord_types:
            print(f"  Generating {chord_type} chords (octave {octave})...")

            for root_note in root_notes:
                # Chord name includes octave
                chord_name = f"{root_note}_{chord_type}_oct{octave}"

                # Generate PSF via spectral analyzer
                psf = generate_chord_psf_via_analyzer(
                    root_note, chord_type, octave,
                    sample_rate, cycles
                )

                psf_templates[chord_name] = psf

            print(f"    ✓ {len(root_notes)} templates generated")

        octave_time = time.perf_counter() - octave_start_time
        print(f"  Octave {octave} time: {octave_time:.2f} seconds")

    total_time = time.perf_counter() - start_time

    print()
    print("=" * 80)
    print(f"✓ Total templates generated: {len(psf_templates)}")
    print(f"✓ Total time: {total_time:.2f} seconds ({len(psf_templates)/total_time:.1f} templates/sec)")
    print("=" * 80)

    # Save if requested
    if save_path:
        print(f"\nSaving templates to: {save_path}")
        with open(save_path, 'wb') as f:
            pickle.dump({
                'templates': psf_templates,
                'frequencies': analyzer.frequencies,
                'sample_rate': sample_rate,
                'cycles': cycles,
                'octaves': octaves,
                'chord_types': chord_types,
                'root_notes': root_notes
            }, f)
        print(f"✓ Saved {len(psf_templates)} templates")

    return psf_templates, analyzer.frequencies


def load_multi_octave_psfs(load_path):
    """
    Load pre-generated multi-octave PSF templates.

    Args:
        load_path: Path to pickle file

    Returns:
        Dict[chord_name_with_octave, psf_array], frequencies, metadata
    """
    print(f"Loading templates from: {load_path}")
    with open(load_path, 'rb') as f:
        data = pickle.load(f)

    print(f"✓ Loaded {len(data['templates'])} templates")
    print(f"  Sample rate: {data['sample_rate']} Hz")
    print(f"  Cycles: {data['cycles']}")
    print(f"  Octaves: {data['octaves']}")
    print(f"  Chord types: {len(data['chord_types'])}")
    print(f"  Root notes: {len(data['root_notes'])}")

    return data['templates'], data['frequencies'], data


def create_octave_agnostic_templates(multi_octave_templates):
    """
    Create "octave-agnostic" templates by combining templates from all octaves.

    For each chord type + root combination, we have 5 templates (one per octave).
    This function creates a single meta-template that can match any octave.

    Strategy: For each chord type + root, keep all octave variants separate
    but allow the detector to try all of them.

    Args:
        multi_octave_templates: Dict with keys like "C_major_oct4"

    Returns:
        Dict mapping (root, chord_type) -> list of templates
    """
    octave_agnostic = {}

    for chord_name, psf in multi_octave_templates.items():
        # Parse chord name: "C_major_oct4" -> root="C", type="major", octave=4
        parts = chord_name.split('_')

        # Handle multi-word chord types (e.g., "dom7" vs "C#")
        if parts[0] in ROOT_NOTES:
            root = parts[0]
            # Everything except root and "oct{N}"
            chord_type = '_'.join(parts[1:-1])  # e.g., "major" or "dom" + "7"
        else:
            # Handle flats/sharps (e.g., "C#_major_oct4")
            root = parts[0]
            chord_type = '_'.join(parts[1:-1])

        # Create key without octave
        key = f"{root}_{chord_type}"

        if key not in octave_agnostic:
            octave_agnostic[key] = []

        octave_agnostic[key].append(psf)

    # Convert lists to arrays for faster computation
    for key in octave_agnostic:
        octave_agnostic[key] = np.array(octave_agnostic[key])

    print(f"Created {len(octave_agnostic)} octave-agnostic chord templates")
    print(f"Each template has {len(list(octave_agnostic.values())[0])} octave variants")

    return octave_agnostic


if __name__ == "__main__":
    print("\nMulti-Octave PSF Template Generator\n")

    # Configuration
    octaves = [2, 3, 4, 5, 6]  # Cover piano range
    save_path = "multi_octave_psf_templates.pkl"

    print("This will generate PSF templates for:")
    print(f"  - {len(CHORD_INTERVALS)} chord types")
    print(f"  - {len(ROOT_NOTES)} root notes")
    print(f"  - {len(octaves)} octaves")
    print(f"  - Total: {len(CHORD_INTERVALS) * len(ROOT_NOTES) * len(octaves)} templates")
    print()

    # Estimate time
    # From previous tests: ~46 seconds for 132 templates (octave 4 only)
    # Extrapolate: 660 templates = 5x more = ~230 seconds = ~4 minutes
    estimated_time = (len(CHORD_INTERVALS) * len(ROOT_NOTES) * len(octaves)) / 132 * 46
    print(f"Estimated generation time: {estimated_time:.0f} seconds (~{estimated_time/60:.1f} minutes)")
    print()

    # Generate
    print("Starting generation...\n")

    templates, frequencies = build_multi_octave_psfs(
        sample_rate=44100,
        cycles=4,
        octaves=octaves,
        chord_types=list(CHORD_INTERVALS.keys()),
        root_notes=ROOT_NOTES,
        save_path=save_path
    )

    print("\n" + "=" * 80)
    print("TEMPLATE SUMMARY")
    print("=" * 80)

    # Count by octave
    for octave in octaves:
        count = sum(1 for key in templates.keys() if f"oct{octave}" in key)
        print(f"Octave {octave}: {count} templates")

    # Count by chord type
    print()
    for chord_type in CHORD_INTERVALS.keys():
        count = sum(1 for key in templates.keys() if f"_{chord_type}_" in key)
        print(f"{chord_type:10s}: {count} templates")

    print("\n✓ Multi-octave PSF templates generated successfully!")
    print(f"✓ Saved to: {save_path}")
