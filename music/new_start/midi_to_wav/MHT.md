# Mathematical Techniques for Space Object Detection
## Binary Hypothesis Test (BHT) and Multi-Hypothesis Test (MHT)

*Summary from: "Measuring Angular Rate of Celestial Objects Using the Space Surveillance Telescope"  
by Captain Anthony J. Sligar, USAF (AFIT, March 2015)*

---

## Overview

Both BHT and MHT are **matched-filter detection algorithms** based on Signal-to-Noise Ratio (SNR) compared against a threshold value. They determine whether a space object is present in telescope imagery by comparing likelihood ratios of competing hypotheses.

---

## 1. Binary Hypothesis Test (BHT)

### 1.1 Fundamental Concept

The BHT evaluates two competing hypotheses for each pixel:
- **H₀**: No object present in the pixel (null hypothesis)
- **H₁**: Object present in the pixel (alternative hypothesis)

### 1.2 Likelihood Ratio Test (LRT)

The basic BHT is expressed as a Likelihood Ratio Test:

```
         P(d(x,y) ∀(x,y) ∈ [1,Md]|H₁)   H₁
Λ =  ────────────────────────────────  ≷  1
         P(d(x,y) ∀(x,y) ∈ [1,Md]|H₀)   H₀
```

Where:
- `d(x,y)` = image data at pixel coordinates (x,y)
- `Md` = number of pixels in one dimension of the square window
- `P(d(x,y)|Hᵢ)` = joint conditional probability of data given hypothesis Hᵢ

### 1.3 Gaussian Noise Model

Using a Gaussian distribution to model the noise, the LRT becomes:

```
        Md  Md
        ∏   ∏   (1/√(2πσ)) exp{-1/(2σ²) [d(w,z) - B - θh(w,z)]²}   H₁
ΛG =   w=1 z=1                                                        ≷  1
        Md  Md                                                        H₀
        ∏   ∏   (1/√(2πσ)) exp{-1/(2σ²) [d(w,z) - B]²}
        w=1 z=1
```

Where:
- `w, z` = pixel locations in the window
- `σ` = standard deviation of noise
- `B` = background noise level (local sample median)
- `θ` = space object's irradiance
- `h(w,z)` = Point Spread Function (PSF)

### 1.4 Background Noise Calculation

**Background level (B):**
```
B = median[d(w,z)] ∀(w,z) ∈ [1,Md]
```

**Standard deviation (σ):**
```
         ___________________________________
        /  Md  Md
       /   ∑   ∑  (d²(w,z) - B)²
σ =   /   w=1 z=1
    \/    ───────────────────────
                  Md²
```

### 1.5 Log-Likelihood Ratio (LLR)

Taking the natural logarithm simplifies the expression:

```
       Md  Md
log(ΛG) = ∑   ∑   1/√(2πσ) [-2B·θh(w,z) + 2d(w,z)·θh(w,z) - (θh(w,z))²]  H₁
          w=1 z=1                                                          ≷ 0
                                                                           H₀
```

This simplifies further to:

```
  Md  Md                              H₁      θ   Md  Md
  ∑   ∑  (d(w,z) - B)h(w,z)           ≷     ───  ∑   ∑  h²(w,z)
 w=1 z=1        σ                     H₀      2σ w=1 z=1
```

### 1.6 SNR Formulation for Point Detector

For the **baseline point detector** where PSF is a delta function `δ(w - cₓ, z - cᵧ)`:

```
              Md  Md
              ∑   ∑  (d(w,z) - B)δ(w - cₓ, z - cᵧ)      (d(cₓ, cᵧ) - B)    H₁
SNRbaseline = w=1 z=1                                  = ─────────────────  ≷  γ
              ────────────────────────────────────          σ                H₀
                        ______________
                       /  Md  Md
              σ      \/   ∑   ∑  δ(w,z)
                          w=1 z=1
```

Where:
- `γ` = detection threshold (typically γ = 6 for SST)
- `(cₓ, cᵧ)` = pixel coordinates being tested

### 1.7 Probability of False Alarm

For threshold γ = 6, assuming Gaussian noise with zero mean and unit variance:

