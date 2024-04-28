from typing import Optional, Tuple, List
import plotly.express as px
import pandas as pd
import numpy as np
import cv2

def load_image(path: str) -> np.ndarray:
    """Load an image from the specified file path."""
    return cv2.imread(path)

def preprocess_image(img: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Convert image to grayscale and perform thresholding and morphological operations."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, bin_img = cv2.threshold(gray, 0, 255, cv2.THRESH_OTSU)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    bin_img = cv2.morphologyEx(bin_img, cv2.MORPH_OPEN, kernel, iterations=2)
    return gray, bin_img, kernel

def segment_image(bin_img: np.ndarray, dist_transform: np.ndarray, kernel: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Perform image segmentation using distance transform and thresholding to identify foreground and background."""
    sure_bg = cv2.dilate(bin_img, kernel, iterations=1)
    sure_fg = cv2.threshold(dist_transform, 0.01 * dist_transform.max(), 255, cv2.THRESH_BINARY)[1].astype(np.uint8)
    unknown = cv2.subtract(sure_bg, sure_fg)
    return sure_fg, sure_bg, unknown

def extract_contours_and_centers(markers: np.ndarray, max_area: Optional[float] = None) -> List[Tuple[np.ndarray, Tuple[int, int]]]:
    """Extract contours and calculate their centers for labeling purposes."""
    labels = np.unique(markers)[2:]  # Skip background and borders
    wells_and_centers = []
    for label in labels:
        target = np.where(markers == label, 255, 0).astype(np.uint8)
        contours, _ = cv2.findContours(target, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            area = cv2.contourArea(contour)
            if max_area is None or area < max_area:
                M = cv2.moments(contour)
                if M['m00'] != 0:
                    center = (int(M['m10'] / M['m00']), int(M['m01'] / M['m00']))
                    wells_and_centers.append((contour, center))
    return wells_and_centers

def annotate_wells(img: np.ndarray, wells_and_centers: List[Tuple[np.ndarray, Tuple[int, int]]]) -> np.ndarray:
    """Annotate the image with well IDs based on their contours and centers."""
    annotated_image = img.copy()
    for index, (contour, center) in enumerate(wells_and_centers, start=1):
        cv2.drawContours(annotated_image, [contour], -1, (0, 255, 0), 2)
        cv2.putText(annotated_image, str(index), center, cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
    return annotated_image

def calculate_mean_intensity(img: np.ndarray, contour: np.ndarray) -> float:
    """Calculate the mean intensity of the area inside the given contour."""
    mask = np.zeros_like(img)
    cv2.drawContours(mask, [contour], -1, 255, -1)
    mean_val = cv2.mean(img, mask=mask)[0]
    return mean_val


if __name__ == "__main__":
    # Usage of the functions
    img = load_image("assets/array.jpg")
    gray, bin_img, kernel = preprocess_image(img)
    dist = cv2.distanceTransform(bin_img, cv2.DIST_L2, 5)

    sure_fg, sure_bg, unknown = segment_image(bin_img, dist, kernel)
    _, markers = cv2.connectedComponents(sure_fg)
    markers += 1
    markers[unknown == 255] = 0
    markers = cv2.watershed(img, markers)

    MAX_CONTOUR_AREA = 1000
    wells_and_centers = extract_contours_and_centers(markers, max_area=MAX_CONTOUR_AREA)
    annotated_image = annotate_wells(img, wells_and_centers)
    cv2.imwrite("annotated_image.png", annotated_image)

    wells, centers = zip(*wells_and_centers)
    wells_intensities = [calculate_mean_intensity(gray, well) for well in wells]

    df = pd.DataFrame({'Well Index': range(1, len(wells_intensities) + 1), 'Mean Intensity': wells_intensities})
    fig = px.scatter(df, x='Well Index', y='Mean Intensity', title='Mean Intensity of Each Well', template='plotly_dark')
    fig.show()