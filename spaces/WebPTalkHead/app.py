import spaces
import gradio as gr
import subprocess
import re
from PIL import Image,ImageSequence
import webp
import io
import hashlib
import os
import time
import shutil
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


output_dir = "outputs"
passed_time =  60 * 20
def load_text(text_path: str) -> str:
    with open(text_path, 'r', encoding='utf-8') as f:
        text = f.read()

    return text

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


def process_images(normal_image,mouth_open_image,eye_close_image,duration=100,pattern = "nnnmmmnenmmmnnnmmmnnnmmmnnnmmm",looping = True):
    # validating images
    
    # cache control
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
    clear_old_files(output_dir,passed_time)
    
    if normal_image is None or mouth_open_image is None or eye_close_image is None:
         raise gr.Error("Need Normal Mouth Eyes 3 images")
    #validate check
    normal_width, normal_height = normal_image.size
    mouth_width, mouth_height = mouth_open_image.size
    eye_width, eye_height = eye_close_image.size
    if normal_width!=mouth_width or normal_height!=mouth_height:
         raise gr.Error("Mouth Image Size must be same as normal")
    if normal_width!=eye_width or normal_height!=eye_height:
         raise gr.Error("Eyes Image Size must be same as normal")
    if duration<1:
         raise gr.Error("min duration is 1")
    
    pattern = pattern[:32]
    if pattern == "":
         pattern = "nme"
    else:
        valids =["n","m","e"]
        for ch in pattern:
            if ch not in valids:
                raise gr.Error("invalid pattern contain.pattern must be n or e or m")
              
    
    frames = []
    for ch in pattern:
        if ch == "m":
            frames.append(mouth_open_image)
        elif ch == "e":
            frames.append(eye_close_image)
        else:
            frames.append(normal_image)

    loop = 0  if looping else 1  #MUST BE ZERO,NOT TRUE
    
    output_buffer = io.BytesIO()
    frames[0].save(output_buffer, 
                   save_all=True, 
                   append_images=frames[1:], 
                   duration=duration, 
                   loop=loop, 
                   format='WebP')
    
    hash_object = hashlib.sha256(output_buffer.getvalue())
    hex_dig = hash_object.hexdigest()
    unique_id = hex_dig[:32]

    
    output_path = f"{output_dir}/{unique_id}.webp"
    with open(output_path,"wb") as f:
         f.write(output_buffer.getvalue())
    
    return output_path



with gr.Blocks(css=css, elem_id="demo-container") as demo:
    with gr.Column():
        gr.HTML(load_text("demo_header.html"))
        gr.HTML(load_text("demo_tools.html"))
    with gr.Row():
                with gr.Column():
                    image_normal = gr.Image(sources=['upload','clipboard'],  elem_id="image_normal", type="pil", label="Normal Image",height=400, value=None)
                    with gr.Row(elem_id="prompt-container",  equal_height=False):
                        with gr.Row():
                            btn = gr.Button("Make WebP Animation", elem_id="run_button")
                    image_mouth = gr.Image(sources=['upload','clipboard'],  elem_id="image_mouth", type="pil", label="Mouth Opened",height=400, value=None)
                    image_eyes = gr.Image(sources=['upload','clipboard'],  elem_id="image_eyes", type="pil", label="Eyes Closed",height=400, value=None)
                    id_input=gr.Text(label="Name", visible=False)
                    with gr.Accordion(label="Advanced Settings", open=False):
                        with gr.Row(equal_height=True):
                            animation_time = gr.Number(value=100, minimum=1, maximum=1000, step=10, label="Animation Time")
                            looping = gr.Checkbox(label="Loop",value=True)
                        with gr.Row( equal_height=True):
                            timing_seat = gr.Text(value="nnnmmmnenmmmnnnmmmnnnmmm", max_length=32,label="Timing Seat")
                with gr.Column():
                    image_out = gr.Image(sources=[],label="Output", elem_id="output-img",type="filepath", format="webp")
                    
    btn.click(fn=process_images, inputs=[image_normal, image_mouth,image_eyes,animation_time,timing_seat,looping], outputs =image_out, api_name='infer')
    gr.Examples(
               examples=[
                    ["examples/00003245_normal.jpg","examples/00003245_mouth.jpg","examples/00003245_eyes.jpg","examples/00003245.webp"],
                    ["examples/00207245_normal.png","examples/00207245_mouth.png","examples/00207245_eyes.png","examples/00207245.webp"],
                    ["examples/00350245_normal.jpg","examples/00350245_mouth.jpg","examples/00350245_eyes.jpg","examples/00350245.webp"],
                    ["examples/00538245_normal.jpg","examples/00538245_mouth.jpg","examples/00538245_eyes.jpg","examples/00538245.webp"],
                    ["examples/00828003_00.jpg","examples/00828003_09.jpg","examples/00828003_99.jpg","examples/00828003.webp"],
                    ["examples/00825000_00.jpg","examples/00825000_09.jpg","examples/00825000_99.jpg","examples/00825000.webp"],
                    ["examples/00824008_00.jpg","examples/00824008_09.jpg","examples/00824008_99.jpg","examples/00824008.webp"],
                    ["examples/prompt01_normal.jpg","examples/prompt01_mouth.jpg","examples/prompt01_eyes.jpg","examples/prompt01.webp"],
                    ],
                inputs=[image_normal,image_mouth,image_eyes,image_out],
                
    )
    gr.HTML(
       gr.HTML(load_text("demo_footer.html"))
    )

    if __name__ == "__main__":
        demo.launch()