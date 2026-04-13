import cv2
import numpy as np
from pathlib import Path

'''def load_grayscale(image_path: str | Path) -> np.ndarray:
   '''Loads the image as a grayscale from the path'''
   image = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
   return image

def binarise(image: np.ndarray) -> np.ndarray:
   '''Finds the black/white cutoff to increase the contrast'''
   _, binary_image = cv2.threshold(
      image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
   )
   return binary_image

def deskew(image: np.ndarray) -> np.ndarray:
   '''rotates the image to correct for tilted photos'''
   
   # Find dark pixel coords
   coords = np.column_stack(np.where(image < 128))
   
   # Not enough content to measure skew
   if len(coords) < 10:
      return image  
   
   # Finds the Angle
   angle = cv2.minAreaRect(coords)[-1]
   if angle < -45:
      angle = 90 + angle
   
   # Skip rotation if skew is negligible
   if abs(angle) < 0.5:
      return image
   
   # Finds the centre of the image and warps to a rectangle
   height, width = image.shape
   centre = (width // 2, height // 2)
   matrix = cv2.getRotationMatrix2D(centre, angle, 1.0)
   return cv2.warpAffine(
      image, matrix, (width, height),
      flags=cv2.INTER_CUBIC,
      borderMode=cv2.BORDER_REPLICATE
   )


def denoise(image: np.ndarray) -> np.ndarray:
   '''Light noise reduction: removes speckles without removing lines'''
   kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
   return cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel)

def save_debug(image: np.ndarray, path: str | Path) -> None:
   '''saves the image at a debug location'''
   cv2.imwrite(str(path), image)

def load_and_clean(image_path: str | Path, save_image_path: None | str | Path = None) -> np.ndarray:
   '''loads and cleans up the image'''
   image = load_grayscale(image_path)
   image = binarise(image)
   image = deskew(image)
   image = denoise(image)

   if save_image_path != None:
      save_debug(image, save_image_path)

   return image'''

def load_and_clean(image_path: str | Path) -> np.ndarray:
    """
    Minimal preprocessing — keep the image as close to the original
    as possible so the VLM can read it. We can add more aggressive
    preprocessing later once we confirm the VLM can see the content.
    """
    img = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError(f"Could not load image at {image_path}")

    # Resize if very large — VLMs don't benefit from huge images
    # and it slows down inference significantly
    max_dimension = 1600
    h, w = img.shape[:2]
    if max(h, w) > max_dimension:
        scale = max_dimension / max(h, w)
        img = cv2.resize(img, (int(w * scale), int(h * scale)))

    return img