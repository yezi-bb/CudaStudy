# oct-cuda-pipeline

Independent reimplementation of a spectral-domain OCT GPU pipeline
(windowing, FFT/log, scan conversion, optional attenuation skeleton).
Not affiliated with any commercial IV-OCT product.

## Compliance

- No vendor DLLs, no reverse engineering, no patient or calibration dumps.
- Algorithms follow public literature and synthetic data only.
- Module names: oct::Context, ResampleWindow, FftLog, TransposeCrop,
  Dsc, EnhanceColor, PullbackBatch, Calib, Detect, StitchContCalib, Ipa.

## Layout

- include/oct — public headers
- src/host — C++ (no <<<>>>)
- src/kernels — CUDA .cu (from Week02)
- tests / bench / docs

## Build

cmake -S . -B build -A x64
cmake --build build --config Release