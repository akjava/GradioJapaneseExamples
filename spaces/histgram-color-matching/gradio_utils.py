

import os
import time
import io
import hashlib

def clear_old_files(dir="files",passed_time=60*60):
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

def get_image_id(image):
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    hash_object = hashlib.sha256(buffer.getvalue())
    hex_dig = hash_object.hexdigest()
    unique_id = hex_dig[:32]
    return unique_id

def save_image(image,extension="jpg",dir_name="files"):
    id = get_image_id(image)
    os.makedirs(dir_name,exist_ok=True)
    file_path = f"{dir_name}/{id}.{extension}"
    
    image.save(file_path)
    return file_path