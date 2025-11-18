"""
Build Chord PSF (Point Spread Function) Templates

Generates chord templates by:
1. Creating pure sinusoidal tones for each chord
2. Running through the ACTUAL spectral_analyzer.py
3. Using resulting spectrum as template

This ensures templates match what the analyzer actually produces!
"""

import numpy as np
from spectral_analyzer import SpectralAnalyzer
from typing import Dict, List


# Chord definitions from chords.py
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
    """
    Convert note name + octave to frequency.

    Args:
        note_name: 'C', 'C#', etc.
        octave: 0-8

    Returns:
        Frequency in Hz
    """
    # Semitones from A4 (440 Hz)
    note_offsets = {
        'C': -9, 'C#': -8, 'D': -7, 'D#': -6, 'E': -5, 'F': -4,
        'F#': -3, 'G': -2, 'G#': -1, 'A': 0, 'A#': 1, 'B': 2
    }

    semitones_from_A4 = note_offsets[note_name] + (octave - 4) * 12
    return 440.0 * 2**(semitones_from_A4 / 12.0)


def generate_pure_chord_audio(root_note, chord_type, octave=4,
                              duration_sec=1.0, sample_rate=44100,
                              amplitude=0.5):
    """
    Generate pure sinusoidal audio for a chord.

    Args:
        root_note: 'C', 'C#', etc.
        chord_type: 'major', 'minor', etc.
        octave: Root octave (default: 4)
        duration_sec: Duration in seconds
        sample_rate: Sample rate in Hz
        amplitude: Peak amplitude (0-1)

    Returns:
        1D numpy array of audio samples
    """
    # Get chord intervals
    intervals = CHORD_INTERVALS[chord_type]

    # Calculate root frequency
    root_freq = note_name_to_frequency(root_note, octave)

    # Generate time array
    t = np.arange(0, duration_sec, 1.0 / sample_rate)

    # Generate chord: sum of sinusoids
    chord_audio = np.zeros(len(t), dtype=np.float32)

    for i, interval in enumerate(intervals):
        # Calculate frequency for this interval
        note_freq = root_freq * 2**(interval / 12.0)

        # Amplitude decreases for higher notes (more realistic)
        note_amplitude = amplitude * (0.8 ** i)

        # Generate sinusoid
        sinusoid = note_amplitude * np.sin(2 * np.pi * note_freq * t)

        chord_audio += sinusoid

    # Normalize to prevent clipping
    max_val = np.max(np.abs(chord_audio))
    if max_val > 0:
        chord_audio = chord_audio / max_val * amplitude

    return chord_audio


def generate_chord_psf_via_analyzer(root_note, chord_type, octave=4,
                                    sample_rate=44100, cycles=4):
    """
    Generate chord PSF by running pure tones through spectral analyzer.

    This is the CORRECT way to generate templates!

    Args:
        root_note: 'C', 'C#', etc.
        chord_type: 'major', 'minor', etc.
        octave: Root octave
        sample_rate: Sample rate
        cycles: Number of cycles for spectral analyzer

    Returns:
        1D array: Spectral template (the "PSF" for this chord)
    """
    # Calculate duration needed for spectral analyzer
    A0_freq = 440.0 / 16
    duration_sec = cycles / A0_freq  # Same as spectral_analyzer

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

    # Analyze chord (this produces the "PSF"!)
    spectral_data = analyzer.dotop(chord_audio)

    # Extract single time slice (average across time for stability)
    # Shape: [freq, time]
    if spectral_data.shape[1] > 1:
        # Average across time to reduce noise
        psf = np.mean(spectral_data, axis=1)
    else:
        psf = spectral_data[:, 0]

    # Normalize (for matched-filter detection)
    psf_norm = np.linalg.norm(psf)
    if psf_norm > 0:
        psf = psf / psf_norm

    return psf


