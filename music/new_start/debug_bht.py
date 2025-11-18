"""Debug BHT/MHT chord detection to understand template matching."""

import numpy as np
import matplotlib.pyplot as plt
from bht_chord_detector import build_chord_templates


# Setup frequencies
A0 = 27.5
frequencies = A0 * 2**(np.arange(-1, 89) / 12.0)

print("Frequency bins:")
print(f"  Total bins: {len(frequencies)}")
print(f"  Range: {frequencies[0]:.2f} Hz to {frequencies[-1]:.2f} Hz")
print(f"  Bins near C4 (261.63 Hz):")

C4_freq = 261.63
for i, f in enumerate(frequencies):
    if 250 < f < 275:
        print(f"    Bin {i}: {f:.2f} Hz (diff from C4: {abs(f-C4_freq):.2f} Hz)")

# Build templates
print("\nBuilding C_major template...")
templates = build_chord_templates(
    frequencies,
    chord_types=['major'],
    template_type='gaussian',
    sigma_hz=10.0
)

h_C = templates['C_major']
h_Ds = templates['D#_major']

print(f"\nC_major template:")
print(f"  Norm: {np.linalg.norm(h_C):.6f}")
print(f"  Sum: {np.sum(h_C):.6f}")
print(f"  Max: {np.max(h_C):.6f}")
print(f"  Non-zero bins: {np.sum(h_C > 0.01)}")

print(f"\nD#_major template:")
print(f"  Norm: {np.linalg.norm(h_Ds):.6f}")
print(f"  Sum: {np.sum(h_Ds):.6f}")
print(f"  Max: {np.max(h_Ds):.6f}")
print(f"  Non-zero bins: {np.sum(h_Ds > 0.01)}")

# Find where C_major template has peaks
peaks_C = np.where(h_C > 0.01)[0]
print(f"\nC_major template peaks (template > 0.01):")
for idx in peaks_C[:15]:  # Show first 15 peaks
    print(f"  Bin {idx}: f={frequencies[idx]:.2f} Hz, h={h_C[idx]:.4f}")

# Find where D#_major template has peaks
peaks_Ds = np.where(h_Ds > 0.01)[0]
print(f"\nD#_major template peaks (template > 0.01):")
for idx in peaks_Ds[:15]:  # Show first 15 peaks
    print(f"  Bin {idx}: f={frequencies[idx]:.2f} Hz, h={h_Ds[idx]:.4f}")

# Generate C major spectrum manually
print("\n" + "="*60)
print("Generating C major chord spectrum manually...")
C4_idx = np.argmin(np.abs(frequencies - 261.63))
E4_idx = np.argmin(np.abs(frequencies - 329.63))
G4_idx = np.argmin(np.abs(frequencies - 392.00))

print(f"  C4: freq={frequencies[C4_idx]:.2f} Hz, bin={C4_idx}")
print(f"  E4: freq={frequencies[E4_idx]:.2f} Hz, bin={E4_idx}")
print(f"  G4: freq={frequencies[G4_idx]:.2f} Hz, bin={G4_idx}")

# Create simple spectrum (just 3 peaks)
spectrum = np.zeros(len(frequencies))
sigma = 5.0
for idx, amp in [(C4_idx, 100), (E4_idx, 80), (G4_idx, 60)]:
    gaussian = amp * np.exp(-(frequencies - frequencies[idx])**2 / (2*sigma**2))
    spectrum += gaussian

# Add small noise
spectrum += 1.0 * np.abs(np.random.randn(len(frequencies)))

print("\nSpectrum peaks:")
for idx in [C4_idx, E4_idx, G4_idx]:
    print(f"  Bin {idx}: f={frequencies[idx]:.2f} Hz, A={spectrum[idx]:.2f}")

# Calculate background and noise
B = np.median(spectrum)
D = (spectrum - B)**2
M = np.mean(D)
S = np.std(D)
outlier_threshold = M + 3*S
mask = D < outlier_threshold
sigma_noise = np.sqrt(np.mean(D[mask]))

print(f"\nNoise statistics:")
print(f"  Background B: {B:.3f}")
print(f"  Noise σ: {sigma_noise:.3f}")
print(f"  Outliers rejected: {np.sum(~mask)}/{len(mask)}")

