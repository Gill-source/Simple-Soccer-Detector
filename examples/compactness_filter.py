# 파일: compactness_filter.py

import cv2
import numpy as np

def remove_low_compactness(mask: np.ndarray, compactness_threshold: float = 0.3) -> np.ndarray:
    """
    주어진 이진 마스크(mask)에서 compactness 값이 threshold 이하인 모든 contour를 지웁니다.
    
    Args:
        mask: cv2.findContours가 동작할 수 있는 0/255 이진 이미지 (예: Canny나 detect_ball 결과)
        compactness_threshold: compactness < threshold 이면 지울 contour 기준.
                             (4*pi*area / perimeter^2)
    
    Returns:
        필터링 후 mask (원본 mask가 직접 수정되므로, 호출자는 반환값을 그대로 사용하면 됩니다)
    """
    # Contour 검출 (외곽선)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area == 0:
            continue

        perimeter = cv2.arcLength(cnt, True)
        if perimeter == 0:
            continue

        compactness = 4 * np.pi * (area / (perimeter * perimeter))
        if compactness < compactness_threshold:
            # contour 내부를 검정(0)으로 칠해서 제거
            cv2.drawContours(mask, [cnt], -1, 0, thickness=cv2.FILLED)

    return mask