def build_all_chord_psfs(sample_rate=44100, cycles=4, octave=4,
                         chord_types=None, root_notes=None):
    """
    Build PSF templates for all chords.

    Args:
        sample_rate: Audio sample rate
        cycles: Spectral analyzer cycles
        octave: Root octave for all chords
        chord_types: List of chord types (default: all)
        root_notes: List of root notes (default: all 12)

    Returns:
        Dict[chord_name, psf_array]
    """
    if chord_types is None:
        chord_types = list(CHORD_INTERVALS.keys())

    if root_notes is None:
        root_notes = ROOT_NOTES

    print("=" * 70)
    print("BUILDING CHORD PSF TEMPLATES")
    print("=" * 70)
    print(f"Sample rate: {sample_rate} Hz")
    print(f"Cycles: {cycles}")
    print(f"Octave: {octave}")
    print(f"Chord types: {len(chord_types)}")
    print(f"Root notes: {len(root_notes)}")
    print(f"Total templates: {len(chord_types) * len(root_notes)}")
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

    for chord_type in chord_types:
        print(f"Generating {chord_type} chords...")

        for root_note in root_notes:
            chord_name = f"{root_note}_{chord_type}"

            # Generate PSF via spectral analyzer
            psf = generate_chord_psf_via_analyzer(
                root_note, chord_type, octave,
                sample_rate, cycles
            )

            psf_templates[chord_name] = psf

        print(f"  ✓ {len(root_notes)} templates generated")

    print()
    print("=" * 70)
    print(f"✓ Total templates generated: {len(psf_templates)}")
    print("=" * 70)

    return psf_templates, analyzer.frequencies


def visualize_chord_psf(psf, frequencies, chord_name, save_path=None):
    """
    Visualize a chord PSF template.

    Args:
        psf: PSF array
        frequencies: Frequency bins
        chord_name: Name of chord
        save_path: Optional path to save figure
    """
    import matplotlib.pyplot as plt

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

    # Plot 1: Full spectrum
    ax1.plot(frequencies, psf, 'b-', linewidth=1)
    ax1.set_xlabel('Frequency (Hz)')
    ax1.set_ylabel('Template Amplitude')
    ax1.set_title(f'Chord PSF Template: {chord_name} (Full Spectrum)')
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim([frequencies[0], frequencies[-1]])

    # Plot 2: Zoom to relevant range (100-1000 Hz)
    mask = (frequencies >= 100) & (frequencies <= 1000)
    ax2.plot(frequencies[mask], psf[mask], 'r-', linewidth=2)
    ax2.set_xlabel('Frequency (Hz)')
    ax2.set_ylabel('Template Amplitude')
    ax2.set_title(f'Chord PSF Template: {chord_name} (100-1000 Hz)')
    ax2.grid(True, alpha=0.3)

    # Mark peaks
    peak_threshold = np.max(psf[mask]) * 0.3
    peak_indices = np.where((psf > peak_threshold) & mask)[0]
    for idx in peak_indices:
        ax2.axvline(frequencies[idx], color='g', linestyle='--', alpha=0.3)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150)
        print(f"Saved to: {save_path}")
    else:
        plt.show()

    return fig


if __name__ == "__main__":
    print("Chord PSF Generator - Using Actual Spectral Analyzer")
    print()

    # Example 1: Generate single chord PSF
    print("1. Generating C major PSF...")
    psf_Cmajor = generate_chord_psf_via_analyzer('C', 'major', octave=4)

    analyzer = SpectralAnalyzer(samplefreq=44100, cycles=4)

    print(f"   PSF shape: {psf_Cmajor.shape}")
    print(f"   PSF norm: {np.linalg.norm(psf_Cmajor):.4f}")
    print(f"   PSF max: {np.max(psf_Cmajor):.4f}")
    print(f"   Non-zero bins: {np.sum(psf_Cmajor > 0.01)}")

    # Find peaks
    peak_threshold = np.max(psf_Cmajor) * 0.3
    peak_indices = np.where(psf_Cmajor > peak_threshold)[0]
    print(f"   Peak frequencies:")
    for idx in peak_indices:
        print(f"     {analyzer.frequencies[idx]:.2f} Hz (amplitude={psf_Cmajor[idx]:.4f})")

    print()

    # Example 2: Generate all chord PSFs
    print("2. Generating all chord PSFs...")
    psf_templates, frequencies = build_all_chord_psfs(
        sample_rate=44100,
        cycles=4,
        octave=4,
        chord_types=['major', 'minor', 'dim'],  # Start with simple chords
        root_notes=['C', 'D', 'E', 'F', 'G', 'A', 'B']  # Natural notes
    )

    print()
    print(f"✓ Generated {len(psf_templates)} PSF templates")
    print()

    # Example 3: Visualize
    print("3. Visualizing C major PSF...")
    visualize_chord_psf(
        psf_templates['C_major'],
        frequencies,
        'C_major',
        save_path='chord_psf_C_major.png'
    )

    print()
    print("✓ Done! PSF templates generated using spectral_analyzer.py")
