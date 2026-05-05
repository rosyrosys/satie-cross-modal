"""Main entry point: generate one or more Satie visualisations.

Usage:
    python -m src.generate                                  # all 3 pieces
    python -m src.generate --piece gymnopedie_1             # one piece
    python -m src.generate --ip-adapter-scale 0.7 --steps 40
"""

from __future__ import annotations
import argparse
from pathlib import Path
import torch

from .audio import find_satie_audio, low_level_features, CLAPEncoder
from .prompts import build_prompt, build_negative
from .pipeline import build_pipeline, load_reference_images, REF_GROUPS


# Per-piece random seeds (composition years, for reproducibility)
SEEDS = {'gymnopedie_1': 1888, 'gnossienne_1': 1890, 'vexations': 1893}

# Per-piece IP-Adapter strength. Higher = stronger reference-image style grounding,
# but weakens prompt fidelity. Tuned for the current SUBJECT_PHRASES directions:
# - Gymnopédie aims at Khnopff/Delville drama (sunset+grid+obelisk) — refs are
#   Puvis-leaning so we keep scale modest, letting prompt drive the new direction.
# - Gnossienne aims at Puvis 3-figures lakeside — refs match well, allow stronger.
# - Vexations aims at empty corridor — no refs match, keep low so prompt dominates.
PER_PIECE_IP_SCALE = {
    'gymnopedie_1': 0.40,
    'gnossienne_1': 0.60,
    'vexations':    0.30,
}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--piece', choices=list(SEEDS), help='Generate only this piece (default: all)')
    p.add_argument('--audio-dir', default='data/audio', type=Path)
    p.add_argument('--refs-dir', default='data/refs', type=Path)
    p.add_argument('--out-dir', default='data/outputs', type=Path)
    p.add_argument('--steps', type=int, default=30, help='Diffusion inference steps')
    p.add_argument('--guidance-scale', type=float, default=6.5)
    p.add_argument('--ip-adapter-scale', type=float, default=0.55)
    p.add_argument('--width', type=int, default=768)
    p.add_argument('--height', type=int, default=768)
    p.add_argument('--no-ip-adapter', action='store_true', help='Disable IP-Adapter even if refs are present')
    p.add_argument('--memory-efficient', action=argparse.BooleanOptionalAction, default=False,
                   help='CPU offload — only needed if VRAM < 12GB. Off by default on T4 (15GB) for IP-Adapter compat.')
    return p.parse_args()


def main() -> int:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Audio discovery
    audio = find_satie_audio(args.audio_dir)
    if not audio:
        print(f'No audio found in {args.audio_dir}. Drop Satie mp3s there and rerun.')
        return 1

    pieces = [args.piece] if args.piece else list(audio)
    pieces = [p for p in pieces if p in audio]
    print(f'Pieces to render: {pieces}')

    # 2. Audio feature extraction
    print('Extracting audio features (CLAP + librosa)...')
    clap = CLAPEncoder()
    feats = {}
    for name in pieces:
        ll = low_level_features(audio[name])
        feats[name] = {'low_level': ll, 'clap': clap.embed(audio[name])}
        print(f'  {name:18s} tempo={ll["tempo"]:6.1f}  centroid={ll["spectral_centroid"]:7.1f}  rms={ll["rms"]:.3f}')

    # 3. Prompt construction
    prompts = {n: build_prompt(n, f['low_level']) for n, f in feats.items()}

    # 4. Reference images (optional)
    refs = load_reference_images(args.refs_dir) if args.refs_dir.exists() else {}
    use_ip_adapter = bool(refs) and not args.no_ip_adapter
    print(f'Reference images: {len(refs)} loaded; IP-Adapter {"ON" if use_ip_adapter else "OFF"}')

    # 5. Build SDXL pipeline
    print('Loading SDXL...')
    pipe = build_pipeline(
        use_ip_adapter=use_ip_adapter,
        ip_adapter_scale=args.ip_adapter_scale,
        memory_efficient=args.memory_efficient,
    )
    print('SDXL ready.')

    # 6. Generate
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    for name in pieces:
        kwargs = dict(
            prompt=prompts[name],
            negative_prompt=build_negative(name),
            generator=torch.Generator(device=device).manual_seed(SEEDS.get(name, 0)),
            num_inference_steps=args.steps,
            guidance_scale=args.guidance_scale,
            height=args.height,
            width=args.width,
        )
        if use_ip_adapter:
            piece_refs = [refs[k.lower()] for k in REF_GROUPS.get(name, []) if k.lower() in refs]
            if piece_refs:
                # diffusers expects: outer list = num_ip_adapters (1 here), inner = images for that adapter
                kwargs['ip_adapter_image'] = [piece_refs]
                # Per-piece IP-Adapter strength (overrides the pipeline-level default)
                pipe.set_ip_adapter_scale(PER_PIECE_IP_SCALE.get(name, args.ip_adapter_scale))

        print(f'>> generating {name}... (ip_scale={PER_PIECE_IP_SCALE.get(name, args.ip_adapter_scale) if use_ip_adapter else "off"})')
        img = pipe(**kwargs).images[0]
        out = args.out_dir / f'{name}.png'
        img.save(out)
        print(f'   saved {out}')

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
