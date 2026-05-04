"""Prompt construction — period anchor, biographical anchors, subject phrases, negatives.

The biographical anchors are the system's interpretive contribution. They are NOT mechanical
inferences from the audio — they are editorial choices made in collaboration with a musicologist.
Edit BIOGRAPHICAL_ANCHORS to change the system's reading of a piece.

See paper §4.4 (Biographical Anchoring).
"""

from .bridge import lexical_bridge

# Diegetic frame — fixed across all pieces
PERIOD_ANCHOR = (
    'Paris between 1880 and 1915, fin-de-siecle Symbolist or Nabis painting, '
    'oil on canvas or coloured lithograph, plate from a contemporary art catalogue'
)

# Per-piece subject phrases — visual ideas, editorial choices
SUBJECT_PHRASES = {
    'gymnopedie_1': (
        'three pale figures in stilled procession across a horizonless ochre plane, '
        'frieze-like, in the manner of Puvis de Chavannes'
    ),
    'gnossienne_1': (
        'a single robed figure in a candlelit corridor of patterned tilework and '
        'arched openings, half-lit ceremonial atmosphere'
    ),
    'vexations': (
        'a single empty interior dissolving into its own repetition, almost monochrome, '
        'in the manner of Whistler nocturnes'
    ),
}

# Biographical anchors — the moment in Satie's life the piece emerged from
BIOGRAPHICAL_ANCHORS = {
    'gymnopedie_1':
        '1888, Auberge du Clou years, five years before the Valadon affair, '
        'the voice of pre-romantic loneliness',
    'gnossienne_1':
        '1890, the year before the Rose+Croix commissions, '
        'modal Orientalism as imagined East, intensified solitude',
    'vexations':
        'late 1893, weeks after Valadon\'s departure on June 20, '
        'the obsessive logic of repetition as grief management',
}

NEGATIVE = (
    'photograph, photographic, lens flare, modern digital art, neon, '
    'high-saturation digital colour, contemporary typography, 3D render, '
    'cgi, hdr, cinematic lighting, Wagnerian opera, Bayreuth, '
    'anime, manga, watermark, signature, text, blurry, lowres'
)


def build_prompt(piece: str, low_level: dict) -> str:
    """Compose the full prompt for one piece by concatenating period + subject + biographical + audio mood."""
    subject = SUBJECT_PHRASES.get(piece, 'a fin-de-siecle Parisian interior')
    biographical = BIOGRAPHICAL_ANCHORS.get(piece, '')
    mood = lexical_bridge(low_level)
    parts = [PERIOD_ANCHOR, subject]
    if biographical:
        parts.append(f'biographical context: {biographical}')
    parts.append(mood)
    return '; '.join(parts)
