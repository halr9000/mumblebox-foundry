"""Shared pixel-preservation rules for both image editors."""
import io
from PIL import Image, ImageChops, ImageFilter

def prepare_mask(size,mask_bytes,feather=0):
    if type(feather) is not int or not 0<=feather<=32:raise ValueError('Edge softness must be between 0 and 32 pixels.')
    if len(mask_bytes)>20*1024**2:raise ValueError('Selection images must be smaller than 20 MB.')
    with Image.open(io.BytesIO(mask_bytes)) as image:
        if image.size!=tuple(size) or image.width*image.height>40_000_000:
            raise ValueError('The selection must match the source image and be below 40 megapixels.')
        mask=image.convert('L')
    if not mask.getbbox():raise ValueError('Select an area to edit first.')
    if feather:mask=ImageChops.multiply(mask,mask.filter(ImageFilter.GaussianBlur(feather)))
    return mask

def composite_image(original,generated,mask):
    original=original.convert('RGBA')
    generated=generated.convert('RGBA').resize(original.size,Image.Resampling.LANCZOS)
    return Image.composite(generated,original,mask)
