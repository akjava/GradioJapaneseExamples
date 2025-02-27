import numpy as np

from PIL import Image,ImageDraw,ImageOps


def create_color_image(width, height, color=(255,255,255)):
    img = Image.new('RGB', (width, height), color)
    return img

def create_compare_image(base_image,paste_image,mask):
    normal_image=base_image.copy()
    normal_image.paste(paste_image,(0,0),mask)

    invert_image=base_image.copy()
    invert_image.paste(paste_image,(0,0),ImageOps.invert(mask))
    return normal_image,invert_image

def mirror(image):
    return ImageOps.mirror(image)

def create_left_half_mask(image):
    
    left_mask = create_color_image(image.width,image.height)
    draw = ImageDraw.Draw(left_mask)
    draw.rectangle((0, 0, int(image.width/2), int(image.height)), fill=(0, 0, 0),outline=None)
    return left_mask.convert("L")

def create_top_half_mask(image):
    
    left_mask = create_color_image(image.width,image.height)
    draw = ImageDraw.Draw(left_mask)
    draw.rectangle((0, 0, int(image.width), int(image.height/2)), fill=(0, 0, 0),outline=None)

    return left_mask.convert("L")

def curve_midtones(x,option=0.7):
    return 255 * (x / 255) ** option

def apply_tone_curve(image, curve_function,option=1.0):
    # LUTを作成
    lut = np.array([curve_function(i,option) for i in range(256)], dtype=np.uint8)
    
    # 画像をNumPy配列に変換
    img_array = np.array(image)
    
    # LUTを適用
    adjusted_array = lut[img_array]
    
    # 調整後の配列を画像に戻す
    return Image.fromarray(adjusted_array)

def simple_white_balance(image, p=10, output_min=0, output_max=255):
    """
    PIL simple white balance without numpy

    Args:
      image: PIL Image 
      p: ignore pixel percent (50 convert to 51)
      output_min: min bright
      output_max: max bright

    Returns:
      PIL Image
    """
    if p == 50:
        p = 51# even make zero-error

    # convert to rgb
    image = image.convert("RGB")

    # get histgram
    histograms = image.histogram()

    # make lut
    luts = []
    for i in range(3):
        hist = histograms[i * 256:(i + 1) * 256]
        total = sum(hist)

        # min
        sum_low = 0
        low_value = 0
        for j, count in enumerate(hist):
            sum_low += count
            if sum_low > total * p / 100:
                low_value = j
                break

        # max
        sum_high = 0
        high_value = 255
        for j, count in enumerate(reversed(hist)):
            sum_high += count
            if sum_high > total * p / 100:
                high_value = 255 - j
                break

        # LUT 
        lut = [0] * 256  # initialize 0
        for j in range(256):
            if j < low_value:
                lut[j] = output_min
            elif j > high_value:
                lut[j] = output_max
            else:
                v = (j - low_value) / (high_value - low_value)
                lut[j] = int(round(output_min + (output_max - output_min) * v))

        luts.extend(lut)

    # apply LUT 
    return image.point(luts)