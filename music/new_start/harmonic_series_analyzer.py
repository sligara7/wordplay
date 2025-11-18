#!/usr/bin/env python3
"""
Harmonic Series Analyzer

Uses harmonic series signatures (f, 2f, 3f, 4f...) with exponential decay
to distinguish fundamentals from harmonics.

Two-phase approach:
1. Intra-sample: Identify harmonic series within each time window
2. Inter-sample: Build temporal DAG to track fundamentals over time

Concept:
- Harmonics are integer multiples of fundamental with exponentially decreasing intensity
- Anything not fitting a harmonic series = separate fundamental
- Temporal continuity helps correct detection errors
"""

import networkx as nx
import numpy as np
from typing import Dict, List, Tuple, Set, Optional
from collections import defaultdict
from scipy.optimize import curve_fit


class HarmonicSeriesAnalyzer:
    """
    Analyze harmonic series to distinguish fundamentals from overtones.
    """

    def __init__(self,
                 audio_graph: nx.Graph,
                 frequency_tolerance: float = 0.02,  # 2% tolerance for integer multiples
                 min_harmonics: int = 2,  # Minimum harmonics to confirm series
                 decay_threshold: float = 0.5):  # R² threshold for exponential fit
        """
        Initialize harmonic series analyzer.

        Args:
            audio_graph: Audio analysis graph from AudioGraphBuilder
            frequency_tolerance: Tolerance for detecting integer multiples (2% = ±2%)
            min_harmonics: Minimum number of harmonics needed to confirm series
            decay_threshold: R² threshold for exponential decay fit
        """
        self.graph = audio_graph
        self.frequency_tolerance = frequency_tolerance
        self.min_harmonics = min_harmonics
        self.decay_threshold = decay_threshold

        # Get time samples
        self.time_samples = self._extract_time_samples()

    def _extract_time_samples(self) -> List[int]:
        """Extract unique time sample indices from graph."""
        time_samples = set()
        for node_id in self.graph.nodes():
            node_data = self.graph.nodes[node_id]
            time_idx = node_data.get('time_idx', node_data.get('time_sample'))
            if time_idx is not None:
                time_samples.add(time_idx)
        return sorted(list(time_samples))

    def analyze_all_time_samples(self) -> Dict[int, List[Dict]]:
        """
        Analyze all time samples to extract fundamentals.

        Returns:
            Dictionary mapping time_sample → list of fundamentals
        """
        fundamentals_by_time = {}

        for time_idx in self.time_samples:
            fundamentals = self._analyze_time_sample(time_idx)
            if fundamentals:
                fundamentals_by_time[time_idx] = fundamentals

        return fundamentals_by_time

    def _analyze_time_sample(self, time_idx: int) -> List[Dict]:
        """
        Analyze single time sample to extract fundamentals.

        Process:
        1. Get all frequencies and intensities at this time
        2. Find harmonic series (f, 2f, 3f, 4f...)
        3. Check for exponential decay
        4. Extract fundamentals

        Args:
            time_idx: Time sample index

        Returns:
            List of detected fundamentals with metadata
        """
        # Get all nodes at this time sample
        nodes_at_time = []
        for node_id in self.graph.nodes():
            node_data = self.graph.nodes[node_id]
            node_time_idx = node_data.get('time_idx', node_data.get('time_sample'))

            if node_time_idx == time_idx:
                freq = node_data.get('frequency')
                intensity = node_data.get('intensity')
                note = node_data.get('note')
                freq_idx = node_data.get('freq_idx', node_data.get('freq_index'))

                if freq and intensity:
                    nodes_at_time.append({
                        'node_id': node_id,
                        'frequency': freq,
                        'intensity': intensity,
                        'note': note,
                        'freq_idx': freq_idx,
                        'time_idx': time_idx
                    })

        if not nodes_at_time:
            return []

        # Sort by frequency (lowest first)
        nodes_at_time.sort(key=lambda n: n['frequency'])

        # Try GCD-based fundamental detection first (handles missing fundamentals)
        # TEMPORARILY DISABLED - causing octave errors (4.4% pitch accuracy)
        # gcd_fundamentals = self._find_fundamentals_via_gcd(nodes_at_time)

        # Also use traditional harmonic series detection
        harmonic_series = self._find_harmonic_series(nodes_at_time)

        # Combine both approaches, preferring GCD results for overlaps
        # TEMPORARILY DISABLED
        # harmonic_series = self._merge_gcd_and_harmonic_series(gcd_fundamentals, harmonic_series)

        # Extract fundamentals (base of each series)
        fundamentals = []
        used_nodes = set()

        for series in harmonic_series:
            if series['fundamental']['node_id'] in used_nodes:
                continue

            # Mark all nodes in this series as used
            for node in series['harmonics']:
                used_nodes.add(node['node_id'])

            # Create fundamental entry
            fundamental_node = series['fundamental']
            fundamentals.append({
                'node_id': fundamental_node['node_id'],
                'frequency': fundamental_node['frequency'],
                'note': fundamental_node['note'],
                'intensity': fundamental_node['intensity'],
                'time_idx': time_idx,
                'time_seconds': self._get_time_in_seconds(time_idx),
                'num_harmonics': series['num_harmonics'],
                'decay_score': series['decay_score'],
                'confidence': series['confidence'],
                'harmonic_nodes': [h['node_id'] for h in series['harmonics']]
            })

        # NOTE: Standalone nodes (not part of harmonic series) are NOT added
        # Rationale: Real musical notes have harmonics. If no harmonics detected,
        # it's likely noise or an artifact. Percussion can be handled separately.
        # This strict approach reduces over-detection significantly.

        return fundamentals

    def _find_harmonic_series(self, nodes: List[Dict]) -> List[Dict]:
        """
        Find harmonic series (f, 2f, 3f...) with exponential decay.

        Args:
            nodes: List of frequency nodes sorted by frequency

        Returns:
            List of harmonic series, each containing:
            - fundamental: The base frequency node
            - harmonics: List of harmonic nodes (including fundamental)
            - num_harmonics: Number of harmonics detected
            - decay_score: R² score for exponential fit
            - confidence: Overall confidence in this series
        """
        series_list = []

        # Try each node as potential fundamental
        # NOTE: We do NOT filter by minimum intensity here
        # - Real fundamentals can be weak or even missing ("missing fundamental" phenomenon)
        # - Intensity is already weighted 40% in confidence calculation
        # - Overlapping series removal will prefer fundamentals with higher confidence

        for i, potential_fundamental in enumerate(nodes):
            f0 = potential_fundamental['frequency']

            # Find harmonics: 2f, 3f, 4f, 5f...
            harmonics = [potential_fundamental]  # Include fundamental
            harmonic_intensities = [potential_fundamental['intensity']]

            for harmonic_num in range(2, 11):  # Check up to 10th harmonic
                expected_freq = f0 * harmonic_num
                tolerance = expected_freq * self.frequency_tolerance

                # NOTE: Piano has inharmonicity (partials sharper than integer multiples)
                # but the 2% flat tolerance seems to work better than progressive tolerance
                # Progressive tolerance was matching too many false harmonics

                # Search for matching frequency
                for node in nodes[i+1:]:  # Only look at higher frequencies
                    if abs(node['frequency'] - expected_freq) <= tolerance:
                        harmonics.append(node)
                        harmonic_intensities.append(node['intensity'])
                        break

            # Check if we have enough harmonics
            if len(harmonics) >= self.min_harmonics + 1:  # +1 for fundamental
                # NOTE: We do NOT check if fundamental is loudest
                # Piano and many instruments have strong 2nd harmonics
                # Instead, we rely on confidence scoring (40% weight on intensity)
                # to prefer fundamentals with higher intensity

                # Check for exponential decay
                decay_score = self._check_exponential_decay(harmonic_intensities)

                # Calculate confidence based on:
                # 1. Number of harmonics found
                # 2. Quality of exponential fit
                # 3. Fundamental intensity
                num_harmonics = len(harmonics) - 1  # Exclude fundamental from count
                confidence = self._calculate_confidence(
                    num_harmonics,
                    decay_score,
                    potential_fundamental['intensity']
                )

                # Only accept if decay score meets threshold or has many harmonics
                if decay_score >= self.decay_threshold or num_harmonics >= 4:
                    series_list.append({
                        'fundamental': potential_fundamental,
                        'harmonics': harmonics,
                        'num_harmonics': num_harmonics,
                        'decay_score': decay_score,
                        'confidence': confidence
                    })

        # Remove overlapping series (keep the one with highest confidence)
        series_list = self._remove_overlapping_series(series_list)

        return series_list

    def _check_exponential_decay(self, intensities: List[float]) -> float:
        """
        Check if intensities follow exponential decay.

        Fits: I(n) = I₀ * e^(-λn)
        where n = harmonic number (1, 2, 3, 4...)

        Returns:
            R² score (0-1) indicating quality of exponential fit
        """
        if len(intensities) < 2:
            return 0.0

        # Harmonic numbers: 1, 2, 3, 4...
        n = np.arange(1, len(intensities) + 1)
        intensities_arr = np.array(intensities)

        # Handle edge case where intensities don't decay
        if intensities_arr[0] == 0:
            return 0.0

        try:
            # Fit exponential decay: I(n) = I₀ * e^(-λn)
            def exponential_decay(n, I0, lambd):
                return I0 * np.exp(-lambd * n)

            # Initial guess
            I0_guess = intensities_arr[0]
            lambda_guess = 0.1

            popt, _ = curve_fit(
                exponential_decay,
                n,
                intensities_arr,
                p0=[I0_guess, lambda_guess],
                maxfev=2000
            )

            # Calculate R² score
            fitted = exponential_decay(n, *popt)
            residuals = intensities_arr - fitted
            ss_res = np.sum(residuals**2)
            ss_tot = np.sum((intensities_arr - np.mean(intensities_arr))**2)

            if ss_tot == 0:
                return 0.0

            r_squared = 1 - (ss_res / ss_tot)
            return max(0.0, min(1.0, r_squared))  # Clamp to [0, 1]

        except (RuntimeError, ValueError):
            # Fit failed - check if intensities are generally decreasing
            # Simple check: count how many intensities decrease
            decreasing_count = sum(1 for i in range(len(intensities)-1)
                                  if intensities[i] >= intensities[i+1])
            return decreasing_count / (len(intensities) - 1) if len(intensities) > 1 else 0.0

    def _calculate_confidence(self, num_harmonics: int, decay_score: float,
                             fundamental_intensity: float) -> float:
        """
        Calculate confidence score for a detected fundamental.

        Factors:
        - More harmonics = higher confidence
        - Better exponential fit = higher confidence
        - Higher fundamental intensity = higher confidence

        Returns:
            Confidence score 0.0 to 1.0
        """
        # Normalize components
        harmonic_score = min(1.0, num_harmonics / 5.0)  # Cap at 5 harmonics
        intensity_score = min(1.0, fundamental_intensity / 0.5)  # Cap at 0.5 intensity

        # Weighted average
        # NOTE: Fundamental intensity gets 40% weight (not 20%) because:
        # - Real fundamentals are usually the strongest frequency in their series
        # - Weak fundamentals with many harmonics are often false detections
        #   (e.g., detecting 2f as fundamental when f is weak/missing)
        confidence = (
            0.3 * harmonic_score +
            0.3 * decay_score +
            0.4 * intensity_score
        )

        return confidence

    def _remove_overlapping_series(self, series_list: List[Dict]) -> List[Dict]:
        """
        Remove overlapping harmonic series, keeping highest confidence.

        If two series share nodes, keep the one with higher confidence.
        """
        if not series_list:
            return []

        # Sort by confidence (descending)
        series_list.sort(key=lambda s: s['confidence'], reverse=True)

        used_nodes = set()
        filtered_series = []

        for series in series_list:
            # Check if any harmonics already used
            series_nodes = {h['node_id'] for h in series['harmonics']}

            if not series_nodes & used_nodes:  # No overlap
                filtered_series.append(series)
                used_nodes.update(series_nodes)

        return filtered_series

    def _find_fundamentals_via_gcd(self, nodes: List[Dict]) -> List[Dict]:
        """
        Find fundamentals using GCD-based approach (handles missing fundamentals).

        Concept: If we detect frequencies [523, 785, 1046] Hz,
        the GCD ≈ 261 Hz is likely the fundamental, even if weak/missing.

        Args:
            nodes: List of frequency nodes sorted by frequency

        Returns:
            List of harmonic series (same format as _find_harmonic_series)
        """
        if len(nodes) < 3:  # Need at least 3 frequencies for reliable GCD
            return []

        series_list = []

        # Try to find clusters of harmonically-related frequencies
        # For each pair of frequencies, calculate their ratio
        # Look for frequencies that fit f, 2f, 3f, 4f pattern

        for i in range(len(nodes)):
            for j in range(i + 1, min(i + 10, len(nodes))):  # Look at next 10 frequencies
                freq1 = nodes[i]['frequency']
                freq2 = nodes[j]['frequency']

                # Calculate approximate GCD (fundamental frequency)
                # The fundamental should divide both frequencies (approximately)
                ratio = freq2 / freq1

                # If ratio is close to an integer (2, 3, 4...), these might be harmonics
                if ratio < 1.5:  # Too close, skip
                    continue

                for n in range(2, 8):  # Try ratios 2, 3, 4, 5, 6, 7
                    if abs(ratio - n) < 0.1:  # Within 10% of integer ratio
                        # freq1 and freq2 are likely n-th and 1st harmonics of freq1/n
                        potential_f0 = freq1 / 1.0  # freq1 is already the fundamental candidate

                        # Or freq2 is the n-th harmonic, so fundamental is freq2/n
                        potential_f0_alt = freq2 / n

                        # Try both candidates
                        for f0_candidate in [potential_f0, potential_f0_alt]:
                            if f0_candidate < 60:  # Below musical range
                                continue

                            # Find all harmonics of this fundamental
                            harmonics = []
                            harmonic_intensities = []

                            for harmonic_num in range(1, 11):
                                expected_freq = f0_candidate * harmonic_num
                                tolerance = expected_freq * self.frequency_tolerance * 2  # More liberal for GCD

                                for node in nodes:
                                    if abs(node['frequency'] - expected_freq) <= tolerance:
                                        harmonics.append(node)
                                        harmonic_intensities.append(node['intensity'])
                                        break

                            # Need at least 3 harmonics for good GCD detection
                            if len(harmonics) >= 3:
                                # Create series entry
                                decay_score = self._check_exponential_decay(harmonic_intensities)
                                num_harmonics = len(harmonics) - 1

                                # Use harmonics[0] as the "fundamental" node
                                # (might be 2f or 3f, but we'll create a virtual fundamental)
                                confidence = self._calculate_confidence(
                                    num_harmonics,
                                    decay_score,
                                    harmonics[0]['intensity']
                                )

                                # Boost confidence for GCD-detected fundamentals
                                confidence *= 1.2  # 20% boost

                                series_list.append({
                                    'fundamental': harmonics[0],  # Use first detected harmonic as proxy
                                    'harmonics': harmonics,
                                    'num_harmonics': num_harmonics,
                                    'decay_score': decay_score,
                                    'confidence': confidence,
                                    'gcd_based': True  # Mark as GCD-based
                                })
                        break  # Found a good ratio, move to next pair

        # Remove duplicates (same fundamental frequency)
        return self._remove_overlapping_series(series_list)

    def _merge_gcd_and_harmonic_series(self, gcd_series: List[Dict], harmonic_series: List[Dict]) -> List[Dict]:
        """
        Merge GCD-based and traditional harmonic series, preferring GCD for conflicts.

        Args:
            gcd_series: Series detected via GCD
            harmonic_series: Series detected via traditional method

        Returns:
            Combined series list
        """
        # Mark traditional series
        for s in harmonic_series:
            if 'gcd_based' not in s:
                s['gcd_based'] = False

        # Combine both lists
        combined = gcd_series + harmonic_series

        # Remove overlaps, preferring GCD-based (they have higher confidence due to boost)
        return self._remove_overlapping_series(combined)

    def _get_time_in_seconds(self, time_idx: int) -> float:
        """Convert time sample index to seconds."""
        # Get sample rate and window length from first node
        for node_id in self.graph.nodes():
            node_data = self.graph.nodes[node_id]
            if 'time_seconds' in node_data and node_data.get('time_idx') == time_idx:
                return node_data['time_seconds']

        # Fallback: estimate based on window (2/11 seconds per sample)
        return time_idx * (2.0 / 11.0)

    def build_temporal_dag(self, fundamentals_by_time: Dict[int, List[Dict]]) -> nx.DiGraph:
        """
        Build temporal DAG tracking fundamentals across time samples.

        Nodes: Fundamentals at each time
        Edges: Probable continuations (same note continuing)
        Edge weights: Probability based on frequency match and intensity similarity

        Args:
            fundamentals_by_time: Output from analyze_all_time_samples()

        Returns:
            Directed acyclic graph of fundamental progressions
        """
        dag = nx.DiGraph()

        # Add nodes
        for time_idx, fundamentals in fundamentals_by_time.items():
            for fund in fundamentals:
                node_id = f"t{time_idx}_f{fund['node_id']}"
                dag.add_node(
                    node_id,
                    time_idx=time_idx,
                    frequency=fund['frequency'],
                    note=fund['note'],
                    intensity=fund['intensity'],
                    confidence=fund['confidence'],
                    original_node=fund['node_id']
                )

        # Add edges between consecutive time samples
        time_samples = sorted(fundamentals_by_time.keys())

        for i in range(len(time_samples) - 1):
            current_time = time_samples[i]
            next_time = time_samples[i + 1]

            current_funds = fundamentals_by_time[current_time]
            next_funds = fundamentals_by_time[next_time]

            # Connect fundamentals that likely represent same note
            for curr_fund in current_funds:
                curr_node_id = f"t{current_time}_f{curr_fund['node_id']}"

                for next_fund in next_funds:
                    next_node_id = f"t{next_time}_f{next_fund['node_id']}"

                    # Calculate transition probability
                    prob = self._calculate_transition_probability(curr_fund, next_fund)

                    if prob > 0.3:  # Threshold for edge creation
                        dag.add_edge(
                            curr_node_id,
                            next_node_id,
                            weight=prob,
                            frequency_match=abs(curr_fund['frequency'] - next_fund['frequency'])
                        )

        return dag

    def _calculate_transition_probability(self, fund1: Dict, fund2: Dict) -> float:
        """
        Calculate probability that fund1 continues as fund2.

        Based on:
        - Frequency similarity (same note should have same frequency)
        - Intensity continuity (should not jump drastically)

        Returns:
            Probability 0.0 to 1.0
        """
        # Frequency match (within 2% = same note)
        freq_diff = abs(fund1['frequency'] - fund2['frequency'])
        freq_tolerance = fund1['frequency'] * 0.02

        if freq_diff <= freq_tolerance:
            freq_score = 1.0
        else:
            # Exponential decay for frequency mismatch
            freq_score = np.exp(-freq_diff / freq_tolerance)

        # Intensity continuity (should be similar)
        intensity_ratio = min(fund1['intensity'], fund2['intensity']) / \
                         max(fund1['intensity'], fund2['intensity'], 0.001)

        # Weighted probability
        probability = 0.7 * freq_score + 0.3 * intensity_ratio

        return probability

    def get_fundamental_tracks(self, dag: nx.DiGraph) -> List[List[str]]:
        """
        Extract fundamental tracks (note continuations) from temporal DAG.

        Uses longest path finding to identify sustained notes.

        Args:
            dag: Temporal DAG from build_temporal_dag()

        Returns:
            List of tracks, where each track is a list of node IDs
        """
        # Find all paths through the DAG
        # Since it's a DAG, we can use topological sort

        if not dag.nodes():
            return []

        # Find source nodes (no incoming edges)
        sources = [n for n in dag.nodes() if dag.in_degree(n) == 0]

        tracks = []
        for source in sources:
            # Find longest path from this source
            path = self._find_longest_path_from_source(dag, source)
            if len(path) >= 2:  # At least 2 time samples
                tracks.append(path)

        return tracks

    def _find_longest_path_from_source(self, dag: nx.DiGraph, source: str) -> List[str]:
        """Find longest path starting from source node."""
        longest_path = [source]
        current = source

        while True:
            # Get all successors
            successors = list(dag.successors(current))

            if not successors:
                break

            # Choose successor with highest edge weight
            best_successor = max(successors,
                               key=lambda s: dag[current][s]['weight'])

            longest_path.append(best_successor)
            current = best_successor

        return longest_path

    def filter_noise(self, fundamentals_by_time: Dict[int, List[Dict]],
                    min_confidence: float = 0.4,
                    min_duration_samples: int = 2) -> List[Dict]:
        """
        Filter noise using temporal DAG.

        Args:
            fundamentals_by_time: Output from analyze_all_time_samples()
            min_confidence: Minimum confidence score
            min_duration_samples: Minimum duration in time samples

        Returns:
            Filtered list of fundamentals
        """
        # Build temporal DAG
        dag = self.build_temporal_dag(fundamentals_by_time)

        # Get fundamental tracks
        tracks = self.get_fundamental_tracks(dag)

        # Keep fundamentals that:
        # 1. Are part of a track with sufficient duration
        # 2. Have sufficient confidence
        filtered_fundamentals = []
        kept_nodes = set()

        for track in tracks:
            if len(track) >= min_duration_samples:
                for node_id in track:
                    node_data = dag.nodes[node_id]
                    if node_data['confidence'] >= min_confidence:
                        kept_nodes.add(node_data['original_node'])

        # Collect filtered fundamentals
        for time_idx, fundamentals in fundamentals_by_time.items():
            for fund in fundamentals:
                if fund['node_id'] in kept_nodes:
                    filtered_fundamentals.append(fund)

        return filtered_fundamentals
