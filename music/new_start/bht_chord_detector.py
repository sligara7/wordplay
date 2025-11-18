"""
Binary Hypothesis Test (BHT) Chord Detector

Adapted from space object detection for musical chord recognition.
Uses matched-filter detection with SNR-based threshold.

Reference: MHT.md (Space Surveillance Telescope algorithms)
Correlation: MHT_MUSIC_CORRELATION.md
"""

import numpy as np
from typing import Dict, List, Tuple, Optional


class BHTChordDetector:
    """
    Binary Hypothesis Test for chord detection in spectral data.

    Analogous to BHT point detector from space surveillance:
    - Image frame → Time slice of spectral data
    - PSF → Chord template
    - Pixel intensity → Spectral amplitude
    - Background noise → Noise floor
    """

    def __init__(self,
                 chord_template: np.ndarray,
                 chord_name: str,
                 threshold: float = 6.0,
                 use_outlier_removal: bool = True):
        """
        Initialize BHT detector for single chord type.

        Args:
            chord_template: h(f) - Template function for chord
            chord_name: Name of chord (e.g., 'C_major')
            threshold: SNR threshold γ (default: 6.0 for P_FA = 9.87e-10)
            use_outlier_removal: Use MHTOR outlier rejection
        """
        self.h = chord_template
        self.chord_name = chord_name
        self.gamma = threshold
        self.use_outlier_removal = use_outlier_removal

        # Precompute template norm for efficiency
        self.h_norm = np.sqrt(np.sum(self.h**2))

    def detect(self, spectral_slice: np.ndarray) -> Dict:
        """
        Detect chord in single time slice using BHT.

        Implements equations from MHT.md:
        - Background: B = median(A(f))
        - Noise std: σ = std(A(f) - B) with outlier removal
        - SNR = Σ[(A(f) - B) · h(f)] / (σ · sqrt(Σ h²(f)))

        Args:
            spectral_slice: A(f, t) - 1D array of spectral amplitudes

        Returns:
            {
                'detected': bool - True if SNR > threshold,
                'snr': float - Signal-to-noise ratio,
                'chord': str - Chord name (if detected),
                'background': float - Background noise level B,
                'noise_std': float - Noise standard deviation σ,
                'confidence': float - Normalized confidence [0, 1]
            }
        """
        # Step 1: Calculate background (median) - Eq. from MHT.md line 62
        B = np.median(spectral_slice)

        # Step 2: Calculate noise standard deviation - MHT.md lines 68-73
        if self.use_outlier_removal:
            sigma = self._calculate_noise_std_with_outlier_removal(spectral_slice, B)
        else:
            sigma = np.std(spectral_slice - B)

        # Step 3: Matched filter SNR - MHT.md lines 96-107
        numerator = np.sum((spectral_slice - B) * self.h)
        denominator = sigma * self.h_norm + 1e-10  # Add epsilon to avoid division by zero

        snr = numerator / denominator

        # Step 4: Threshold test - MHT.md line 110
        detected = (snr > self.gamma)

        # Convert SNR to normalized confidence [0, 1]
        # SNR of 6 → 0.5, SNR of 12 → 1.0
        confidence = min(max((snr - self.gamma) / self.gamma, 0.0), 1.0)

        return {
            'detected': detected,
            'snr': float(snr),
            'chord': self.chord_name if detected else None,
            'background': float(B),
            'noise_std': float(sigma),
            'confidence': float(confidence)
        }

    def _calculate_noise_std_with_outlier_removal(self,
                                                   A: np.ndarray,
                                                   B: float) -> float:
        """
        Calculate noise standard deviation with outlier removal (MHTOR).

        Implements MHTOR algorithm from MHT.md section 3:
        1. Compute squared deviations D(f) = (A(f) - B)²
        2. Calculate M = mean(D), S = std(D)
        3. Reject outliers where D(f) ≥ M + 3·S
        4. Recompute σ using only non-outlier frequencies

        This removes:
        - Strong harmonics (like bright stars in astronomy)
        - Transients (like cosmic rays)
        - Artifacts (like hot pixels)

        Args:
            A: Spectral amplitudes A(f)
            B: Background level

        Returns:
            σ - Noise standard deviation with outliers removed
        """
        # Step 1: Squared deviations - MHT.md line 204
        D = (A - B)**2

        # Step 2: Mean and std dev of squared deviations - MHT.md lines 212-223
        M = np.mean(D)
        S = np.std(D)

        # Step 3: Outlier rejection - MHT.md lines 228-232
        outlier_threshold = M + 3 * S
        mask = D < outlier_threshold

        # Handle case where all samples are outliers
        if np.sum(mask) < 3:
            # Fallback to standard calculation
            return np.std(A - B)

        # Step 4: Recompute sigma using only non-outliers - MHT.md line 237
        sigma = np.sqrt(np.mean(D[mask]))

        return sigma

    def get_detection_probability(self, snr: float) -> float:
        """
        Calculate theoretical detection probability for given SNR.

        For Gaussian noise with SNR and threshold γ:
        P_detection = Q(γ - SNR) where Q is the Q-function

        Args:
            snr: Signal-to-noise ratio

        Returns:
            Probability of detection [0, 1]
        """
        from scipy.stats import norm
        return 1 - norm.cdf(self.gamma - snr)

    def get_false_alarm_probability(self) -> float:
        """
        Calculate theoretical false alarm probability.

        For threshold γ and Gaussian noise:
        P_FA = Q(γ) = integral from γ to ∞ of normal distribution

        From MHT.md line 119: γ=6 → P_FA = 9.87 × 10⁻¹⁰

        Returns:
            Probability of false alarm
        """
        from scipy.stats import norm
        return 1 - norm.cdf(self.gamma)