```
              ∞
P_FA = ∫    (1/√(2π)) exp(-t²/2) dt = 9.87 × 10⁻¹⁰
           6
```

---

## 2. Multi-Hypothesis Test (MHT)

### 2.1 Fundamental Concept

MHT extends BHT by considering **nine different hypotheses** (H₁ through H₉) representing different sub-pixel positions, plus the null hypothesis H₀.

**Key Innovation**: Accounts for the fact that objects may not be centered perfectly on a pixel, causing the sampled PSF shape to vary.

### 2.2 Nine Hypotheses Generation

The nine hypotheses are created by shifting the system PSF by ±15μm (half-pixel) horizontally and vertically:

| Hypothesis | Horizontal Shift (αₐ) | Vertical Shift (βₐ) |
|------------|------------------------|----------------------|
| H₁         | -15μm                  | -15μm                |
| H₂         | 0                      | -15μm                |
| H₃         | +15μm                  | -15μm                |
| H₄         | -15μm                  | 0                    |
| H₅         | 0                      | 0                    |
| H₆         | +15μm                  | 0                    |
| H₇         | -15μm                  | +15μm                |
| H₈         | 0                      | +15μm                |
| H₉         | +15μm                  | +15μm                |

### 2.3 MHT SNR Equation

For each hypothesis Hₐ:

```
            Md  Md
            ∑   ∑  (d(w,z) - B)hsamp(w - cₓ - αₐ, z - cᵧ - βₐ)    Hₐ
SNRₐ =     w=1 z=1                                                  ≷  γMHT
           ──────────────────────────────────────────────────       H₀
                    _______________
                   /  Md  Md
           σ     \/   ∑   ∑  h²samp(w,z)
                      w=1 z=1
```

Where:
- `hsamp(w,z)` = sampled (downsampled) PSF
- `αₐ, βₐ` = sub-pixel shifts for hypothesis a
- `γMHT` = detection threshold (γMHT = 6.2212 for SST)

### 2.4 Hypothesis Selection

The hypothesis with the **maximum SNR** is selected:

```
SNRM-ary = max(SNRₐ) for a ∈ {1, 2, ..., 9}
```

This provides:
1. **Detection decision**: Is an object present?
2. **Sub-pixel location**: Which hypothesis best represents the object's position?

### 2.5 MHT Probability of False Alarm

Considering nine mutually exclusive hypotheses and assuming statistical independence:

```
P_FA(MHT) ≈ 4 × 9.87 × 10⁻¹⁰ = 3.94 × 10⁻⁹
```

To maintain comparable false alarm rate to BHT, threshold is raised to γMHT = 6.2212, yielding P_FA = 9.87 × 10⁻¹⁰.

---

## 3. MHT with Outlier Removal (MHTOR)

### 3.1 Enhanced Noise Calculation

MHTOR improves upon standard MHT by **rejecting outlier noise samples** (e.g., bright stars, cosmic rays) when computing background standard deviation.

### 3.2 Squared Deviations

Compute squared deviations from background:

```
D(m) = (d(m) - B)²
```

Where `m` is a pixel index in the window.

### 3.3 Mean and Standard Deviation of Squared Deviations

**Mean:**
```
M = E[D(m)]
```

**Standard deviation:**
```
         ___________________
        /   Md
       /    ∑  D²(m)
S =   /    m=1              - M²
    \/     ─────────
             Md²
```

### 3.4 Outlier Rejection

Exclude pixels where:
```
D(m) ≥ (M + 3·S)
```

This removes samples outside 3 standard deviations from the mean.

### 3.5 New Standard Deviation (ζ)

Compute new standard deviation `ζ` using only non-outlier pixels, then substitute in the MHT equation:

```
            Md  Md
            ∑   ∑  (d(w,z) - B)hsamp(w - cₓ - αₐ, z - cᵧ - βₐ)    Hₐ
SNRₐ =     w=1 z=1                                                  ≷  γMHT
           ──────────────────────────────────────────────────       H₀
                    _______________
                   /  Md  Md
           ζ     \/   ∑   ∑  h²samp(w,z)
                      w=1 z=1
```

**Effect**: Lowering the normalizing factor (ζ < σ) increases SNR, improving detection performance.

---

