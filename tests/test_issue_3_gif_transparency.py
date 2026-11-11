# -*- coding: utf-8 -*-

import io
from os.path import abspath, dirname, join
from unittest import TestCase
from PIL import Image

from thumbor.config import Config
from thumbor.context import Context
from thumbor.engines.pil import Engine

FIXTURES_PATH = abspath(join(dirname(__file__), "fixtures/"))
STORAGE_PATH = join(FIXTURES_PATH, "images")


class GifTransparencyTestCase(TestCase):
    """Test that resized GIFs preserve their transparency index."""

    def get_context(self):
        cfg = Config(
            SECURITY_KEY="ACME-SEC",
            ENGINE="thumbor.engines.pil",
            PILLOW_PRESERVE_INDEXED_MODE=True,
        )
        cfg.LOADER = "thumbor.loaders.file_loader"
        cfg.FILE_LOADER_ROOT_PATH = STORAGE_PATH
        cfg.STORAGE = "thumbor.storages.no_storage"
        return Context(config=cfg)

    def setUp(self):
        self.context = self.get_context()
        self.engine = Engine(self.context)

    def test_gif_transparency_preserved_after_resize(self):
        """Verify that resizing a palette GIF preserves its transparency index."""
        # Load the original sticker GIF
        original_path = join(FIXTURES_PATH, "sticker.gif")
        original = Image.open(original_path)
        
        # Check that the original has a transparency index
        self.assertIsNotNone(original.info.get('transparency'), 
                           "Original GIF must have a transparency index")
        original_transparency_idx = original.info['transparency']
        original_transparent_pixels = 0
        
        # Count transparent pixels in the original
        original_data = list(original.getdata())
        for pixel_idx in original_data:
            if pixel_idx == original_transparency_idx:
                original_transparent_pixels += 1
        
        self.assertGreater(original_transparent_pixels, 0, 
                          "Original GIF must have some transparent pixels")
        
        # Load and resize through the engine
        with open(original_path, 'rb') as f:
            image_bytes = f.read()
        
        self.engine.load(image_bytes, ".gif")
        
        # Resize to a smaller size
        self.engine.resize(60, 40)
        
        # Read back as GIF
        resized_bytes = self.engine.read(extension=".gif", quality=None)
        
        # Check that the resized image has transparency
        resized = Image.open(io.BytesIO(resized_bytes))
        
        # Verify mode is still P (palette)
        self.assertEqual(resized.mode, 'P', 
                        "Resized image should remain in palette mode")
        
        # Check that transparency index exists
        resized_transparency_idx = resized.info.get('transparency')
        self.assertIsNotNone(resized_transparency_idx,
                           "Resized GIF must preserve transparency index, not create opaque black box")
        
        # Count transparent pixels in the resized version
        resized_data = list(resized.getdata())
        resized_transparent_pixels = 0
        for pixel_idx in resized_data:
            if pixel_idx == resized_transparency_idx:
                resized_transparent_pixels += 1
        
        # Allow some variation due to resampling, but there should be transparent pixels
        self.assertGreater(resized_transparent_pixels, 0,
                          "Resized GIF should have transparent pixels, not opaque background")
        
        # The number of transparent pixels should be roughly similar to the original
        # (within 25% tolerance due to resampling)
        pixel_count_original = original.size[0] * original.size[1]
        pixel_count_resized = resized.size[0] * resized.size[1]
        
        # Calculate the percentage of transparent pixels
        original_transparent_pct = 100.0 * original_transparent_pixels / pixel_count_original
        resized_transparent_pct = 100.0 * resized_transparent_pixels / pixel_count_resized
        
        # Allow 25% difference due to resampling artifacts
        self.assertAlmostEqual(original_transparent_pct, resized_transparent_pct, delta=25,
                              msg=f"Transparent pixel percentage should be preserved: original {original_transparent_pct:.1f}%, resized {resized_transparent_pct:.1f}%")