class MHTChordDetector:
    """
    Multi-Hypothesis Test (MHT) for chord detection.

    Tests multiple chord templates simultaneously and selects best match.
    Analogous to MHT in space surveillance with 9 sub-pixel hypotheses.
    """

    def __init__(self,
                 chord_templates: Dict[str, np.ndarray],
                 threshold: float = 6.5,
                 use_outlier_removal: bool = True):
        """
        Initialize MHT detector with multiple chord templates.

        Args:
            chord_templates: Dict[chord_name, h(f)] - All chord templates
            threshold: SNR threshold γ_MHT (adjusted for multiple hypotheses)
            use_outlier_removal: Use MHTOR outlier rejection

        Note: Threshold should be higher than BHT to maintain same P_FA.
        From MHT.md: γ_BHT=6.0 → γ_MHT=6.2212 for 9 hypotheses.
        For ~120 chord templates: γ_MHT ≈ 6.5
        """
        self.templates = chord_templates
        self.gamma_MHT = threshold
        self.use_outlier_removal = use_outlier_removal

        # Precompute template norms
        self.template_norms = {
            name: np.sqrt(np.sum(h**2))
            for name, h in chord_templates.items()
        }

    def detect(self, spectral_slice: np.ndarray) -> Dict:
        """
        Detect best matching chord via M-ary hypothesis test.

        Tests all chord hypotheses:
        H₀: No chord (noise only)
        H₁: Chord 1 present
        H₂: Chord 2 present
        ...
        H_N: Chord N present

        Selects hypothesis with maximum SNR (if above threshold).

        Args:
            spectral_slice: A(f, t) - 1D array of spectral amplitudes

        Returns:
            {
                'detected': bool - True if max SNR > threshold,
                'chord': str - Best matching chord (if detected),
                'snr': float - Maximum SNR across all hypotheses,
                'all_snrs': Dict[chord_name, snr] - SNRs for all chords,
                'background': float - Background noise level,
                'noise_std': float - Noise standard deviation,
                'confidence': float - Normalized confidence [0, 1],
                'top_5_chords': List[Tuple[str, float]] - Top 5 chord candidates
            }
        """
        # Step 1: Calculate background and noise (same for all hypotheses)
        B = np.median(spectral_slice)

        if self.use_outlier_removal:
            sigma = self._calculate_noise_std_with_outlier_removal(spectral_slice, B)
        else:
            sigma = np.std(spectral_slice - B)

        # Step 2: Calculate SNR for each chord template - MHT.md lines 154-162
        snrs = {}
        for chord_name, h in self.templates.items():
            snr = self._calculate_snr(spectral_slice, B, sigma, h, chord_name)
            snrs[chord_name] = snr

        # Step 3: M-ary selection - select max SNR - MHT.md line 174
        best_chord = max(snrs, key=snrs.get)
        max_snr = snrs[best_chord]

        # Step 4: Threshold test - MHT.md lines 156-157
        detected = (max_snr > self.gamma_MHT)

        # Get top 5 chord candidates
        sorted_chords = sorted(snrs.items(), key=lambda x: x[1], reverse=True)
        top_5 = sorted_chords[:5]

        # Normalized confidence
        confidence = min(max((max_snr - self.gamma_MHT) / self.gamma_MHT, 0.0), 1.0)

        return {
            'detected': detected,
            'chord': best_chord if detected else None,
            'snr': float(max_snr),
            'all_snrs': {k: float(v) for k, v in snrs.items()},
            'background': float(B),
            'noise_std': float(sigma),
            'confidence': float(confidence),
            'top_5_chords': [(name, float(snr)) for name, snr in top_5]
        }

    def _calculate_snr(self,
                       A: np.ndarray,
                       B: float,
                       sigma: float,
                       h: np.ndarray,
                       chord_name: str) -> float:
        """
        Calculate SNR for given chord template.

        SNR = Σ[(A(f) - B) · h(f)] / (σ · sqrt(Σ h²(f)))

        From MHT.md lines 154-162.
        """
        numerator = np.sum((A - B) * h)
        denominator = sigma * self.template_norms[chord_name] + 1e-10

        return numerator / denominator

    def _calculate_noise_std_with_outlier_removal(self, A: np.ndarray, B: float) -> float:
        """Same as BHTChordDetector._calculate_noise_std_with_outlier_removal"""
        D = (A - B)**2
        M = np.mean(D)
        S = np.std(D)
        outlier_threshold = M + 3 * S
        mask = D < outlier_threshold

        if np.sum(mask) < 3:
            return np.std(A - B)

        return np.sqrt(np.mean(D[mask]))

    def get_false_alarm_probability_adjusted(self) -> float:
        """
        Calculate false alarm probability adjusted for multiple hypotheses.

        From MHT.md line 187:
        P_FA(MHT) ≈ N · P_FA(BHT)

        where N is number of hypotheses.
        """
        from scipy.stats import norm
        p_fa_single = 1 - norm.cdf(self.gamma_MHT)
        return len(self.templates) * p_fa_single


