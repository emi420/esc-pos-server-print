""" Image format handling class
This module contains the image format handler :py:class:`EscposImage`.
:author: `Michael Billington <michael.billington@gmail.com>`_
:organization: `python-escpos <https://github.com/python-escpos>`_
:copyright: Copyright (c) 2016 Michael Billington <michael.billington@gmail.com>
:license: GNU GPL v3
"""

from PIL import Image, ImageOps


class EscposImage(object):
    """
    Load images in, and output ESC/POS formats.
    The class is designed to efficiently delegate image processing to
    PIL, rather than spend CPU cycles looping over pixels.
    """

    def __init__(self, img_source):
        """
        Load in an image
        
        :param img_source: PIL.Image, or filename to load one from.
        """
        if isinstance(img_source, Image.Image):
            img_original = img_source
        else:
            img_original = Image.open(img_source)

        # Convert to white RGB background, paste over white background
        # to strip alpha.
        img_original = img_original.convert('RGBA')
        im = Image.new("RGB", img_original.size, (255, 255, 255))
        im.paste(img_original, mask=img_original.split()[3])
        # Convert down to greyscale
        im = im.convert("L") 
        # Invert: Only works on 'L' images
        im = ImageOps.invert(im)
        # Pure black and white
        self._im = im.convert("1")
    
    @property
    def width(self):
        """
        Width of image in pixels
        """
        width_pixels, _ = self._im.size
        return width_pixels

    @property
    def width_bytes(self):
        """
        Width of image if you use 8 pixels per byte and 0-pad at the end.
        """
        return (self.width + 7) >> 3

    @property
    def height(self):
        """
        Height of image in pixels
        """
        _, height_pixels = self._im.size
        return height_pixels

    def to_column_format(self, high_density_vertical=True):
        """
        Extract slices of an image as equal-sized blobs of column-format data.
        :param high_density_vertical: Printed line height in dots
        """
        im = self._im.transpose(Image.ROTATE_270).transpose(Image.FLIP_LEFT_RIGHT)
        line_height = 24 if high_density_vertical else 8
        width_pixels, height_pixels = im.size
        top = 0
        left = 0
        while left < width_pixels:
            box = (left, top, left + line_height, top + height_pixels)
            im_slice = im.transform((line_height, height_pixels), Image.EXTENT, box)
            im_bytes = im_slice.tobytes()
            yield(im_bytes)
            left += line_height

    def to_raster_format(self):
        """
        Convert image to raster-format binary
        """
        return self._im.tobytes()


