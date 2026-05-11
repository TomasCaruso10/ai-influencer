"""Post-processing pipeline: humanization + resizing + (placeholder) upscaling.

Quick reference:
    from aiinfluencer.post_process import humanize, resize_for_channel, Channel

    # Humanization (grain + chromatic aberration + vignetting)
    humanized = humanize(Path("raw.png"), Path("out.png"), grain_iso=600)

    # Resize a aspect ratio del canal
    resize_for_channel(Path("in.png"), Path("ig.jpg"), channel=Channel.IG_FEED)
"""

from aiinfluencer.post_process.humanization import HumanizationConfig, humanize
from aiinfluencer.post_process.resizing import Channel, resize_for_channel

__all__ = ["humanize", "HumanizationConfig", "resize_for_channel", "Channel"]
