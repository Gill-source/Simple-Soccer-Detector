import cv2
import numpy as np

def apply_blur(image_path, lower_green=(30, 40, 0), upper_green=(100, 255, 255)):
    # 이미지 로드
    img = image_path
    
    # 강한 블러 적용
    blur_image = cv2.GaussianBlur(img, (41, 41), 0)
    
    # HSV 색상 공간으로 변환
    hsv = cv2.cvtColor(blur_image, cv2.COLOR_BGR2HSV)
    
    # 초록색 범위 정의
    lower_green = np.array([30, 40, 0])
    upper_green = np.array([100, 255, 255])
    
    # 초록색 마스크 생성
    green_mask = cv2.inRange(hsv, lower_green, upper_green)
    
    return green_mask

# Helper function to remove continuous white rows from top of mask (spectator region)
def remove_spectator_region(mask_person_shape, n):
    """
    Divide the mask into n vertical slices. For each slice, remove continuous white rows
    from the top of that slice until the white pixel count per row falls below 30% of the slice width.
    Mask (set to zero) all rows above each slice’s cutoff_row within that slice.
    Returns the modified mask and a list of n cutoff_row indices (one per slice).
    """
    height, width = mask_person_shape.shape
    slice_width = width // n
    cutoff_rows = []

    for i in range(n):
        # Determine column range for this slice
        start_col = i * slice_width
        # Ensure last slice goes to the right edge
        end_col = (i + 1) * slice_width if i < n - 1 else width
        current_slice = mask_person_shape[:, start_col:end_col]
        white_threshold = int((end_col - start_col) * 0.3)

        slice_cutoff = None
        for row_idx in range(height):
            # Count white pixels in this row of the slice
            white_count = np.count_nonzero(current_slice[row_idx] == 255)
            if white_count <= white_threshold:
                slice_cutoff = row_idx
                break
            # Fill this row in the slice completely with black
            mask_person_shape[row_idx, start_col:end_col] = 0

        if slice_cutoff is None:
            slice_cutoff = height

        # Mask all rows above the cutoff within this slice
        mask_person_shape[:slice_cutoff, start_col:end_col] = 0
        cutoff_rows.append(slice_cutoff)

    return mask_person_shape, cutoff_rows