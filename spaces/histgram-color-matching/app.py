import spaces
import gradio as gr
import subprocess
from PIL import Image,ImageEnhance,ImageFilter,ImageDraw
import json
import numpy as np
from skimage.exposure  import match_histograms
from gradio_utils import save_image 
from color_utils import simple_white_balance,apply_tone_curve,curve_midtones,create_left_half_mask,create_top_half_mask,create_compare_image ,mirror

def color_match(base_image,cropped_image,color_match_format="RGB"):
    reference = np.array(base_image.convert(color_match_format))
    target =np.array(cropped_image.convert(color_match_format))
    matched = match_histograms(target, reference,channel_axis=-1)

    return Image.fromarray(matched,mode=color_match_format)



def apply_layer(image_dict):
    base_rgba = image_dict["background"].convert("RGBA")
    if len(image_dict['layers']) > 0:
         layer = image_dict['layers'][0]
         mask = layer.convert("L")                     # グレイスケールに変換
         mask=mask.point(lambda x: 255 if x > 0 else x)
         

         layer_rgba = layer.convert("RGBA")
         base_rgba.paste(layer_rgba, (0, 0),mask)
    return base_rgba
         

def create_enhanced_image(reference_image,brightness=1.0,color=1.0,contrast=1.0,use_whitebalance=False,top_whitebalance=1):

    if use_whitebalance:
        reference_image = simple_white_balance(reference_image,top_whitebalance)

    if brightness!=1.0:
        brightness_enhancer = ImageEnhance.Brightness(reference_image)
        reference_image = brightness_enhancer.enhance(brightness)
    
    if color!=1.0:
        color_enhancer = ImageEnhance.Color(reference_image)
        reference_image = color_enhancer.enhance(color)
    
    if contrast!=1.0:
        contrast_enhancer = ImageEnhance.Contrast(reference_image)
        reference_image = contrast_enhancer.enhance(contrast)

    return reference_image
    



def process_images(reference_image_dict,target_image_dict,mirror_target=False,middle_tone_value=0.75,color_match_format="RGB",progress=gr.Progress(track_tqdm=True)):
    progress(0, desc="Start color matching")
    if reference_image_dict == None:
        raise gr.Error("Need reference_image")

    if target_image_dict == None:
        raise gr.Error("Need target_image")
    
    if not isinstance(reference_image_dict, dict):
        raise gr.Error("Need DictData reference_image_dict")
    
    if not isinstance(target_image_dict, dict):
        raise gr.Error("Need DictData target_image_dict")

    reference_image = apply_layer(reference_image_dict)
    target_image = apply_layer(target_image_dict)
    if mirror_target:
        target_image = mirror(target_image)


    images = []

    left_mask = create_left_half_mask(reference_image)
    top_mask = create_top_half_mask(reference_image)

    color_matched = color_match(reference_image,target_image,color_match_format)
    color_matched_resized = color_matched.resize(reference_image.size)
    matched_path = save_image(color_matched.convert("RGB"))
    images.append((matched_path,"color matched"))
    progress(0.2)

    reference_mix_left,reference_mix_right = create_compare_image(reference_image,color_matched_resized,left_mask)
    images.append((save_image(reference_mix_left.convert("RGB"),extension="webp"),"mixed_left"))
    images.append((save_image(reference_mix_right.convert("RGB"),extension="webp"),"mixed_right"))
    progress(0.4)

    reference_mix_top,reference_mix_bottom = create_compare_image(reference_image,color_matched_resized,top_mask)
    images.append((save_image(reference_mix_top.convert("RGB"),extension="webp"),"mixed_top"))
    images.append((save_image(reference_mix_bottom.convert("RGB"),extension="webp"),"mixed_bottom"))
    progress(0.6)

    color_matched_tone = apply_tone_curve(color_matched.convert("RGB"),curve_midtones,middle_tone_value)
    color_matched_tone_resized = color_matched_tone.resize(reference_image.size)

    images.append((save_image(color_matched_tone.convert("RGB")),"tone-curved"))
    reference_mix_left,reference_mix_right = create_compare_image(reference_image,color_matched_tone_resized,left_mask)
    images.append((save_image(reference_mix_left.convert("RGB"),extension="webp"),"mixed_left"))
    images.append((save_image(reference_mix_right.convert("RGB"),extension="webp"),"mixed_right"))
    progress(0.8)
    
    reference_mix_top,reference_mix_bottom = create_compare_image(reference_image,color_matched_tone_resized,top_mask)
    images.append((save_image(reference_mix_top.convert("RGB"),extension="webp"),"mixed_top"))
    images.append((save_image(reference_mix_bottom.convert("RGB"),extension="webp"),"mixed_bottom"))
    progress(1.0)

    return images



