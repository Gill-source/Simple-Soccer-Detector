import cv2
import numpy as np

def morphology_based_width_filter(combined_mask, min_width=8):
    """
    모폴로지 연산으로 좁은 연결부 제거
    """
    # Opening 연산으로 좁은 연결부 끊기
    # 커널 크기를 min_width/2로 설정
    kernel_size = max(3, min_width // 2)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
    
    # Opening: 침식 후 팽창
    opened = cv2.morphologyEx(combined_mask, cv2.MORPH_OPEN, kernel)
    
    # 너무 많이 줄어든 부분 복원 (단, 연결은 유지하지 않음)
    restore_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    restored = cv2.dilate(opened, restore_kernel, iterations=2)
    
    # 원본 마스크와 교집합으로 경계 정리
    result = cv2.bitwise_and(combined_mask, restored)
    
    return result

def improved_watershed(combined_mask, min_connection_width=2):
    """
    개선된 Watershed - 좁은 연결부 필터링 포함
    """
    # 1. 좁은 연결부 제거
    filtered_mask = morphology_based_width_filter(combined_mask, min_connection_width)
    
    # 2. Distance Transform
    distance = cv2.distanceTransform(filtered_mask, cv2.DIST_L2, 5)
    distance = cv2.GaussianBlur(distance, (5, 5), 0)
    
    # 3. 적응적 임계값 (더 민감하게)
    threshold = 0.1 * distance.max()
    _, peaks = cv2.threshold(distance, threshold, 255, cv2.THRESH_BINARY)
    peaks = np.uint8(peaks)
    
    # 4. 피크 강화
    kernel_peak = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    peaks = cv2.dilate(peaks, kernel_peak, iterations=1)
    
    # 5. Watershed
    num_labels, markers = cv2.connectedComponents(peaks)
    markers = markers + 1
    markers[filtered_mask == 0] = 0
    
    filtered_mask_3ch = cv2.cvtColor(filtered_mask, cv2.COLOR_GRAY2BGR)
    cv2.watershed(filtered_mask_3ch, markers)
    
    # 6. Bounding box 추출 추가
    bounding_boxes = []
    unique_labels = np.unique(markers)
    
    for label in unique_labels:
        if label <= 0:  # 배경과 경계선 제외
            continue
            
        # 해당 라벨의 마스크 생성
        label_mask = (markers == label).astype(np.uint8) * 255
        
        # 면적 확인
        area = cv2.countNonZero(label_mask)
        if area < 32:  # 최소 면적
            continue
            
        # 윤곽선 찾기
        contours, _ = cv2.findContours(label_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            
            # 선수 형태 검증 (세로 > 가로, 적절한 크기)
            if h > w and 5 <= w <= 100 and 10 <= h <= 200:
                bounding_boxes.append((x, y, w, h))
    
    return bounding_boxes  # bounding box 리스트만 반환