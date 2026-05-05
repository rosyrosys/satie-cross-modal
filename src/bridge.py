"""Lexical bridge — handcrafted rules translating audio descriptors into image-prompt vocabulary.

This is intentionally NOT a learned function. The rule base is auditable: an expert can read
a Satie audio profile, follow the rules that fire, and understand why a particular image
was generated. See paper §4.6 for methodology.

Editing this file is the primary way to change the system's interpretive choices.

Phrases are compressed to fit within CLIP's 77-token budget when concatenated with the
period/subject/biographical components.
"""

from .audio import percentile


def lexical_bridge(low_level: dict) -> str:
    """Translate low-level audio descriptors into a visual-prompt paragraph."""
    cent_p  = percentile(low_level['spectral_centroid'], 'spectral_centroid')
    tempo_p = percentile(low_level['tempo'], 'tempo')
    dyn_p   = percentile(low_level['dynamic_range'], 'dynamic_range')
    rms_p   = percentile(low_level['rms'], 'rms')
    chunks: list[str] = []

    # Palette — driven by spectral centroid (perceived brightness)
    if cent_p < 0.3:
        chunks.append('muted ochres, silvered blues')
    elif cent_p < 0.6:
        chunks.append('warm gaslight gold, aged ivory')
    else:
        chunks.append('luminous bright contour, warm highlights')

    # Composition rhythm — driven by tempo
    if tempo_p < 0.3:
        chunks.append('quiet horizontal, slow rhythm, sparse')
    elif tempo_p < 0.6:
        chunks.append('balanced gentle oscillation')
    else:
        chunks.append('animated rhythmic, restless surface')

    # Surface treatment — driven by dynamic range
    if dyn_p < 0.3:
        chunks.append('flat fresco surface')
    else:
        chunks.append('layered painterly surface')

    # Mood — driven by RMS (overall energy)
    if rms_p < 0.3:
        chunks.append('ceremonial stillness, evening light')
    elif rms_p < 0.7:
        chunks.append('soft half-lit interior')
    else:
        chunks.append('charged vivid presence')

    return ', '.join(chunks)