def read_file(file_path: str) -> str:
    """read the text of target file
    """
    with open(file_path, 'r', encoding='utf-8') as f:
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

def color_changed(color):
    #mode must be RGBA
    editor = gr.ImageEditor(brush=gr.Brush(colors=[color],color_mode="fixed"))
    return editor,editor  

#css=css,
def update_button_label(image):
    if image == None:
        print("none replace")
        return  gr.Button(visible=True),gr.Button(visible=False),gr.Row(visible=True),gr.Row(visible=True)
    else:
        return  gr.Button(visible=False),gr.Button(visible=True),gr.Row(visible=False),gr.Row(visible=False)
    
def update_visible(fill_color_mode,image):
     if image != None:
          return  gr.Row(visible=False),gr.Row(visible=False)
     
     if fill_color_mode:
        return  gr.Row(visible=False),gr.Row(visible=True)
     else:
        return  gr.Row(visible=True),gr.Row(visible=False)
     
with gr.Blocks(css=css, elem_id="demo-container") as demo:
    with gr.Column():
        gr.HTML(read_file("demo_header.html"))
        gr.HTML(read_file("demo_tools.html"))
    with gr.Row():
                with gr.Column():
                    reference_image = gr.ImageEditor(height=1050,sources=['upload','clipboard'],layers = False,transforms=[],image_mode='RGBA',elem_id="image_upload", type="pil", label="Reference Image",brush=gr.Brush(colors=["#001"], color_mode="fixed"))
                    with gr.Row(elem_id="prompt-container",  equal_height=False):
                        btn1 = gr.Button("Color Match", elem_id="run_button",variant="primary")
                        mirror_target = gr.Checkbox(label="Mirror target",value=False)
                        pick=gr.ColorPicker(label="color",value="#001",info="ImageEditor color is broken,pick color from here.reselect paint-tool and draw.but not so effective")
                        
                    target_image = gr.ImageEditor(height=1050,sources=['upload','clipboard'],layers = False,transforms=[],image_mode='RGBA',elem_id="image_upload", type="pil", label="Target Image",brush=gr.Brush(colors=["#001"], color_mode="fixed"))
                    pick.change(fn=color_changed,inputs=[pick],outputs=[reference_image,target_image])
                    
                            
                    
                    with gr.Accordion(label="Advanced Settings", open=False):
                        gr.HTML("<h4>Post-Process Target Image</h4>")
                        with gr.Row(equal_height=True):
                            middle_tone_value = gr.Slider(
                            label="middle tone",
                            minimum=0,
                            maximum=2.0,
                            step=0.01,
                            value=0.75)
                            color_match_format = gr.Dropdown(label="Format",choices=["RGB","CMYK","YCbCr","HSV","LAB"],value="RGB",info="RGB and CMYK seems same,others are broken")
                        
                with gr.Column():
                    image_out = gr.Gallery(height=800,label="Output", elem_id="output-img",format="webp", preview=True)
                    
                    
                    
            

    
    gr.on(
        [btn1.click],
        fn=process_images, inputs=[reference_image,target_image,mirror_target,middle_tone_value,color_match_format], outputs =[image_out], api_name='infer'
    )
    gr.Examples(
                examples =[
                        ["examples/face01.webp","examples/face02.webp"],
                        ["examples/face01.webp","examples/face03.webp"],
                        ["examples/face01.webp","examples/face04.webp"],
                        ["examples/face02.webp","examples/face03.webp"],
                        ["examples/face02.webp","examples/face04.webp"],
                        ["examples/face03.webp","examples/face04.webp"],
                           ],
                inputs=[reference_image,target_image]
    )
    gr.HTML(read_file("demo_footer.html"))

    if __name__ == "__main__":
        demo.launch()
