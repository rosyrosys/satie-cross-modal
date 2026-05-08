"""Prompt construction — period anchor, biographical anchors, subject phrases, negatives.

The biographical anchors are the system's interpretive contribution. They are NOT mechanical
inferences from the audio — they are editorial choices made in collaboration with a musicologist.
Edit BIOGRAPHICAL_ANCHORS to change the system's reading of a piece.

See paper §4.4 (Biographical Anchoring).

Compressed to fit within CLIP's 77-token limit; longer phrases were silently truncated upstream.
"""

from .bridge import lexical_bridge

# Diegetic frame — fixed across all pieces (compressed: 30→8 tokens)
PERIOD_ANCHOR = 'fin-de-siecle Parisian Symbolist painting, 1890s'

# Per-piece subject phrases — visual ideas, editorial choices
SUBJECT_PHRASES = {
    'gymnopedie_1': (
        'a lone man in dark fin-de-siecle coat walking slowly along a quiet country path, '
        'low horizon, sparse trees, golden silent dawn, contemplative solitude, '
        'in the manner of Khnopff and Symbolist landscape'
    ),
    'gnossienne_1': (
        'three pale draped figures in solemn procession beside still lakeside, '
        'hooded contemplation, earth-tone palette, in the manner of Puvis de Chavannes'
    ),
    'vexations': (
        'endless wood-paneled corridor in fin-de-siecle Parisian interior, '
        'deep one-point perspective, vanishing point, sunlit boiserie, '
        'dim grey monochrome chiaroscuro, no people, painterly oil'
    ),
}

# Biographical anchors — the moment in Satie's life the piece emerged from (compressed)
BIOGRAPHICAL_ANCHORS = {
    'gymnopedie_1': '1888, pre-romantic bohemian loneliness',
    'gnossienne_1': '1890, modal solitude, contemplation before love',
    'vexations':    '1893, mourning Valadon departure, obsessive grief',
}

NEGATIVE = (
    'photograph, photographic, lens flare, modern digital art, neon, '
    'high-saturation digital colour, contemporary typography, 3D render, '
    'cgi, hdr, cinematic lighting, Wagnerian opera, Bayreuth, '
    'anime, manga, watermark, signature, text, blurry, lowres, '
    'art deco, 1920s, geometric repeated pattern'
)

# Per-piece extra negatives prepended to the global NEGATIVE.
PIECE_NEGATIVES = {
    'gymnopedie_1': 'multiple figures, three figures, group of people, crowd, procession of figures, ',
    'vexations':    'people, figures, crowd, cafe, conversation, multiple figures, '
                    'furniture, table, chair, painting on wall, ',
}


def build_prompt(piece: str, low_level: dict) -> str:
    """Compose the full prompt — subject first (concrete visual content), then
    biographical anchor (interpretive), then period (style), then audio-driven mood.
    Order chosen so the most semantically critical parts survive CLIP's 77-token cut."""
    subject = SUBJECT_PHRASES.get(piece, 'a fin-de-siecle Parisian interior')
    biographical = BIOGRAPHICAL_ANCHORS.get(piece, '')
    mood = lexical_bridge(low_level)
    parts = [subject]
    if biographical:
        parts.append(biographical)
    parts.append(PERIOD_ANCHOR)
    parts.append(mood)
    return '; '.join(parts)


def build_negative(piece: str) -> str:
    """Combine piece-specific extra negatives with the global NEGATIVE."""
    return PIECE_NEGATIVES.get(piece, '') + NEGATIVE
