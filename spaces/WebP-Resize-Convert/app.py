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
    files = os.listdir(dir)
    current_time = time.time()
    for file in files:
         file_path = os.path.join(dir,file)
         
         ctime = os.stat(file_path).st_ctime
         diff = current_time - ctime
         print(f"ctime={ctime},current_time={current_time},passed_time={passed_time},diff={diff}")
         if diff > passed_time:
              os.remove(file_path)
              print(f"file removed {file_path}")#TODO remove later


def get_image_id(image):
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    hash_object = hashlib.sha256(buffer.getvalue())
    hex_dig = hash_object.hexdigest()
    unique_id = hex_dig[:32]
    return unique_id

dir_name ="images"
passed_time = 60*3


def process_create_webp(images,duration=100, loop=0,quality=85):
    frames = []
    for image_file in images:
        frames.append(image_file)
    
    output_buffer = io.BytesIO()
    frames[0].save(output_buffer, 
                   save_all=True, 
                   append_images=frames[1:], 
                   duration=duration, 
                   loop=loop, 
                   format='WebP',
                   quality=quality
                   )
    
    return output_buffer.getvalue()

def process_create_apng(images,duration=100, disposal=1,blend=0,loop=0):
    frames = []
    for image_file in images:
        frames.append(image_file)
    
    output_buffer = io.BytesIO()
    frames[0].save(output_buffer, 
                   save_all=True, 
                   append_images=frames[1:], 
                   #duration=duration, disposal=0,blend=1,
                   duration=duration, disposal=disposal,blend=blend,
                   loop=loop, 
                   format='png')
    
    return output_buffer.getvalue()

def process_create_gif(images,duration=100, quantize=False,disposal=1,blend=0,loop=0):
    frames = []
    for image_file in images:
        if quantize:
            image_file = image_file.quantize(colors=256, method=2)
            #image_file = image_file.quantize()
        

        frames.append(image_file)
    
    output_buffer = io.BytesIO()
    frames[0].save(output_buffer, 
                   save_all=True, 
                   append_images=frames[1:], 
                   #duration=duration, disposal=0,blend=1,
                   duration=duration, disposal=disposal,blend=blend,
                   loop=loop, 
                   format='gif',
                   optimize=False
                   #dither=Image.FLOYDSTEINBERG
                   )
    
    return output_buffer.getvalue()

def save_to_image(image,extension="png",quality=0.8):
    id = get_image_id(image)
    path = os.path.join(dir_name,f"{id}.{extension}")
    if extension == "jpg" or extension == "jpeg" or extension == "webp":
        image.convert("RGB").save(path,quality=quality)
    else:
        image.save(path)
    return path


def convert_webp_to_images(webp_path):
     # add list
  frames = []
  durations = []
  Image.init()
  image = Image.open(webp_path)
  if hasattr(image,"n_frames"):
    for i in range(image.n_frames):
        image.seek(i)
        frame = image.copy()
        frames.append(frame)
        # frame.info must be dictionary
        duration = frame.info.get("duration",100)
        durations.append(duration)
  else:# webp never happen?
      frames.append(image)
      durations.append(100)#default

  return frames,durations

def buffer_to_id(buffer_value):
    hash_object = hashlib.sha256(buffer_value)
    hex_dig = hash_object.hexdigest()
    unique_id = hex_dig[:32]
    return unique_id

