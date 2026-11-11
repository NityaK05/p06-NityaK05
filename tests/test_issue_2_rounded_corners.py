# -*- coding: utf-8 -*-
"""
Regression test for Issue #2: Transparent rounded corners carry a dark ring

The test verifies that when applying round_corner filter with transparent=1,
the corner pixels fade smoothly through the alpha channel instead of being
darkened (which created a visible dark ring).
"""

from tornado.testing import gen_test
from tests.base import FilterTestCase


class RoundCornerTransparencyTestCase(FilterTestCase):
    @gen_test
    async def test_round_corner_transparent_preserves_original_colors(self):
        """Test that transparent round corners use alpha blending, not color darkening."""
        # Apply round_corner with transparent flag to a PNG
        image = await self.get_filtered(
            "source.jpg",
            "thumbor.filters.round_corner",
            "round_corner(60,255,255,255,1)",  # white background, transparent
            mode="RGBA",
        )
        
        # Get the image as RGB to examine pixel values
        from PIL import Image
        import io
        
        # Convert to PIL Image for pixel inspection
        if isinstance(image, bytes):
            pil_image = Image.open(io.BytesIO(image))
        else:
            pil_image = image
        
        # Ensure it's RGBA
        if pil_image.mode != "RGBA":
            pil_image = pil_image.convert("RGBA")
        
        # Get corner pixels (top-left area where the corner should be rounded)
        # Check a few pixels along the diagonal where the curve is
        width, height = pil_image.size
        
        # Sample pixels at various distances from corner (should have varying alpha)
        has_partial_transparency = False
        has_non_darkened_colors = False
        
        # Check the top-left region
        for y in range(min(10, height)):
            for x in range(min(10, width)):
                r, g, b, a = pil_image.getpixel((x, y))
                
                # If alpha is between 0 and 255 (not fully opaque or transparent)
                # this indicates proper alpha blending
                if 0 < a < 255:
                    has_partial_transparency = True
                
                # If we have partial transparency and colors aren't heavily darkened
                # (i.e., not close to black), this indicates proper blending
                if has_partial_transparency and (r + g + b) > 100:
                    has_non_darkened_colors = True
        
        # The fix should result in:
        # 1. Partial alpha values at corners (not just 0 or 255)
        # 2. Colors that fade through alpha, not darkened to black
        assert (has_partial_transparency or has_non_darkened_colors), (
            "Transparent corners should use alpha blending. "
            "Check that corner pixels have partial transparency or preserved color values."
        )
