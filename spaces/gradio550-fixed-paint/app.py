import spaces
import gradio as gr
import re
from PIL import Image,ImageFilter

import os
import numpy as np




def process_images(fg_image):
    # I'm not sure when this happen maybe api calling
    #return fg_image["background"],fg_image['layers'][0]
    def white_non_black(image):
        return np.where(image > 0, 255, image)

    mask = fg_image['layers'][0]
    mask = mask.convert("L")
    white_mask = Image.fromarray(white_non_black(np.array(mask)))
    fg_image["background"].paste(fg_image['layers'][0], (0, 0),white_mask)

    paint_masked = Image.composite(fg_image['layers'][0], Image.new("RGBA", fg_image['layers'][0].size, (0, 0, 0, 0)), white_mask)

    return fg_image["background"],white_mask

    

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
}
}

.text {
  font-size: 16px;
}
"""

def color_changed(color):
    #mode must be RGBA
    editor = gr.ImageEditor(brush=gr.Brush(colors=[color],color_mode="fixed"))
    return editor  

with gr.Blocks(css=css, elem_id="demo-container") as demo:
    with gr.Column():
        gr.HTML(read_file("demo_header.html"))
        gr.HTML(read_file("tools.html"))
    with gr.Row():
                with gr.Column():
                    #mode must be RGBA
                    image = gr.ImageEditor(height=800,sources=['upload','clipboard'],transforms=[],image_mode='RGBA', layers=False,  elem_id="Foreground", type="pil", label="Foreground",brush=gr.Brush(colors=["#808080"],default_size=50, color_mode="fixed"))
                    pick=gr.ColorPicker(label="color",value="#888",info="ImageEditor color is broken,pick color from here.reselect paint-tool and draw.")
                    pick.change(fn=color_changed,inputs=[pick],outputs=[image])
                    
                    
                    btn = gr.Button("Apply Paint", elem_id="run_button",variant="primary")
                            
                with gr.Column():
                    image_out = gr.Image(sources=[],label="Output", elem_id="output-img",format="webp")
                    mask_out = gr.Image(sources=[],label="Mask", elem_id="mask-img",format="jpg")

                    
            

    btn.click(fn=process_images, inputs=[image], outputs =[image_out,mask_out], api_name='infer')
    gr.Examples(
               examples=[
                   ["examples/00538245.jpg"],
                   ["examples/eye-close.jpg"],
                   ["examples/acc.jpg"]
                         ]
                         ,
                inputs=[image]
    )
    gr.HTML(read_file("demo_footer.html"))

    demo.launch()
