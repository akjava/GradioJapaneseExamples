import spaces
import gradio as gr
import re
from PIL import Image,ImageEnhance

import os

import numpy as np
import hashlib
import io
import cv2
import time

def clear_old_files(dir,passed_time):
    try:
        files = os.listdir(dir)
        current_time = time.time()
        for file in files:
            file_path = os.path.join(dir,file)
            
            ctime = os.stat(file_path).st_ctime
            diff = current_time - ctime
            #print(f"ctime={ctime},current_time={current_time},passed_time={passed_time},diff={diff}")
            if diff > passed_time:
                os.remove(file_path)
    except:
            print("maybe still gallery using error")



              #print(f"file removed {file_path}")

def simple_white_balance(image, p=10, output_min=0, output_max=255):
    """
    PIL simple white balance without numpy

    Args:
      image: PIL Image 
      p: ignore pixel percent
      output_min: min bright
      output_max: max bright

    Returns:
      PIL Image
    """

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

def pil_to_cv2(pil_image):
    numpy_array = np.array(pil_image)
    bgr_image = cv2.cvtColor(numpy_array, cv2.COLOR_RGB2BGR)
    return bgr_image
def cv2_to_pil(cv2_image):
     rgb_image = cv2.cvtColor(cv2_image, cv2.COLOR_BGR2RGB)
     pil_image = Image.fromarray(rgb_image)
     return pil_image



def get_image_id(image):
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    hash_object = hashlib.sha256(buffer.getvalue())
    hex_dig = hash_object.hexdigest()
    unique_id = hex_dig[:32]
    return unique_id

dir_name ="images"
passed_time = 60*5
def cv2_to_result(cv2_image,label,origin_rgba=None,mask=None):
    pil_image=cv2_to_pil(cv2_image)

    if mask is not None:
        pil_image =  apply_mask(pil_image,origin_rgba,mask)

    id = get_image_id(pil_image)
    path = os.path.join(dir_name,f"{id}.jpg")
    pil_image.save(path)
    return (path,label)


def apply_mask(image_rgb,origin_rgba=None,mask=None):
    image_rgba = image_rgb.convert("RGBA")
    origin_rgba.paste(image_rgba, (0, 0), mask)
    return origin_rgba.convert("RGB")

def enhance_image(enhancer,value,origin_rgba=None,mask=None):
    enhanced = enhancer.enhance(value)
    if mask is None:
        return enhanced
    else:
        return apply_mask(enhanced,origin_rgba,mask)
        

    
