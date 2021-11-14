#!/usr/bin/env python3

import functools
from PIL import Image
import os

class WmCfg(object):
    def __init__(watermark_path, input_dir, output_dir, quality=97, alpha=150, landscape_fraction=0.1, portrait_fraction=0.025):
        self.watermark_path = watermark_path
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.quality = quality
        self.alpha = alpha
        self.landscape_fraction = landscape_fraction
        self.portrait_fraction = portrait_fraction

class ThumbCfg(object):
    def __init__(watermark_path, input_dir, output_dir, quality=97, clamp_width=250, clamp_height=None):
        self.watermark_path = watermark_path
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.quality = quality
        self.clamp_width = clamp_width
        self.clamp_height = clamp_height

def image_transpose_exif(im):
    """
    Apply Image.transpose to ensure 0th row of pixels is at the visual
    top of the image, and 0th column is the visual left-hand side.
    Return the original image if unable to determine the orientation.

    As per CIPA DC-008-2012, the orientation field contains an integer,
    1 through 8. Other values are reserved.

    Parameters
    ----------
    im: PIL.Image
       The image to be rotated.
    """

    exif_orientation_tag = 0x0112
    exif_transpose_sequences = [                   # Val  0th row  0th col
        [],                                        #  0    (reserved)
        [],                                        #  1   top      left
        [Image.FLIP_LEFT_RIGHT],                   #  2   top      right
        [Image.ROTATE_180],                        #  3   bottom   right
        [Image.FLIP_TOP_BOTTOM],                   #  4   bottom   left
        [Image.FLIP_LEFT_RIGHT, Image.ROTATE_90],  #  5   left     top
        [Image.ROTATE_270],                        #  6   right    top
        [Image.FLIP_TOP_BOTTOM, Image.ROTATE_90],  #  7   right    bottom
        [Image.ROTATE_90],                         #  8   left     bottom
    ]

    try:
        seq = exif_transpose_sequences[im._getexif()[exif_orientation_tag]]
    except Exception:
        return im
    else:
        return functools.reduce(type(im).transpose, seq, im)


def watermark_and_thumbnail(watermark_path, input_image_path, watermarked_output_path, thumbnail_output_path, alpha=150, width_fraction=0.2, clamp_width=250, clamp_height=None, quality=97):
    im = Image.open(input_image_path)
    im = image_transpose_exif(im)
    wm = Image.open(watermark_path)

    
    print("wm/th args: alpha:{}, width_frac: {}, clamp_width:{}, clamp_height:{} quality:{}".format(alpha, width_fraction, clamp_width, clamp_height, quality))
    if clamp_width == None and clamp_height == None:
        raise ValueError("Must have either clamp width or clamp height to thumbnail.")
    elif clamp_width == None:
        clamp_width = int((clamp_height / im.height) * im.width)
    elif clamp_height == None:
        clamp_height = int((clamp_width / im.width) * im.height)
    print("Thumb: resizing {} to {},{}".format(thumbnail_output_path, clamp_width, clamp_height))
    thumb = im.resize((clamp_width, clamp_height))
    thumb.save(thumbnail_output_path, quality=quality)

    for x in range(wm.width):
        for y in range(wm.height):
            (r, g, b, a) = wm.getpixel((x, y))
            if a > 0:
                a = alpha
                wm.putpixel((x, y), (r, g, b, a))


    desired_width = int(im.width * width_fraction)
    desired_height = int((float(desired_width) / wm.width) * wm.height)
    wm = wm.resize((desired_width, desired_height))

    border = 20
    x_pos = im.width - desired_width - border
    y_pos = im.height - desired_height - border

    im.paste(wm, (x_pos, y_pos), wm)
    im.save(watermarked_output_path, quality=quality)

def main():
    alpha = 180
    width_frac = 0.4
    thumb_width = 300
    quality = 97

    input_dir = os.path.expanduser("~/portfolio_website/raw_images")
    watermarked_output_dir = os.path.expanduser("~/portfolio_website/images")
    thumbnail_output_dir = os.path.expanduser("~/portfolio_website/thumbs")
    watermark_path = os.path.expanduser("~/watermark/emmaduffy_watermark.png")

    for f in os.listdir(input_dir):
        input_path = os.path.join(input_dir, f)
        watermarked_output_path = os.path.join(watermarked_output_dir, f)
        thumbnail_output_path = os.path.join(thumbnail_output_dir, f)

        if not f.lower().endswith(".jpg"):
            print("{} doesn't seem to be a JPEG, not watermarking".format(f))
            continue

        print("Watermarking {}, will be put in {}".format(f, watermarked_output_dir))
        print("Thumbnailing {}, will be put in {}".format(f, thumbnail_output_dir))
        watermark_and_thumbnail(watermark_path, input_path, watermarked_output_path, thumbnail_output_path, alpha=alpha, width_fraction=width_frac, quality=quality, clamp_width=thumb_width)


if __name__ == "__main__": main()