# Manual SNR calculation for C_major
numerator_C = np.sum((spectrum - B) * h_C)
denominator_C = sigma_noise * np.linalg.norm(h_C)
snr_C = numerator_C / denominator_C

print(f"\nC_major SNR calculation:")
print(f"  Numerator: Σ[(A-B)·h] = {numerator_C:.2f}")
print(f"  Denominator: σ·||h|| = {denominator_C:.2f}")
print(f"  SNR: {snr_C:.2f}")

# Manual SNR calculation for D#_major
numerator_Ds = np.sum((spectrum - B) * h_Ds)
denominator_Ds = sigma_noise * np.linalg.norm(h_Ds)
snr_Ds = numerator_Ds / denominator_Ds

print(f"\nD#_major SNR calculation:")
print(f"  Numerator: Σ[(A-B)·h] = {numerator_Ds:.2f}")
print(f"  Denominator: σ·||h|| = {denominator_Ds:.2f}")
print(f"  SNR: {snr_Ds:.2f}")

# Check if templates overlap with spectrum peaks
print("\n" + "="*60)
print("Checking template-spectrum alignment...")
print(f"\nC_major template at spectrum peaks:")
print(f"  h[C4_bin={C4_idx}] = {h_C[C4_idx]:.4f}")
print(f"  h[E4_bin={E4_idx}] = {h_C[E4_idx]:.4f}")
print(f"  h[G4_bin={G4_idx}] = {h_C[G4_idx]:.4f}")

print(f"\nD#_major template at spectrum peaks:")
print(f"  h[C4_bin={C4_idx}] = {h_Ds[C4_idx]:.4f}")
print(f"  h[E4_bin={E4_idx}] = {h_Ds[E4_idx]:.4f}")
print(f"  h[G4_bin={G4_idx}] = {h_Ds[G4_idx]:.4f}")

# Plot comparison
fig, axes = plt.subplots(3, 1, figsize=(14, 10))

# Plot spectrum
ax = axes[0]
ax.plot(frequencies, spectrum, 'k-', linewidth=1, label='Spectrum')
ax.axvline(frequencies[C4_idx], color='r', linestyle='--', alpha=0.5, label=f'C4 ({frequencies[C4_idx]:.1f} Hz)')
ax.axvline(frequencies[E4_idx], color='g', linestyle='--', alpha=0.5, label=f'E4 ({frequencies[E4_idx]:.1f} Hz)')
ax.axvline(frequencies[G4_idx], color='b', linestyle='--', alpha=0.5, label=f'G4 ({frequencies[G4_idx]:.1f} Hz)')
ax.set_xlim([200, 500])
ax.set_xlabel('Frequency (Hz)')
ax.set_ylabel('Amplitude')
ax.set_title('Generated C Major Spectrum')
ax.legend()
ax.grid(True, alpha=0.3)

# Plot C_major template
ax = axes[1]
ax.plot(frequencies, h_C, 'r-', linewidth=2, label='C_major template')
ax.axvline(frequencies[C4_idx], color='r', linestyle='--', alpha=0.3)
ax.axvline(frequencies[E4_idx], color='g', linestyle='--', alpha=0.3)
ax.axvline(frequencies[G4_idx], color='b', linestyle='--', alpha=0.3)
ax.set_xlim([200, 500])
ax.set_xlabel('Frequency (Hz)')
ax.set_ylabel('Template Value')
ax.set_title(f'C Major Template (SNR={snr_C:.2f})')
ax.legend()
ax.grid(True, alpha=0.3)

# Plot D#_major template
ax = axes[2]
ax.plot(frequencies, h_Ds, 'orange', linewidth=2, label='D#_major template')
ax.axvline(frequencies[C4_idx], color='r', linestyle='--', alpha=0.3)
ax.axvline(frequencies[E4_idx], color='g', linestyle='--', alpha=0.3)
ax.axvline(frequencies[G4_idx], color='b', linestyle='--', alpha=0.3)
ax.set_xlim([200, 500])
ax.set_xlabel('Frequency (Hz)')
ax.set_ylabel('Template Value')
ax.set_title(f'D# Major Template (SNR={snr_Ds:.2f})')
ax.legend()
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('debug_template_alignment.png', dpi=150)
print(f"\nSaved debug plot to: debug_template_alignment.png")
