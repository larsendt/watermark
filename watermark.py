#!/usr/bin/env python3

import functools
import os

from PIL import Image


class WmCfg(object):
    def __init__(
        self,
        watermark_path,
        input_image_path,
        output_image_path,
        quality=97,
        alpha=150,
        landscape_fraction=0.1,
        portrait_fraction=0.025,
        border=0.005,
    ):
        self.watermark_path = watermark_path
        self.input_image_path = input_image_path
        self.output_image_path = output_image_path
        self.quality = quality
        self.alpha = alpha
        self.landscape_fraction = landscape_fraction
        self.portrait_fraction = portrait_fraction
        self.border = border


class ThumbCfg(object):
    def __init__(
        self,
        input_image_path,
        output_image_path,
        quality=97,
        clamp_width=250,
        clamp_height=None,
    ):
        self.input_image_path = input_image_path
        self.output_image_path = output_image_path
        self.quality = quality
        self.clamp_width = clamp_width
        self.clamp_height = clamp_height

    def width_height(self, im):
        if self.clamp_width == None and self.clamp_height == None:
            raise ValueError(
                "Must have either clamp width or clamp height to thumbnail."
            )
        elif self.clamp_width == None:
            self.clamp_width = int((self.clamp_height / im.height) * im.width)
        elif self.clamp_height == None:
            self.clamp_height = int((self.clamp_width / im.width) * im.height)
        else:
            raise ValueError(
                "Setting both clamp_width and clamp_height would change the aspect ratio of the thumbnail."
            )

        return (self.clamp_width, self.clamp_height)


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
    exif_transpose_sequences = [  # Val  0th row  0th col
        [],  #  0    (reserved)
        [],  #  1   top      left
        [Image.FLIP_LEFT_RIGHT],  #  2   top      right
        [Image.ROTATE_180],  #  3   bottom   right
        [Image.FLIP_TOP_BOTTOM],  #  4   bottom   left
        [Image.FLIP_LEFT_RIGHT, Image.ROTATE_90],  #  5   left     top
        [Image.ROTATE_270],  #  6   right    top
        [Image.FLIP_TOP_BOTTOM, Image.ROTATE_90],  #  7   right    bottom
        [Image.ROTATE_90],  #  8   left     bottom
    ]

    try:
        seq = exif_transpose_sequences[im._getexif()[exif_orientation_tag]]
    except Exception:
        return im
    else:
        return functools.reduce(type(im).transpose, seq, im)


def thumbnail(thumb_cfg: ThumbCfg):
    im = Image.open(thumb_cfg.input_image_path)
    im = image_transpose_exif(im)
    thumb = im.resize(thumb_cfg.width_height(im))
    thumb.save(
        thumb_cfg.output_image_path, quality=thumb_cfg.quality, exif=im.info["exif"]
    )


def watermark(wm_cfg: WmCfg):
    im = Image.open(wm_cfg.input_image_path)
    im = image_transpose_exif(im)
    wm = Image.open(wm_cfg.watermark_path)

    if im.width > im.height:
        desired_width = int(im.width * wm_cfg.landscape_fraction)
        desired_height = int((float(wm.width) / im.width) * wm.height)
        border = int(im.width * wm_cfg.border)
    else:
        desired_width = int(im.height * wm_cfg.portrait_fraction)
        desired_height = int((float(wm.height) / im.height) * wm.width)
        border = int(im.height * wm_cfg.border)
    wm = wm.resize((desired_width, desired_height))

    x_pos = im.width - desired_width - border
    y_pos = im.height - desired_height - border

    im.paste(wm, (x_pos, y_pos), wm)
    im.save(wm_cfg.output_image_path, quality=wm_cfg.quality, exif=im.info["exif"])


def main():
    input_dir = os.path.expanduser("~/dev/misc/watermark/input_images")
    watermarked_output_dir = os.path.expanduser("~/dev/misc/watermark/output_images")
    thumbnail_output_dir = os.path.expanduser("~/dev/misc/watermark/thumbs")
    watermark_path = os.path.expanduser("~/dev/misc/watermark/emmaduffy_watermark.png")

    for f in os.listdir(input_dir):
        input_path = os.path.join(input_dir, f)
        watermarked_output_path = os.path.join(watermarked_output_dir, f)
        thumbnail_output_path = os.path.join(thumbnail_output_dir, f)

        if not f.lower().endswith(".jpg") and not f.lower().endswith(".jpeg"):
            print("{} doesn't seem to be a JPEG, not watermarking".format(f))
            continue

        wm_cfg = WmCfg(
            watermark_path,
            input_path,
            watermarked_output_path,
            alpha=120,
            landscape_fraction=0.1,
            portrait_fraction=0.025,
        )
        print("Watermarking {}, will be put in {}".format(f, watermarked_output_dir))
        watermark(wm_cfg)

        thumb_cfg = ThumbCfg(
            input_image_path=input_path,
            output_image_path=thumbnail_output_path,
            clamp_width=300,
            clamp_height=None,
        )
        print("Thumbnailing {}, will be put in {}".format(f, thumbnail_output_dir))
        thumbnail(thumb_cfg)


if __name__ == "__main__":
    main()