def process_images(fg_image,top_value=2,mask_image=None):
    if fg_image == None:
         raise gr.Error("need image")
    fg_rgba = None
    if mask_image!=None:
        mask_image = mask_image.convert("L")
        fg_rgba = fg_image.convert("RGBA")
    
    if not os.path.exists(dir_name):
        os.mkdir(dir_name)

    clear_old_files(dir_name,passed_time)

    images =[]
    cv2_image = pil_to_cv2(fg_image)
    wb = cv2.xphoto.createSimpleWB()
    simple_result=cv2_to_result(wb.balanceWhite(cv2_image),"cv2-simple",fg_rgba,mask_image)
    images.append(simple_result)
    simple_wb_image=Image.open(simple_result[0])

    enchance_values = [1.1]
    enhancer = ImageEnhance.Brightness(fg_image)
    for value in enchance_values:
        color_balanced = enhance_image(enhancer,value,fg_rgba,mask_image)
        id = get_image_id(color_balanced)
        label=f"pil-br:{value}"
        path = os.path.join(dir_name,f"{id}.jpg")
        color_balanced.save(path)
        images.append((path,label))
    
    enchance_values = [1.1,1.25,1.5]
    enhancer = ImageEnhance.Color(fg_image)
    for value in enchance_values:
        color_balanced = enhance_image(enhancer,value,fg_rgba,mask_image)
        id = get_image_id(color_balanced)
        label=f"pil-co:{value}"
        path = os.path.join(dir_name,f"{id}.jpg")
        color_balanced.save(path)
        images.append((path,label))

        blended_image = Image.blend(simple_wb_image, color_balanced, 0.5)
        if mask_image is not None:
            blended_image = apply_mask(blended_image,fg_rgba,mask_image)
        label=f"pil-co:{value}+swb"
        id = get_image_id(blended_image)
        path = os.path.join(dir_name,f"{id}.jpg")
        blended_image.save(path)
        images.append((path,label))
    
    
    
    

    wb = cv2.xphoto.createGrayworldWB()
    gray_wordls = cv2_to_result(wb.balanceWhite(cv2_image),"cv2-grayworld",fg_rgba,mask_image)
    images.append(gray_wordls)
    enhancer = ImageEnhance.Brightness(Image.open(gray_wordls[0]))
    enhancer2 = ImageEnhance.Brightness(fg_image)

    enchance_values = [1.25,1.5]#0.75 darker no need
    for value in enchance_values:
        bright_image = enhance_image(enhancer,value,fg_rgba,mask_image)
        id = get_image_id(bright_image)
        label=f"gwb_pil-br:{value}"
        path = os.path.join(dir_name,f"{id}.jpg")
        bright_image.save(path)
        images.append((path,label))

        bright_origin_image = enhancer2.enhance(value)
        bright_origin_image_cv2=pil_to_cv2(bright_origin_image)
        gray_wordls = cv2_to_result(wb.balanceWhite(bright_origin_image_cv2),f"pil-br{value}_gwb",fg_rgba,mask_image)
        images.append(gray_wordls)


    wb = cv2.xphoto.createLearningBasedWB()
    images.append(cv2_to_result(wb.balanceWhite(cv2_image),"cv2-learning",fg_rgba,mask_image))

    pil_simple = simple_white_balance(fg_image,top_value)
    if mask_image is not None:
        pil_simple = apply_mask(pil_simple,fg_rgba,mask_image)

    id = get_image_id(pil_simple)
    label=f"custom-simple"
    path = os.path.join(dir_name,f"{id}.jpg")
    pil_simple.save(path)
    images.append((path,label))


    images2 = []
    enchance_values = [0.75,0.8,0.85,0.9,0.95]
    enchance_values2 = [0.9,0.95, 1]
    enhancer = ImageEnhance.Color(fg_image)
    for value in enchance_values:
        color_balanced = enhance_image(enhancer,value,None,None)
        enhancer2 = ImageEnhance.Brightness(color_balanced)
        for value2 in enchance_values2:
            br_balanced = enhance_image(enhancer2,value2,fg_rgba,mask_image)
            id = get_image_id(br_balanced)
            label=f"pil-br{value2}_co{value}"
            path = os.path.join(dir_name,f"{id}.jpg")
            br_balanced.save(path)
            images2.append((path,label))

    return images,images2
    

def read_file(path: str) -> str:
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    return content

css="""
#col-left {
    margin: 0 auto;
    max-width: 640px;
}
#col-right {
    margin: 0 auto;
    max-width: 640px;
}
.grid-container {
  display: flex;
  align-items: center;
  justify-content: center;
  gap:10px
}

.image {
  width: 128px; 
  height: 128px; 
  object-fit: cover; 
}

.text {
  font-size: 16px;
}

"""

with gr.Blocks(css=css, elem_id="demo-container") as demo:
    with gr.Column():
        gr.HTML(read_file("demo_header.html"))
        gr.HTML(read_file("demo_tools.html"))
    with gr.Row():
                with gr.Column():
                    image = gr.Image(sources=['upload','clipboard'],image_mode='RGB',  elem_id="Image", type="pil", label="Image")
                    
                            
                    btn = gr.Button("White balances", elem_id="run_button",variant="primary")
                    
                    with gr.Accordion(label="Advanced Settings", open=False):
                        with gr.Row( equal_height=True):
                            id_input=gr.Text(label="Name", visible=False)
                            top_value = gr.Slider(
                            label="Cutom-Ignore Percent",info ="last one's simple-wb option",
                            minimum=0,
                            maximum=99,
                            step=1,
                            value=1,
                )
                        image_mask = gr.Image(sources=['upload','clipboard'],  elem_id="mask_upload", type="pil", label="Mask Uploaded",height=400, value=None)
                    
                            
                with gr.Column():
                    image_out = gr.Gallery(height=800,label="Output", elem_id="image_out",format="webp", preview=True)
                    image_out2 = gr.Gallery(height=800,label="Output", elem_id="image_out",format="webp", preview=True)

                    
            

    btn.click(fn=process_images, inputs=[image,top_value,image_mask], outputs =[image_out,image_out2], api_name='infer')
    gr.Examples(
               examples=[
                  ["examples/wink.jpg"]
                         ]
                         ,
                inputs=[image]
    )
    gr.HTML(
         gr.HTML(read_file("demo_footer.html"))
    )
    if __name__ == "__main__":
        demo.launch()