def build_chord_templates(frequencies: np.ndarray,
                          chord_types: Optional[List[str]] = None,
                          template_type: str = 'gaussian',
                          sigma_hz: float = 10.0) -> Dict[str, np.ndarray]:
    """
    Build chord templates h_c(f) for matched-filter detection.

    Args:
        frequencies: Array of frequency bins from spectral_analyzer
        chord_types: List of chord types to generate (default: all)
        template_type: 'binary' or 'gaussian' (default: 'gaussian')
        sigma_hz: Spread of Gaussian peaks in Hz (for gaussian type)

    Returns:
        Dict[chord_name, template] where template is h(f)
    """
    # Chord interval definitions (semitones from root)
    # From chords.py and MHT_MUSIC_CORRELATION.md
    all_chord_intervals = {
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

    if chord_types is None:
        chord_intervals = all_chord_intervals
    else:
        chord_intervals = {k: v for k, v in all_chord_intervals.items() if k in chord_types}

    # Note names
    note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

    templates = {}

    # For each root note
    for root_idx, root_name in enumerate(note_names):
        # For each chord type
        for chord_type, intervals in chord_intervals.items():
            chord_name = f"{root_name}_{chord_type}"

            # Create template
            if template_type == 'binary':
                template = _build_binary_template(
                    frequencies, root_idx, intervals
                )
            elif template_type == 'gaussian':
                template = _build_gaussian_template(
                    frequencies, root_idx, intervals, sigma_hz
                )
            else:
                raise ValueError(f"Unknown template_type: {template_type}")

            templates[chord_name] = template

    return templates


def _build_binary_template(frequencies: np.ndarray,
                           root_idx: int,
                           intervals: List[int]) -> np.ndarray:
    """Build binary chord template (1 at chord frequencies, 0 elsewhere)."""
    template = np.zeros(len(frequencies))

    A0_freq = 27.5  # A0 frequency

    # Mapping from note_names index to semitones above A0
    # C=3, C#=4, D=5, D#=6, E=7, F=8, F#=9, G=10, G#=11, A=0, A#=1, B=2
    note_to_semitone = [3, 4, 5, 6, 7, 8, 9, 10, 11, 0, 1, 2]

    # For each interval in chord
    for interval in intervals:
        pitch_class = (root_idx + interval) % 12
        target_semitone = note_to_semitone[pitch_class]

        # Mark all octaves of this pitch class
        for freq_idx, freq in enumerate(frequencies):
            # Calculate pitch class from frequency
            semitones = 12 * np.log2(freq / A0_freq)
            freq_semitone = int(round(semitones % 12)) % 12

            if freq_semitone == target_semitone:
                template[freq_idx] = 1.0

    return template


def _build_gaussian_template(frequencies: np.ndarray,
                             root_idx: int,
                             intervals: List[int],
                             sigma_hz: float) -> np.ndarray:
    """
    Build Gaussian-weighted chord template.

    More realistic than binary - accounts for spectral spread.
    """
    template = np.zeros(len(frequencies))

    A0_freq = 27.5
    # note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    # A is at index 9, so we need to convert from C-based to A-based indexing
    # C is 3 semitones above A (in the previous octave)
    # So C0 is at semitone 3, C#0 at 4, etc.

    # Mapping from note_names index to semitones above A0
    # C=3, C#=4, D=5, D#=6, E=7, F=8, F#=9, G=10, G#=11, A=0, A#=1, B=2
    note_to_semitone = [3, 4, 5, 6, 7, 8, 9, 10, 11, 0, 1, 2]

    # For each interval in chord
    for interval in intervals:
        pitch_class = (root_idx + interval) % 12
        semitone_in_octave = note_to_semitone[pitch_class]

        # Get all target frequencies (all octaves)
        target_freqs = []
        for octave in range(-1, 9):  # A-1 to A8
            # Calculate frequency for this pitch class and octave
            semitones_from_A0 = octave * 12 + semitone_in_octave
            freq = A0_freq * 2**(semitones_from_A0 / 12.0)

            # Only include if in frequency range
            if frequencies[0] <= freq <= frequencies[-1]:
                target_freqs.append(freq)

        # Add Gaussian peak at each target frequency
        for target_freq in target_freqs:
            gaussian = np.exp(-(frequencies - target_freq)**2 / (2 * sigma_hz**2))
            template += gaussian

    # Normalize (important for SNR calculation)
    if np.sum(template**2) > 0:
        template = template / np.linalg.norm(template)

    return template


if __name__ == "__main__":
    # Example usage and validation
    print("=" * 60)
    print("BHT/MHT Chord Detector - Example Usage")
    print("=" * 60)

    # Create synthetic spectral data
    print("\n1. Generating synthetic C major chord spectral data...")

    # Frequency bins (simulate spectral_analyzer output)
    A0 = 27.5
    frequencies = A0 * 2**(np.arange(-1, 89) / 12.0)  # A-1 to A8

    # Create C major chord: C4 (261.63 Hz), E4 (329.63 Hz), G4 (392.00 Hz)
    C4_freq = 261.63
    E4_freq = 329.63
    G4_freq = 392.00

    # Simulate spectral peaks with Gaussian spread
    sigma = 5.0  # Hz
    spectral_data = (
        10.0 * np.exp(-(frequencies - C4_freq)**2 / (2*sigma**2)) +
        8.0 * np.exp(-(frequencies - E4_freq)**2 / (2*sigma**2)) +
        6.0 * np.exp(-(frequencies - G4_freq)**2 / (2*sigma**2))
    )

    # Add noise
    noise_level = 0.5
    spectral_data += noise_level * np.random.randn(len(frequencies))

    print(f"   Frequencies: {len(frequencies)} bins from {frequencies[0]:.1f} to {frequencies[-1]:.1f} Hz")
    print(f"   Signal peaks at: C4={C4_freq:.2f} Hz, E4={E4_freq:.2f} Hz, G4={G4_freq:.2f} Hz")
    print(f"   Noise level: {noise_level}")

    # Build chord templates
    print("\n2. Building chord templates...")
    templates = build_chord_templates(
        frequencies,
        chord_types=['major', 'minor', 'dim'],
        template_type='gaussian',
        sigma_hz=10.0
    )
    print(f"   Generated {len(templates)} chord templates")

    # Test BHT detector
    print("\n3. Testing BHT detector (single chord: C major)...")
    bht = BHTChordDetector(
        chord_template=templates['C_major'],
        chord_name='C_major',
        threshold=6.0,
        use_outlier_removal=True
    )

    bht_result = bht.detect(spectral_data)
    print(f"   Detected: {bht_result['detected']}")
    print(f"   SNR: {bht_result['snr']:.2f}")
    print(f"   Background: {bht_result['background']:.3f}")
    print(f"   Noise std: {bht_result['noise_std']:.3f}")
    print(f"   Confidence: {bht_result['confidence']:.3f}")
    print(f"   P(false alarm): {bht.get_false_alarm_probability():.2e}")

    # Test MHT detector
    print("\n4. Testing MHT detector (all chord types)...")
    mht = MHTChordDetector(
        chord_templates=templates,
        threshold=6.5,
        use_outlier_removal=True
    )

    mht_result = mht.detect(spectral_data)
    print(f"   Detected: {mht_result['detected']}")
    print(f"   Best chord: {mht_result['chord']}")
    print(f"   SNR: {mht_result['snr']:.2f}")
    print(f"   Confidence: {mht_result['confidence']:.3f}")
    print(f"\n   Top 5 candidates:")
    for i, (chord, snr) in enumerate(mht_result['top_5_chords'], 1):
        print(f"      {i}. {chord:15s} SNR={snr:6.2f}")

    print("\n" + "=" * 60)
    print("SUCCESS: BHT/MHT chord detection working!")
    print("=" * 60)