def process_images(input_path,same_size=False,image_width=128,file_format="webp",webp_quality=85):
    if input_path == None:
         raise gr.Error("need image")
    
    # cache control
    if not os.path.exists(dir_name):
        os.mkdir(dir_name)
    clear_old_files(dir_name,passed_time)



    images =[]
    frames,durations = convert_webp_to_images(input_path)
    new_frames = []


    new_width,new_height = frames[0].size
    if not same_size and image_width!=new_width:
       
        ratio = new_height/new_width
        new_height = int(image_width*ratio)
        new_width = image_width
        #print(f"ratio = {ratio} new size {new_width} x {new_height}")
        for frame in frames:
            new_frame = frame.resize((new_width,new_height))# extremly slow Image.LANCZOS
            new_frames.append(new_frame)
    else:
        new_frames = frames

    if file_format == "webp":
        webp_buffer = process_create_webp(new_frames,durations,webp_quality)
        webp_id = buffer_to_id(webp_buffer)
        webp_path = os.path.join(dir_name,f"{webp_id}.webp")
        with open(webp_path, 'wb') as f:
            f.write(webp_buffer)
        
        images.append((webp_path,"webp"))

    elif file_format == "apng":
        apng_buffer = process_create_apng(new_frames,durations)
        apng_id = buffer_to_id(apng_buffer)
        apng_path = os.path.join(dir_name,f"{apng_id}.apng")
        with open(apng_path, 'wb') as f:
            f.write(apng_buffer)
        
        images.append((apng_path,"apng"))

    elif file_format == "gif":
        gif_buffer = process_create_gif(new_frames,durations,False)
        gif_id = buffer_to_id(gif_buffer)
        gif_path = os.path.join(dir_name,f"{gif_id}.gif")
        with open(gif_path, 'wb') as f:
            f.write(gif_buffer)
        
        images.append((gif_path,"gif"))
    else:
        f,extension = file_format.split("-")
        for i ,frame in enumerate(new_frames):
            path = save_to_image(frame,extension,webp_quality)
            images.append((path,f"index {i}"))

    return images
    

def read_file(path: str) -> str:
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    return content

def test_echo(param):
     return param

def samesize_changed(check,slider):
    return gr.Slider(label="Image Width",
                            minimum=8,
                            maximum=2048,
                            step=1,
                            value=slider,
                            interactive=not check)

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
js = """
function(path){
console.log(path)
return path
}
"""

with gr.Blocks(css=css, elem_id="demo-container") as demo:
    with gr.Column():
        gr.HTML(read_file("demo_header.html"))
        gr.HTML(read_file("demo_tools.html"))
    with gr.Row():
                with gr.Column():
                    file = gr.File(label="WebP Upload")
                    image = gr.Image(sources=[],image_mode='RGB',  elem_id="Image", type="filepath", label="Preview WebP")
                    
                    #file.select(fn=test_echo,inputs=[file])
                    
                    file.upload(fn=test_echo,inputs=[file],outputs=[image])
                    file.clear(fn=test_echo,inputs=[file],outputs=[image])

                    btn = gr.Button("Convert", elem_id="run_button",variant="primary")
                    # type choice
                    # size slider

                    file_format=gr.Dropdown(
                    ["webp", "apng", "gif","images-png","images-jpg"], label="Animation Format", info="Convert to  Animattion" )
                    
                    same_size = gr.Checkbox(label="Same Size",value=False)
                           
                    image_width = gr.Slider(
                            label="Image Width",info = "new animation size",
                            minimum=8,
                            maximum=2048,
                            step=1,
                            value=128,
                            interactive=True)
                    same_size.change(fn=samesize_changed,inputs=[same_size,image_width],outputs=[image_width])
                    
                    with gr.Accordion(label="Advanced Settings", open=False):
                        with gr.Row( equal_height=True):
                           webp_quality = gr.Slider(
                            label="WebP Quality",info = "this change file size",
                            minimum=0,
                            maximum=100,
                            step=1,
                            value=85,
                            interactive=True)
                
                with gr.Column():
                    image_out = gr.Gallery(height=800,label="Output", elem_id="output-img",format="webp", columns=[4],rows=[2],preview=True)

                    
            

    btn.click(fn=process_images, inputs=[file,same_size,image_width,file_format,webp_quality], outputs =[image_out], api_name='infer')
    gr.Examples(
               examples=[
                   ["examples/1024.webp","examples/1024.webp"],
                   #["images/00346245_00006200.jpg", "images/00346245_00003200.jpg","images/00346245_mask.jpg",10,0,"images/00346245_mixed.jpg"]
                  
                         ]
                         ,
                inputs=[image,file]#example not fire event
    )
    gr.HTML(read_file("demo_footer.html"))
    if __name__ == "__main__":
        demo.launch()
