import spaces
import gradio as gr
import re
from PIL import Image,ImageFilter

import os
import numpy as np




def process_images(fg_image, bg_image,fg_image_mask=None,dilate=0,blur=0):
    # I'm not sure when this happen maybe api calling
    
    #Basically ImageEditor's value are dictionary,If not convert value to dict
    if not isinstance(fg_image, dict):
        if fg_image_mask == None:
             print("empty mask")
             return image,None
        else:
            image = dict({'background': image, 'layers': [fg_image_mask]}) #no need?

    if fg_image_mask!=None:
         mask = fg_image_mask
    else:
         if len(fg_image['layers']) == 0:
              print("empty mask")
              return image,None
         #print("use layer")
         mask = fg_image['layers'][0]

    mask = mask.convert("L")

    if dilate>0:
        if dilate%2 ==0:
             dilate -= 1
        mask = mask.filter(ImageFilter.MaxFilter(dilate))


    if blur>0:
        mask = mask.filter(ImageFilter.GaussianBlur(radius=blur))


    image2 = fg_image["background"].convert("RGBA")
    
    if bg_image == None:
         image2_masked = Image.composite(image2, Image.new("RGBA", image2.size, (0, 0, 0, 0)), mask)
         return image2_masked,mask
    

    bg_image = bg_image.convert("RGBA")
    bg_image.paste(image2, (0, 0), mask)

    return [bg_image,mask]
    

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
                    image = gr.ImageEditor(height=800,sources=['upload','clipboard'],transforms=[],image_mode='RGB', layers=False,  elem_id="Foreground", type="pil", label="Foreground",brush=gr.Brush(colors=["#fff"], color_mode="fixed"))
                    #image.height=1000
                    
                    btn = gr.Button("Paste to BG", elem_id="run_button",variant="primary")
                    
                    bg_image = gr.Image(sources=['upload','clipboard'],  elem_id="bg_image", type="pil", label="Background Image",height=400, value=None)
                    image_mask = gr.Image(sources=['upload','clipboard'],  elem_id="mask_upload", type="pil", label="Mask Uploaded",height=400, value=None)
                    with gr.Accordion(label="Advanced Settings", open=False):
                        with gr.Row( equal_height=True):
                            blur = gr.Slider(
                            label="blur",
                            minimum=0,
                            maximum=100,
                            step=1,
                            value=5)

                            dilate = gr.Slider(
                            label="dilate",
                            minimum=0,
                            maximum=100,
                            step=1,
                            value=0)
                        id_input=gr.Text(label="Name", visible=False)
                            
                with gr.Column():
                    image_out = gr.Image(height=800,sources=[],label="Output", elem_id="output-img",format="webp")
                    mask_out = gr.Image(height=800,sources=[],label="Mask", elem_id="mask-img",format="jpeg")

                    
            

    btn.click(fn=process_images, inputs=[image, bg_image,image_mask,dilate,blur], outputs =[image_out,mask_out], api_name='infer')
    gr.Examples(
               examples=[
                   ["examples/00533245_00004200_eyes.jpg","examples/00533245_00003200_mouth.jpg","examples/00533245_99_mask.jpg",5,18,"examples/00533245_mixed.jpg"],
                   ["examples/00346245_00006200.jpg", "examples/00346245_00003200.jpg","examples/00346245_mask.jpg",10,0,"examples/00346245_mixed.jpg"]
                  
                         ]
                         ,
                inputs=[image,bg_image,image_mask,blur,dilate,image_out]
    )
    gr.HTML(read_file("demo_footer.html"))

    if __name__ == "__main__":
        demo.launch()
