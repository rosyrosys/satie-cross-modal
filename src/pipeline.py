"""Stable Diffusion XL pipeline with optional IP-Adapter conditioning.

Memory-efficient by default (sequential CPU offload + VAE slicing) so the pipeline
fits on a free Colab T4 (16GB) or a 12GB consumer GPU.
"""

from pathlib import Path
import gc
import torch
from PIL import Image


def load_reference_images(refs_dir: Path, target_size: int = 512) -> dict[str, Image.Image]:
    """Load all jpg/png from ``refs_dir`` and resize to a square."""
    refs: dict[str, Image.Image] = {}
    for ext in ('*.jpg', '*.jpeg', '*.png'):
        for p in sorted(refs_dir.glob(ext)):
            refs[p.stem.lower()] = Image.open(p).convert('RGB').resize((target_size, target_size))
    return refs


# Per-piece reference image groups (filename stems, lowercase)
# Reassigned to match new SUBJECT_PHRASES directions:
# - Gymnopédie now targets Khnopff/Delville drama → Symbolist refs (Moreau, Redon, Whistler)
# - Gnossienne now targets Puvis lakeside → Puvis-heavy refs
# - Vexations targets empty corridor → minimal refs (Whistler atmosphere only) so
#   IP-Adapter doesn't smuggle figures back into the empty room.
REF_GROUPS = {
    'gymnopedie_1': ['moreau_galatea', 'redon_closed_eyes', 'whistler_nocturne'],
    'gnossienne_1': ['puvis_sacred_grove', 'puvis_summer', 'redon_closed_eyes'],
    'vexations':    ['whistler_nocturne', 'redon_closed_eyes'],
}


def build_pipeline(
    use_ip_adapter: bool = True,
    sdxl_model: str = 'stabilityai/stable-diffusion-xl-base-1.0',
    vae_model: str = 'madebyollin/sdxl-vae-fp16-fix',
    ip_adapter_repo: str = 'h94/IP-Adapter',
    ip_adapter_weight: str = 'ip-adapter_sdxl.bin',
    ip_adapter_scale: float = 0.55,
    memory_efficient: bool = True,
):
    """Construct the SDXL + (optional) IP-Adapter pipeline.

    Parameters
    ----------
    use_ip_adapter : load IP-Adapter weights (requires reference images at generation time)
    memory_efficient : enable sequential CPU offload + VAE slicing/tiling for 12-16GB GPUs
    """
    from diffusers import StableDiffusionXLPipeline, AutoencoderKL

    torch.cuda.empty_cache(); gc.collect()
    dtype = torch.float16

    vae = AutoencoderKL.from_pretrained(vae_model, torch_dtype=dtype)
    pipe = StableDiffusionXLPipeline.from_pretrained(
        sdxl_model, vae=vae, torch_dtype=dtype, variant='fp16', use_safetensors=True
    )

    # Load IP-Adapter BEFORE enabling offload so its image_encoder gets registered
    # in the offload hook chain (otherwise its weights stay on CPU while inputs go to CUDA).
    if use_ip_adapter:
        pipe.load_ip_adapter(ip_adapter_repo, subfolder='sdxl_models', weight_name=ip_adapter_weight)
        pipe.set_ip_adapter_scale(ip_adapter_scale)

    if memory_efficient:
        # model_cpu_offload (whole-module) is more compatible with IP-Adapter than
        # sequential_cpu_offload (per-layer), which leaves the CLIP image encoder
        # in a mixed cuda/meta state and breaks torch.cat in vision embeddings.
        pipe.enable_model_cpu_offload()
        pipe.enable_vae_slicing()
        pipe.enable_vae_tiling()
    else:
        pipe = pipe.to('cuda')

    return pipe
