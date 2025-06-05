import cv2
import numpy as np

def fast_object_detection_connected_components(combined_mask, min_area=32):
    """
    Connected Components를 이용한 빠른 객체 검출
    """
    # Connected Components 라벨링 (cv2.findContours보다 빠름)
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(combined_mask, connectivity=8)
    
    bounding_boxes = []
    for i in range(1, num_labels):  # 0은 배경이므로 제외
        area = stats[i, cv2.CC_STAT_AREA]
        if area > min_area:
            x = stats[i, cv2.CC_STAT_LEFT]
            y = stats[i, cv2.CC_STAT_TOP]
            w = stats[i, cv2.CC_STAT_WIDTH]
            h = stats[i, cv2.CC_STAT_HEIGHT]
            
            # 세로 > 가로 조건 및 크기 필터링
            if h >= w and 1 <= w <= 100 and 1 <= h <= 200:
                bounding_boxes.append((x, y, w, h))
    
    return bounding_boxes


def extract_player_bounding_boxes(combined_mask, min_area=2, min_width=1, max_width=25, min_height=2, max_height=100):
    """
    combined_mask에서 선수 영역의 bounding box를 추출
    조건: 세로가 가로보다 길고, 세로나 가로 길이가 적절한 범위 내에 있음
    
    Args:
        combined_mask: 이진 마스크 (0과 255로 구성)
        min_area: 최소 영역 크기 (이보다 작은 영역은 노이즈로 간주)
        min_width: 최소 가로 길이 (기본값: 10)
        max_width: 최대 가로 길이 (기본값: 150)
        min_height: 최소 세로 길이 (기본값: 20)
        max_height: 최대 세로 길이 (기본값: 300)
    
    Returns:
        bounding_boxes: [(x, y, w, h), ...] 형태의 리스트
    """
    # 윤곽선 찾기
    contours, _ = cv2.findContours(combined_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    bounding_boxes = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > min_area:  # 최소 면적 필터링
            x, y, w, h = cv2.boundingRect(cnt)
            
            # 세로가 가로보다 길어야 함 (사람의 기본 형태)
            if h > w:
                # 가로, 세로 길이 범위 필터링
                if (min_width <= w <= max_width) and (min_height <= h <= max_height):
                    bounding_boxes.append((x, y, w, h))
    
    return bounding_boxes

def fast_object_detection_projection(combined_mask):
    """
    수직/수평 projection을 이용한 빠른 객체 분리
    """
    # 수직 projection (각 열의 합)
    vertical_proj = np.sum(combined_mask, axis=0)
    
    # 객체 경계 찾기 (0이 아닌 구간)
    non_zero_cols = np.where(vertical_proj > 0)[0]
    
    if len(non_zero_cols) == 0:
        return []
    
    # 연속된 구간 찾기
    diff = np.diff(non_zero_cols)
    split_points = np.where(diff > 10)[0]  # 10픽셀 이상 떨어진 구간은 다른 객체
    
    bounding_boxes = []
    start_idx = 0
    
    for split_point in np.append(split_points, len(non_zero_cols)-1):
        x_start = non_zero_cols[start_idx]
        x_end = non_zero_cols[split_point]
        
        # 해당 x 범위에서 y 범위 찾기
        roi = combined_mask[:, x_start:x_end+1]
        horizontal_proj = np.sum(roi, axis=1)
        non_zero_rows = np.where(horizontal_proj > 0)[0]
        
        if len(non_zero_rows) > 0:
            y_start = non_zero_rows[0]
            y_end = non_zero_rows[-1]
            w = x_end - x_start + 1
            h = y_end - y_start + 1
            
            # 필터링 조건
            if h > w and w >= 15 and h >= 30:
                bounding_boxes.append((x_start, y_start, w, h))
        
        start_idx = split_point + 1
    
    return bounding_boxes


def merge_nearby_boxes(boxes, merge_threshold=50):
    """
    가까운 bounding box들을 병합
    
    Args:
        boxes: [(x, y, w, h), ...] 형태의 bounding box 리스트
        merge_threshold: 병합 기준 거리
    
    Returns:
        merged_boxes: 병합된 bounding box 리스트
    """
    if len(boxes) <= 1:
        return boxes
    
    def boxes_distance(box1, box2):
        x1, y1, w1, h1 = box1
        x2, y2, w2, h2 = box2
        center1 = (x1 + w1//2, y1 + h1//2)
        center2 = (x2 + w2//2, y2 + h2//2)
        return np.sqrt((center1[0] - center2[0])**2 + (center1[1] - center2[1])**2)
    
    merged = []
    used = set()
    
    for i, box1 in enumerate(boxes):
        if i in used:
            continue
            
        group = [box1]
        for j, box2 in enumerate(boxes):
            if j != i and j not in used and boxes_distance(box1, box2) < merge_threshold:
                group.append(box2)
                used.add(j)
        used.add(i)
        
        # 그룹의 모든 박스를 포함하는 최소 사각형 계산
        x_coords = []
        y_coords = []
        for x, y, w, h in group:
            x_coords.extend([x, x + w])
            y_coords.extend([y, y + h])
        
        x_min, x_max = min(x_coords), max(x_coords)
        y_min, y_max = min(y_coords), max(y_coords)
        
        merged.append((x_min, y_min, x_max - x_min, y_max - y_min))
    
    return merged

def draw_player_boxes(image, boxes, color=(0, 255, 255), thickness=2):
    """
    이미지에 bounding box들을 그리기
    
    Args:
        image: 원본 이미지
        boxes: [(x, y, w, h), ...] 형태의 bounding box 리스트
        color: 박스 색상 (BGR)
        thickness: 선 두께
    
    Returns:
        result_image: 박스가 그려진 이미지
    """
    result = image.copy()
    
    for i, (x, y, w, h) in enumerate(boxes):
        # 박스 그리기
        cv2.rectangle(result, (x, y), (x + w, y + h), color, thickness)
        
        # 선수 번호 표시
        cv2.putText(result, f"Player {i+1}", (x, y-10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, thickness)
        
        # 박스 크기 정보 표시
        cv2.putText(result, f"{w}x{h}", (x, y+h+20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
    
    return result