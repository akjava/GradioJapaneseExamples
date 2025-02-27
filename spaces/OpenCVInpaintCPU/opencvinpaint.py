import os
import sys

import cv2
import numpy as np
from PIL import Image


debug = False

def gray3d_to_2d(grayscale: np.ndarray) -> np.ndarray:
    channel = grayscale.shape[2] if grayscale.ndim == 3 else 1 
    if channel!=1:
        text = f"grayscale shape = {grayscale.shape} channel = {channel} ndim = {grayscale.ndim} size = {grayscale.size}"
        raise ValueError(f"color maybe rgb or rgba {text}")

    if grayscale.ndim == 2:
        return grayscale
    return np.squeeze(grayscale)

def pil_to_cv(image):
    cv_image = np.array(image, dtype=np.uint8)
    if cv_image.shape[2] == 3:  # カラー
        cv_image = cv2.cvtColor(cv_image, cv2.COLOR_RGB2BGR)
    elif cv_image.shape[2] == 4: #
        cv_image = cv2.cvtColor(cv_image, cv2.COLOR_RGBA2BGR)
    return cv_image

def blend_rgb_images(image1: np.ndarray, image2: np.ndarray, mask: np.ndarray) -> np.ndarray:

    if image1.shape != image2.shape or image1.shape[:2] != mask.shape:
        raise ValueError("not same shape")

    # 画像を float 型に変換
    image1 = image1.astype(float)
    image2 = image2.astype(float)

    # mask to 3 chan 0 -1 value
    alpha = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR).astype(float) / 255.0

    # calcurate blend
    blended = (1 - alpha) * image1 + alpha * image2

    return blended.astype(np.uint8)

def process_cvinpaint(image,mask_image,inpaint_radius,blur_radius,edge_expand,inpaint_mode,dilate=0):
    #print("process cvinpaint")
    #print(blur_radius,",",edge_expand)
    cv_image = pil_to_cv(image)

    cv_mask = pil_to_cv(mask_image)

  


    cv_gray = cv2.cvtColor(cv_mask,cv2.COLOR_BGR2GRAY)
    

    mask = gray3d_to_2d(cv_gray)
    if dilate>0:
        kernel = np.ones((dilate, dilate), np.uint8)
        mask = cv2.dilate(mask, kernel, iterations=1)

    #cv2.imwrite("_mask.jpg",mask)
    #cv2.imwrite("_image.jpg",cv_image)
    mode = cv2.INPAINT_TELEA if inpaint_mode == "Telea" else cv2.INPAINT_NS
    img_inpainted = cv2.inpaint(cv_image, mask,inpaint_radius, mode)
    if debug:
        cv2.imwrite("close_eye_inpaint.jpg",img_inpainted)
    
    
    ## blur
    if blur_radius > 0:
        if blur_radius%2==0:
            blur_radius += 1
        #print(blur_radius)
        blurred_image = cv2.GaussianBlur(img_inpainted, (blur_radius, blur_radius), 0) #should be odd
        if debug:
            cv2.imwrite("close_eye_inpaint_burred.jpg",blurred_image)
    else:
        blurred_image = img_inpainted

    # expand edge and blur
    kernel = np.ones((edge_expand, edge_expand), np.uint8)
    extend_mask = cv2.dilate(mask, kernel, iterations=1)

    if edge_expand > 0 and blur_radius > 0:
        extend_burred_mask = cv2.GaussianBlur(extend_mask, (blur_radius, blur_radius), 0)
    else:
        extend_burred_mask = extend_mask

    
    img_inpainted = blend_rgb_images(img_inpainted,blurred_image,extend_burred_mask)

    output_image = img_inpainted.copy()
    
    if output_image.shape[2] == 3:  # カラー
        output_image = cv2.cvtColor(output_image, cv2.COLOR_BGR2RGB)
    
    return Image.fromarray(output_image),Image.fromarray(mask)

if __name__ == "__main__":
    image = Image.open(sys.argv[1])
    mask  = Image.open(sys.argv[2])
    output = process_cvinpaint(image,mask)
    output.save(sys.argv[3])