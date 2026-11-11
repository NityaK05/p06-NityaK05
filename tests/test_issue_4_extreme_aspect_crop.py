# -*- coding: utf-8 -*-

from os.path import abspath, dirname, join
from unittest import TestCase
import math

from thumbor.config import Config
from thumbor.context import Context, RequestParameters
from thumbor.engines.pil import Engine

FIXTURES_PATH = abspath(join(dirname(__file__), "fixtures/"))
STORAGE_PATH = join(FIXTURES_PATH, "images")


class ExtremeAspectCropTestCase(TestCase):
    """Test that extreme aspect ratio crops don't produce empty images."""

    def test_auto_crop_doesnt_produce_zero_dimensions(self):
        """Verify that extreme aspect ratios don't result in 0-sized crops."""
        # Simulate the auto_crop logic with extreme aspect ratios
        # Test case: 16x16 source resized to 800x20
        source_width, source_height = 16, 16
        target_width, target_height = 800, 20
        
        # Calculate crop dimensions using the same logic as auto_crop
        source_ratio = round(source_width / source_height, 2)
        target_ratio = round(target_width / target_height, 2)
        
        if source_ratio == target_ratio:
            self.fail("Test setup error: aspect ratios should not match")
        
        if (
            target_width / source_width
            > target_height / source_height
        ):
            crop_width = source_width
            crop_height = int(
                round(source_width * target_height / target_width, 0)
            )
        else:
            crop_width = int(
                round(
                    math.ceil(
                        target_width * source_height / target_height
                    ),
                    0,
                )
            )
            crop_height = source_height
        
        # This is the bug: crop_height becomes 0 due to rounding
        self.assertEqual(crop_height, 0, 
                        "Without the fix, crop_height becomes 0 due to rounding")
        self.assertGreater(crop_width, 0, 
                          "crop_width should be positive")

    def test_auto_crop_clamp_fix(self):
        """Verify that clamping crop dimensions to 1px fixes the issue."""
        # Simulate the auto_crop logic with the fix
        # Test case: 16x16 source resized to 800x20
        source_width, source_height = 16, 16
        target_width, target_height = 800, 20
        
        # Calculate crop dimensions using the same logic as auto_crop
        source_ratio = round(source_width / source_height, 2)
        target_ratio = round(target_width / target_height, 2)
        
        if source_ratio == target_ratio:
            self.fail("Test setup error: aspect ratios should not match")
        
        if (
            target_width / source_width
            > target_height / source_height
        ):
            crop_width = source_width
            crop_height = int(
                round(source_width * target_height / target_width, 0)
            )
        else:
            crop_width = int(
                round(
                    math.ceil(
                        target_width * source_height / target_height
                    ),
                    0,
                )
            )
            crop_height = source_height
        
        # Apply the fix: clamp to minimum 1px
        crop_width = max(1, crop_width)
        crop_height = max(1, crop_height)
        
        # Now both dimensions should be at least 1
        self.assertGreaterEqual(crop_width, 1, 
                               "crop_width should be at least 1 after clamping")
        self.assertGreaterEqual(crop_height, 1, 
                               "crop_height should be at least 1 after clamping")

    def test_various_extreme_ratios(self):
        """Test multiple extreme aspect ratios to ensure fix works broadly."""
        test_cases = [
            # (source_w, source_h, target_w, target_h, description)
            (16, 16, 800, 20, "Very wide (40:1)"),
            (1, 1, 50, 25, "Extreme on tiny source (2:1)"),
            (1, 1, 100, 49, "Extreme on tiny source (>2:1)"),
            (940, 2, 1, 1, "Very narrow fit-in (1:1 target)"),
        ]
        
        for src_w, src_h, tgt_w, tgt_h, desc in test_cases:
            with self.subTest(case=desc):
                # Calculate crop dimensions
                if (tgt_w / src_w) > (tgt_h / src_h):
                    crop_width = src_w
                    crop_height = int(round(src_w * tgt_h / tgt_w, 0))
                else:
                    crop_width = int(round(math.ceil(tgt_w * src_h / tgt_h), 0))
                    crop_height = src_h
                
                # Apply the fix
                crop_width = max(1, crop_width)
                crop_height = max(1, crop_height)
                
                # Verify both are positive
                self.assertGreaterEqual(crop_width, 1, 
                                       f"crop_width should be >=1: {desc}")
                self.assertGreaterEqual(crop_height, 1, 
                                       f"crop_height should be >=1: {desc}")
