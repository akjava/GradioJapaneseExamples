import spaces
import gradio as gr
import subprocess
import re
from PIL import Image

import opencvinpaint

def sanitize_prompt(prompt):
  # Allow only alphanumeric characters, spaces, and basic punctuation
  allowed_chars = re.compile(r"[^a-zA-Z0-9\s.,!?-]")
  sanitized_prompt = allowed_chars.sub("", prompt)
  return sanitized_prompt

#@spaces.GPU(duration=120)
def process_images(image, image2=None,inpaint_radius=3,blur_radius=25,edge_expand=8,inpaint_mode="Telea",dilate=0,progress=gr.Progress(track_tqdm=True)):
    progress(0, desc="Start Inpainting")
    #print("process_images")
    # I'm not sure when this happen
    if not isinstance(image, dict):
        if image2 == None:
             print("empty mask")
             return image
        else:
            image = dict({'background': image, 'layers': [image2]})

    if image2!=None:
         mask = image2
    else:
         if len(image['layers']) == 0:
              print("empty mask")
              return image
         mask = image['layers'][0]

    img_width,img_height = image["background"].size
    mask_width, mask_height = mask.size
    if img_width!=mask_width or img_height!=mask_height:
         raise gr.Error(f"image size({img_width},{img_height}) must be same as mask size({mask_width},{mask_height})")
    else:
         pass
         #print("size ok")

    output,cvmask = opencvinpaint.process_cvinpaint(image["background"],mask,inpaint_radius,blur_radius,edge_expand,inpaint_mode,dilate)
        
    return output,cvmask
    

# code from https://huggingface.co/spaces/diffusers/stable-diffusion-xl-inpainting/blob/main/app.py
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

#css=css,

with gr.Blocks(css=css, elem_id="demo-container") as demo:
    with gr.Column():
        gr.HTML(read_file("demo_header.html"))
        gr.HTML(read_file("demo_tools.html"))
    with gr.Row():
                with gr.Column():
                    image = gr.ImageEditor(height=800,sources=['upload','clipboard'],transforms=[],image_mode='RGB', layers=False,  elem_id="image_upload", type="pil", label="Upload",brush=gr.Brush(colors=["#fff"], color_mode="fixed"))
                    with gr.Row(elem_id="prompt-container",  equal_height=False):
                        with gr.Row():
                            btn = gr.Button("Inpaint!", elem_id="run_button")
                    image_mask = gr.Image(sources=['upload','clipboard'],  elem_id="mask_upload", type="pil", label="Mask_Upload",height=400, value=None)
                    with gr.Accordion(label="Advanced Settings", open=False):
                        with gr.Row( equal_height=True):
                            inpaint_radius = gr.Slider(value=3, minimum=1.0, maximum=20.0, step=1, label="Inpaint Radius",info="increse become slow but smooth")
                            blur_radius = gr.Slider(value=25, minimum=0.0, maximum=50.0, step=1, label="Blur Radius",info="not bluar mask,inner blur")
                            edge_expand = gr.Slider(value=8, minimum=0.0, maximum=20.0, step=1, label="Edge Expand",info="not mask extend,for smooth mix")
                            dilate = gr.Slider(value=0, minimum=0.0, maximum=40.0, step=1, label="Dilate",info="extend mask,but make slow")
                    with gr.Row(equal_height=True):
                            modes = ["Telea", "Navier-Stokes"]
                            inpaint_mode = gr.Dropdown(label="modes", choices=modes, value="Telea") 
                with gr.Column():
                    image_out = gr.Image(sources=[],label="Output", elem_id="output-img")
                    mask_out = gr.Image(sources=[],label="Mask", elem_id="mask-img",format="jpeg")
                    
            

    btn.click(fn=process_images, inputs=[image, image_mask,inpaint_radius,blur_radius,edge_expand,inpaint_mode,dilate], outputs =[image_out,mask_out], api_name='infer')
    gr.Examples(
               examples=[["examples/00207245.jpg", "examples/00207245_mask.jpg","examples/00207245.webp"],
                         ["examples/00047689.jpg", "examples/00047689_mask.jpg","examples/00047689.webp"]]
,
                #fn=predict,
                inputs=[image,image_mask,image_out],
                cache_examples=False,
    )
    gr.HTML(read_file("demo_footer.html"))

    if __name__ == "__main__":
        demo.launch()
