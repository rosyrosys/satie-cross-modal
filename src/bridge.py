"""Lexical bridge — handcrafted rules translating audio descriptors into image-prompt vocabulary.

This is intentionally NOT a learned function. The rule base is auditable: an expert can read
a Satie audio profile, follow the rules that fire, and understand why a particular image
was generated. See paper §4.6 for methodology.

Editing this file is the primary way to change the system's interpretive choices.
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
        chunks.append('muted palette of dusty ochres, silvered blues, and greyed greens')
    elif cent_p < 0.6:
        chunks.append('warm palette of gaslight gold, deep maroon, and aged ivory')
    else:
        chunks.append('luminous palette with bright contour lines and warm highlights')

    # Composition rhythm — driven by tempo
    if tempo_p < 0.3:
        chunks.append('quiet horizontal composition, slow visual rhythm, sparsely populated')
    elif tempo_p < 0.6:
        chunks.append('balanced composition with gentle oscillating rhythm')
    else:
        chunks.append('animated composition, rhythmic colour blocks, restless surface')

    # Surface treatment — driven by dynamic range
    if dyn_p < 0.3:
        chunks.append('flat surface treatment in the manner of a fresco')
    else:
        chunks.append('layered painterly surface with subtle textural inflection')

    # Mood — driven by RMS (overall energy)
    if rms_p < 0.3:
        chunks.append('an air of ceremonial stillness, evening light')
    elif rms_p < 0.7:
        chunks.append('a soft interior mood, half-lit')
    else:
        chunks.append('a charged atmosphere, vivid presence')

    return ', '.join(chunks)
