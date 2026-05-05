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
        'three pale draped figures only, sparse procession across ochre plane, '
        'frieze in the manner of Puvis de Chavannes'
    ),
    'gnossienne_1': (
        'single robed figure in 1890s candlelit oriental corridor, '
        'dusty mosaic tile, arched openings, ceremonial mystery'
    ),
    'vexations': (
        'completely empty silent room, no people, deserted interior, '
        'dim grey-blue monochrome, abandoned, in the manner of Whistler nocturnes'
    ),
}

# Biographical anchors — the moment in Satie's life the piece emerged from (compressed)
BIOGRAPHICAL_ANCHORS = {
    'gymnopedie_1': '1888, pre-romantic bohemian loneliness',
    'gnossienne_1': '1890, imagined Orient, intensified solitude',
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
    'vexations': 'people, figures, crowd, cafe, conversation, multiple figures, ',
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
