"""Audio loading and feature extraction for the Satie cross-modal pipeline.

Two feature families:
1. Global semantic embedding via CLAP (laion/clap-htsat-unfused, 512-dim)
2. Low-level descriptors via librosa (tempo, spectral centroid, MFCC, chroma, RMS, dynamic range)
"""

from pathlib import Path
import numpy as np
import torch
import librosa


def find_satie_audio(audio_dir: Path) -> dict[str, Path]:
    """Auto-match audio files in ``audio_dir`` to canonical piece names by keyword."""
    exts = ('*.mp3', '*.wav', '*.ogg', '*.flac', '*.m4a')
    files = sorted(p for ext in exts for p in audio_dir.glob(ext))

    keywords = {
        'gymnopedie_1': ('gymnop', 'gym1', 'gymnopedie'),
        'gnossienne_1': ('gnoss', 'gnossienne'),
        'vexations':    ('vex',),
    }

    matched: dict[str, Path] = {}
    for canonical, keys in keywords.items():
        for f in files:
            n = f.name.lower()
            if any(k in n for k in keys):
                matched[canonical] = f
                break
    return matched


def _tempo(y: np.ndarray, sr: int) -> float:
    """Version-agnostic tempo extraction (librosa 0.10 / 0.11 compatible)."""
    fn = getattr(librosa.feature, 'tempo', None) or getattr(librosa.beat, 'tempo', None)
    if fn is None:
        raise RuntimeError("librosa: no tempo function found")
    return float(np.atleast_1d(fn(y=y, sr=sr))[0])


def low_level_features(audio_path: Path, max_seconds: float = 60.0) -> dict:
    """Compute librosa low-level descriptors for one audio file."""
    y, sr = librosa.load(str(audio_path), sr=22050, mono=True, duration=max_seconds)
    rms = librosa.feature.rms(y=y)[0]
    sc = librosa.feature.spectral_centroid(y=y, sr=sr)
    return {
        'tempo':             _tempo(y, sr),
        'spectral_centroid': float(np.mean(sc)),
        'spectral_flux':     float(np.mean(np.abs(np.diff(sc, axis=1)))),
        'mfcc_mean':         librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13).mean(axis=1).tolist(),
        'chroma_mean':       librosa.feature.chroma_cqt(y=y, sr=sr).mean(axis=1).tolist(),
        'rms':               float(np.mean(rms)),
        'dynamic_range':     float(np.percentile(rms, 95) - np.percentile(rms, 5)),
    }


class CLAPEncoder:
    """Lazy-loaded CLAP encoder. Reuse the instance across multiple files."""

    def __init__(self, model_name: str = 'laion/clap-htsat-unfused', device: str | None = None):
        from transformers import ClapModel, ClapProcessor
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = ClapModel.from_pretrained(model_name).to(self.device).eval()
        self.proc = ClapProcessor.from_pretrained(model_name)

    @torch.no_grad()
    def embed(self, audio_path: Path, sr: int = 48000, duration: float = 30.0) -> np.ndarray:
        y, _ = librosa.load(str(audio_path), sr=sr, mono=True, duration=duration)
        inputs = self.proc(audio=y, sampling_rate=sr, return_tensors='pt').to(self.device)
        e = self.model.get_audio_features(**inputs).squeeze(0).float().cpu().numpy()
        return e / (np.linalg.norm(e) + 1e-8)


# Reference distribution (rough priors over solo piano music; see paper §4.2)
REF_STATS = {
    'tempo':              (60.0, 90.0, 130.0),  # p10, median, p90
    'spectral_centroid':  (900.0, 1500.0, 2400.0),
    'rms':                (0.02, 0.05, 0.12),
    'dynamic_range':      (0.02, 0.05, 0.10),
}


def percentile(value: float, key: str) -> float:
    """Map a raw descriptor value to a [0, 1] percentile against the reference distribution."""
    p10, p50, p90 = REF_STATS[key]
    if value <= p10:
        return 0.05
    if value <= p50:
        return 0.05 + 0.45 * (value - p10) / (p50 - p10)
    if value <= p90:
        return 0.5 + 0.4 * (value - p50) / (p90 - p50)
    return 0.95