## 4. Point Spread Function (PSF) Modeling

### 4.1 System PSF Components

The overall system impulse response combines three transfer functions:

```
hmodel(x,y) = ℱ⁻¹{Hoptics(fx, fy) · Hpixel(fx, fy) · Hatm(fx, fy)}
```

Where:
- `Hoptics` = Optical Transfer Function (accounts for aberrations)
- `Hpixel` = Pixel sampling function
- `Hatm` = Atmospheric transfer function
- `ℱ⁻¹` = Inverse Fourier Transform

### 4.2 Optical Transfer Function

Based on the generalized pupil function with phase aberrations:

```
P(u,v) = A(u,v) · exp[j·E(u,v)]
```

Where:
- `A(u,v)` = aperture function (donut-shaped for SST: 3.5m outer, 1.75m inner diameter)
- `E(u,v)` = wavefront error modeled using Zernike polynomials

**Wavefront error:**
```
E(u,v) = Z₂φ₂(u,v) + Z₃φ₃(u,v) + ... + ZNφN(u,v)
```

- `Zᵢ` = Zernike coefficients (determined empirically for SST)
- `φᵢ(u,v)` = Zernike polynomials

**Optical PSF (via Fraunhofer propagation):**

```
                |∞  ∞                                    |²
hoptics(x,y) = |∫  ∫  P(u,v) exp[j2π(xu + yv)/(λ̄z)] dudv|
                |                                         |
               -∞ -∞
```

**Optical Transfer Function:**
```
Hoptics(fx, fy) = ℱ{hoptics(x,y)}
```

### 4.3 Pixel Transfer Function

Accounts for finite square pixels (30μm × 30μm for SST):

```
Hpixel(fx, fy) = ℱ{rect(ax, ay)}
```

Where `a = 30μm` = pixel size.

### 4.4 Atmospheric Transfer Function

Long-exposure atmospheric effects:

```
                         (  λ̄·z·υ  )⁵/³
Hatm(fx, fy) = exp[-3.44(────────)    ]
                         (   r₀    )
```

