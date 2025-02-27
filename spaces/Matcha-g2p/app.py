import spaces
import gradio as gr
import cleaners

#@spaces.GPU(duration=120)
def process_text(text):
    
    output = cleaners.english_cleaners_piper(text)
    #output = english_cleaners2(text)
    return output
    

# code from https://huggingface.co/spaces/diffusers/stable-diffusion-xl-inpainting/blob/main/app.py
def read_file(file_path: str) -> str:
    """read the text of target file
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    return content
#demo.launch(share=True)
#css=css,
demo_blocks = gr.Blocks( elem_id="demo-container")
with demo_blocks as demo:
    gr.HTML(read_file("demo_header.html"))
    with gr.Row():
                with gr.Column():
                   
                        text = gr.Textbox(placeholder="Your text(Grapheme)",value="hello world", show_label=False, elem_id="prompt")
                        btn = gr.Button("G2P", elem_id="run_button")
                        text_out = gr.Textbox(label="Output", elem_id="output-img", )
                    
                        
                    
                    
            

    btn.click(fn=process_text, inputs=[text], outputs =text_out, api_name='infer')
    #prompt.submit(fn=process_images, inputs=[image, prompt, negative_prompt, guidance_scale, steps, strength, scheduler], outputs=[image_out, share_btn_container])
    #share_button.click(None, [], [], _js=share_js)

    gr.Examples(
               examples=[["hello world"],["How are you doing today?"],["I'm good, thanks. Anything exciting happening in your life lately?"]]
,
                #fn=predict,
                inputs=[text],
                cache_examples=False,
    )
    gr.HTML(
        """
            <div style="text-align: center;">
                <p></a> - Gradio Demo by 🤗 Hugging Face
                </p>
            </div>
        """
    )

demo_blocks.queue(max_size=25).launch(share=True)
