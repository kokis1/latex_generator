import numpy as np
import cv2
from pathlib import Path
from dataclasses import dataclass

@dataclass
class Chunk:
   index: int
   image: np.ndarray
   top: int
   bottom: int

def equal_splits(height: int, n: int) -> list[tuple[int, int]]:
   step = height // n
   boundaries = list(range(0, height, step)) + [height]
   return list(zip(boundaries[:-1], boundaries[1:]))

def find_whitespace_splits(image: np.ndarray, max_chunks: int) -> list[tuple[int, int]]:
   '''Projects the pixel darkness onto the y-axis and finds the lines that are almost completely white.
      These provide natural points to chunk the text.'''
   # row_darkness[i] = number of dark pixels in row i
   row_darkness = np.sum(image < 128, axis=1)
   h = image.shape[0]

   # A row counts as whitespace if it has very few dark pixels
   whitespace_threshold = image.shape[1] * 0.02
   is_white = row_darkness < whitespace_threshold

   # Find contiguous whitespace bands
   bands: list[tuple[int, int]] = []
   in_band = False
   band_start = 0
   for y, white in enumerate(is_white):
      if white and not in_band:
         in_band = True
         band_start = y
      elif not white and in_band:
         in_band = False
         bands.append((band_start, y))
   if in_band:
      bands.append((band_start, h))

   # Pick up to max_chunks-1 split points (midpoints of whitespace bands)
   # Evenly spaced across the page so chunks are roughly equal in content
   if not bands:
      return equal_splits(h, max_chunks)

   step = max(1, len(bands) // (max_chunks - 1))
   split_rows = [((b[0] + b[1]) // 2) for b in bands[::step]]

   # Convert split rows into (top, bottom) pairs
   boundaries = [0] + split_rows + [h]
   return list(zip(boundaries[:-1], boundaries[1:]))

def crop_chunks(image: np.ndarray, split_points: list[tuple[int, int]]) -> list[Chunk]:
   '''splits the image into chunks based on the split points'''

   chunks = []
   for i, (top, bottom) in enumerate(split_points):
      
      # Skips very thin regions
      if bottom - top < 10:
         continue
      cropped = image[top:bottom, :]
      chunks.append(Chunk(index=1, image=cropped, top=top, bottom=bottom))
   return chunks

def save_chunks(chunks: list[Chunk], output_dir: Path) -> list[Path]:
   '''writes the chunks to the disk as .PNGs (for debugging)'''
   output_dir.mkdir(parents=True, exist_ok=True)
   paths = []
   for chunk in chunks:
      path = output_dir / f"chunk_{chunk.index}.png"
      cv2.imwrite(str(path), chunk.image)
      paths.append(path)
   return paths


def segment(image: np.ndarray, max_chunks: int = 10) -> list[Chunk]:
   '''Splits the file into horizontal strips using whitespace detection.
      Falls back to equally spaced strips if none are detected.'''
   split_points = find_whitespace_splits(image, max_chunks)
   return crop_chunks(image, split_points)