Where:
- `υ = √(fx² + fy²)` = radial frequency
- `r₀` = atmospheric coherence diameter (Fried's seeing parameter)
- `λ̄` = mean wavelength of light
- `z` = propagation distance

### 4.5 Sampled PSF (Down-sampled)

To create the nine hypotheses, the modeled PSF is shifted and down-sampled:

```
hsamp(m, Δx, n, Δy) = ∫∫ hmodel(x,y) δ(Lm - x - LΔx, Ln - y - LΔy) dx dy
```

Where:
- `L` = ratio between 30μm SST pixels and Nyquist pixel size
- `Δx, Δy` = sub-pixel shifts

**Sampled irradiance:**
```
isamp(m, Δx, n, Δy) = θ·hsamp(m, Δx, n, Δy) + B
```

---

## 5. Position Determination Algorithms

### 5.1 Centroid Algorithm (Used with BHT)

For detection array D(x,y) containing 1s (detected) and 0s (not detected):

```
         20  20
         ∑   ∑  D(x,y) · x
        x=1 y=1
xcenter = ───────────────────
           20  20
           ∑   ∑  D(x,y)
          x=1 y=1
```

Similarly for ycenter.

**Limitation**: Equal weighting to all detection points; doesn't account for intensity variations.

### 5.2 Center of Intensity (CoI) Algorithm

Uses actual intensity values dSST(x,y) instead of binary detection:

```
         3   3
         ∑   ∑  dSST(x,y) · x
        x=1 y=1
xcenter = ─────────────────────
           3   3
           ∑   ∑  dSST(x,y)
          x=1 y=1
```

**Advantage**: Weights position by intensity, providing more accurate location.

### 5.3 Center of SNR (CoS) Algorithm (Used with MHT)

Uses SNR values from four MHT hypotheses (H₅, H₆, H₈, H₉) mapped to a master matrix that is double the size of the original data window. Centroid operation is performed on this SNR master matrix:

```
         6   6
         ∑   ∑  SNRmaster(i,j) · i
        i=1 j=1
xcenter = ────────────────────────── / 2
            6   6
            ∑   ∑  SNRmaster(i,j)
           i=1 j=1
```

Division by 2 accounts for the doubled matrix size.

**Advantage**: Best position accuracy; provides sub-pixel information from hypothesis selection.

---

## 6. Angular Rate Calculation

### 6.1 Change in Position

Between two successive frames:

```
Δx = x₂ - x₁
Δy = y₂ - y₁

Δxy = √(Δx² + Δy²)
```

### 6.2 Pixel to Radian Conversion

Each pixel represents an angular size:

```
         ( psize )      ( 30μm )
Δθ = tan(──────) = tan(──────) = 8.571 μrad/pixel
         (  f   )      ( 3.5m )
```

Where:
- `psize = 30μm` = effective pixel size (binned 2×2)
- `f = 3.5m` = focal length of SST

### 6.3 Angular Rate

```
       Δθ · Δxy   radians
θ̇ = ────────── [────────]
          t       second
```

Where `t` = time interval between frames (1 second for SST data).

### 6.4 Comparison to True Angular Rate

For stars with known sidereal rate:

```
        2π
θ̇T = ──────────────────────────── = 72.921 μrad/sec
     (23.9344699 hrs × 3600 sec)
```

**Validation metric:**
```
      θ̇calculated
R = ───────────── ≈ 1 (for accurate algorithms)
         θ̇T
```

---

## 7. Statistical Comparison

### 7.1 Expected Value (Accuracy)

Mean of angular rate measurements:

```
E[X] = mean of (θ̇N-1, θ̇N-2, ..., θ̇2, θ̇1)
```

The algorithm with E[X] closest to 1 (or closest to θ̇T) is most accurate.

### 7.2 Variance (Precision)

```
σ² = E[(X - E[X])²]
```

The algorithm with smallest σ² is most consistent/precise.

---

## 8. Key Performance Advantages of MHT over BHT

1. **Detection**: MHT improved probability of detection by up to 50% over BHT
2. **Sub-pixel accuracy**: MHT provides sub-pixel location information (9 possible positions)
3. **Position accuracy**: MHT-based position algorithms (CoS) provide most accurate centroid determination
4. **Angular rate accuracy**: Better position → more accurate angular rate → better orbital track prediction

---

## 9. Summary of Key Equations

### BHT (Point Detector):
```
SNRbaseline = (d(cₓ, cᵧ) - B) / σ  ≷  γ = 6
```

### MHT (Multi-hypothesis):
```
            Md  Md
            ∑   ∑  (d(w,z) - B)hsamp(w - cₓ - αₐ, z - cᵧ - βₐ)
SNRₐ =     w=1 z=1                                               ≷  γMHT = 6.2212
           ─────────────────────────────────────────────────
                    _______________
                   /  Md  Md
           σ     \/   ∑   ∑  h²samp(w,z)
                      w=1 z=1

SNRM-ary = max(SNRₐ)
```

### System PSF:
```
hmodel(x,y) = ℱ⁻¹{Hoptics(fx, fy) · Hpixel(fx, fy) · Hatm(fx, fy)}
```

### Angular Rate:
```
       tan(30μm/3.5m) · √(Δx² + Δy²)
θ̇ = ────────────────────────────────  [rad/sec]
                  t
```

---

## Appendix: Notation Summary

| Symbol | Meaning |
|--------|---------|
| d(x,y) | Image data at pixel (x,y) |
| B | Background noise level (median) |
| σ | Standard deviation of noise |
| ζ | Standard deviation with outliers removed |
| θ | Object irradiance (photon count) |
| h(w,z) | Point Spread Function |
| hsamp | Sampled (downsampled) PSF |
| Md | Number of pixels in one dimension of window |
| γ | Detection threshold |
| SNR | Signal-to-Noise Ratio |
| P_FA | Probability of false alarm |
| H₀ | Null hypothesis (no object) |
| Hₐ | Alternative hypothesis a (object at sub-pixel position) |
| αₐ, βₐ | Horizontal and vertical sub-pixel shifts |
| r₀ | Fried's seeing parameter (atmospheric coherence) |
| λ̄ | Mean wavelength |
| Δx, Δy | Change in pixel position |
| θ̇ | Angular rate |
| E[X] | Expected value (mean) |
| σ² | Variance |