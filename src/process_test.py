import cv2
import numpy as np
from matplotlib import pyplot as plt
from typing import Optional, Tuple
import plotly.express as px
import pandas as pd

def load_image(path: str) -> np.ndarray:
    """Load an image from the specified file path."""
    return cv2.imread(path)

def imshow(img: np.ndarray, ax: Optional[plt.Axes] = None, title: Optional[str] = None, cmap: Optional[str] = 'gray') -> None:
    """Display an image using matplotlib with options for subplot usage, title, and colormap."""
    if img.dtype == np.int32:  # This checks if the image is of type CV_32S
        img = img.astype(np.float32)  # Convert to float to avoid issues with negative numbers in markers
    
    if ax is None:
        plt.imshow(img, cmap=cmap)
        plt.title(title)
        plt.axis('off')
        plt.show()
    else:
        ax.imshow(img, cmap=cmap)
        ax.set_title(title)
        ax.axis('off')

def preprocess_image(img: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Convert image to grayscale and perform thresholding and morphological operations."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    ret, bin_img = cv2.threshold(gray, 0, 255, cv2.THRESH_OTSU)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    bin_img = cv2.morphologyEx(bin_img, cv2.MORPH_OPEN, kernel, iterations=2)
    return gray, bin_img, kernel

def compute_distance_transform(bin_img: np.ndarray) -> np.ndarray:
    """Compute the distance transform of a binary image."""
    return cv2.distanceTransform(bin_img, cv2.DIST_L2, 5)

def segment_image(bin_img: np.ndarray, dist_transform: np.ndarray, kernel: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Perform image segmentation using distance transform and thresholding to identify foreground and background."""
    sure_bg = cv2.dilate(bin_img, kernel, iterations=1)
    ret, sure_fg = cv2.threshold(dist_transform, 0.01 * dist_transform.max(), 255, cv2.THRESH_BINARY)
    sure_fg = sure_fg.astype(np.uint8)
    unknown = cv2.subtract(sure_bg, sure_fg)
    return sure_fg, sure_bg, unknown

def apply_watershed(img: np.ndarray, markers: np.ndarray) -> np.ndarray:
    """Apply the watershed algorithm to segment the image."""
    return cv2.watershed(img, markers)

import cv2
import numpy as np
from matplotlib import pyplot as plt
from typing import Optional, Tuple, List

def extract_contours_and_centers(markers: np.ndarray, max_area: Optional[float] = None) -> List[Tuple[np.ndarray, Tuple[int, int]]]:
    """
    Extract contours and calculate their centers for labeling purposes.

    Args:
    markers (np.ndarray): The segmented image with watershed markers.
    max_area (float, optional): The maximum area of a contour to include.

    Returns:
    List[Tuple[np.ndarray, Tuple[int, int]]]: A list of tuples containing each contour and its calculated center.
    """
    labels = np.unique(markers)
    wells_and_centers = []
    for label in labels[2:]:  # Skip the first two labels as they represent background and borders.
        target = np.where(markers == label, 255, 0).astype(np.uint8)
        contours, _ = cv2.findContours(target, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            area = cv2.contourArea(contour)
            if max_area is None or area < max_area:
                M = cv2.moments(contour)
                if M['m00'] != 0:
                    cX = int(M['m10'] / M['m00'])
                    cY = int(M['m01'] / M['m00'])
                    center = (cX, cY)
                    wells_and_centers.append((contour, center))
    return wells_and_centers

def annotate_wells(img: np.ndarray, wells_and_centers: List[Tuple[np.ndarray, Tuple[int, int]]]) -> np.ndarray:
    """
    Annotate the image with well IDs based on their contours and centers.

    Args:
    img (np.ndarray): The image to annotate.
    wells_and_centers (List[Tuple[np.ndarray, Tuple[int, int]]]): List of contours and their centers.

    Returns:
    np.ndarray: The annotated image.
    """
    annotated_image = img.copy()
    for index, (contour, center) in enumerate(wells_and_centers):
        cv2.drawContours(annotated_image, [contour], -1, (0, 255, 0), 2)
        cv2.putText(annotated_image, str(index + 1), center, cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
    return annotated_image

def calculate_mean_intensity(img: np.ndarray, contour: np.ndarray) -> float:
    """
    Calculate the mean intensity of the area inside the given contour.

    Args:
    img (np.ndarray): The image from which to calculate intensity.
    contour (np.ndarray): The contour that defines the ROI.

    Returns:
    float: The mean intensity within the contour.
    """
    mask = np.zeros_like(img, dtype=np.uint8)  # Create a mask that is the same size as the image
    cv2.drawContours(mask, [contour], -1, color=255, thickness=-1)  # Draw the contour filled with white
    masked_img = cv2.bitwise_and(img, img, mask=mask)  # Apply the mask to the image
    mean_val = cv2.mean(img, mask=mask)[0]  # Calculate the mean value of the pixels inside the contour
    return mean_val


# Usage of the functions
img = load_image("assets/roi.png")
imshow(img, title="Original Image")

gray, bin_img, kernel = preprocess_image(img)
imshow(bin_img, title="Binary Image after Morphology")

dist = compute_distance_transform(bin_img)
fig, axes = plt.subplots(nrows=2, ncols=2, figsize=(8, 8))
imshow(dist, axes[0, 1], title="Distance Transform")

sure_fg, sure_bg, unknown = segment_image(bin_img, dist, kernel)
imshow(sure_bg, axes[0, 0], title="Sure Background")

ret, markers = cv2.connectedComponents(sure_fg)
markers += 1
markers[unknown == 255] = 0

markers = apply_watershed(img, markers)
imshow(markers, title="Markers after Watershed")

# Define a maximum area threshold. Adjust this value based on your specific needs and the scale of your images.
MAX_CONTOUR_AREA = 1000  # Example threshold, you may need to adjust this.

wells_and_centers = extract_contours_and_centers(markers, max_area=1000)
annotated_image = annotate_wells(img, wells_and_centers)
imshow(annotated_image, title="Annotated Image with Well IDs")

wells, centers = zip(*wells_and_centers)

# Usage of the function
wells_intensities = [calculate_mean_intensity(gray, well) for well in wells]  # Assuming 'gray' is your grayscale image

# To visualize the mean intensities:
fig, ax = plt.subplots()
ax.bar(range(len(wells_intensities)), wells_intensities, color='blue')
ax.set_title("Mean Intensity of Each Well")
ax.set_xlabel("Well Index")
ax.set_ylabel("Mean Intensity")
plt.show()

# To visualize the mean intensities using Plotly in dark theme/mode:
df = pd.DataFrame({'Well Index': range(len(wells_intensities)), 'Mean Intensity': wells_intensities})
fig = px.bar(df, x='Well Index', y='Mean Intensity', title='Mean Intensity of Each Well', template='plotly_dark')
fig.show()

# This plots a simple bar graph showing the mean intensity of each well.