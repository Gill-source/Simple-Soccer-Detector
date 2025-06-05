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