import cv2
import numpy as np
from pathlib import Path

"""def load_grayscale(image_path: str | Path) -> np.ndarray:
   '''Loads the image as a grayscale from the path'''
   image = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
   return image

def load_colour(image_path: str | Path) -> np.ndarray:
   image = cv2.imread(str(image_path), cv2.IMREAD_COLOR_RGB)
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

   return image"""


def crop_to_page(img: np.ndarray) -> np.ndarray:
    """
    Detects the largest light-coloured rectangular region (the page)
    and crops to it. Falls back to the full image if no clear page
    boundary is found.
    """
    # Convert to HSV — easier to isolate light/white regions than in BGR
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # Mask for light regions: low saturation, high value (brightness)
    # This captures white and near-white paper regardless of lighting
    lower = np.array([0, 0, 160])
    upper = np.array([180, 60, 255])
    mask = cv2.inRange(hsv, lower, upper)

    # Clean up the mask — close small holes, remove speckle
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (20, 20))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

    contours, _ = cv2.findContours(
        mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    if not contours:
        return img

    # Take the largest contour — assumed to be the page
    largest = max(contours, key=cv2.contourArea)

    # Reject if the detected region is less than 20% of the image
    # (probably noise rather than a real page)
    image_area = img.shape[0] * img.shape[1]
    if cv2.contourArea(largest) < image_area * 0.2:
        return img

    # Get a tight bounding rectangle and crop with a small margin
    x, y, w, h = cv2.boundingRect(largest)
    margin = 20
    x = max(0, x - margin)
    y = max(0, y - margin)
    w = min(img.shape[1] - x, w + margin * 2)
    h = min(img.shape[0] - y, h + margin * 2)

    return img[y:y + h, x:x + w]


def resize_if_large(img: np.ndarray, max_dimension: int = 1600) -> np.ndarray:
    h, w = img.shape[:2]
    if max(h, w) <= max_dimension:
        return img
    scale = max_dimension / max(h, w)
    return cv2.resize(img, (int(w * scale), int(h * scale)))


def load_and_clean(image_path: str | Path) -> np.ndarray:
    """
    Load a colour image, crop to the page content, and resize if needed.
    """
    img = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError(f"Could not load image at {image_path}")

    img = crop_to_page(img)
    img = resize_if_large(img, max_dimension=1600)

    return img

def save_debug(img: np.ndarray, path: str | Path) -> None:
    cv2.imwrite(str(path), img)