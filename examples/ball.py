import cv2
import numpy as np


def detect_ball(frame):
    """
    1) Canny로 에지 검출
    2) 컨투어별 원형도 계산 → 가장 둥근 후보 찾기
    3) 후보 영역 평균 HSV 확인 → 흰색 기준 통과 시 리턴
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    # 1) 에지 검출
    edges = cv2.Canny(gray, 50, 150)
    # 모폴로지로 끊긴 에지 연결 (선택)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5,5))
    edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel, iterations=1)

    # 2) 컨투어별 원형도 계산
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    best = None
    best_circ = 0.0
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < 50 or area > 2000:  # 공 크기 범위 필터
            continue
        perim = cv2.arcLength(cnt, True)
        if perim <= 0:
            continue
        circ = 4 * np.pi * area / (perim * perim)
        # circularity가 1에 가까울수록 원형
        if circ > best_circ:
            best_circ = circ
            best = cnt

    # 3) 최종 후보의 색상 확인
    if best is not None and best_circ > 0.6:
        x,y,w,h = cv2.boundingRect(best)
        # 후보 영역 HSV 평균
        roi_hsv = cv2.cvtColor(frame[y:y+h, x:x+w], cv2.COLOR_BGR2HSV)
        mean_s = roi_hsv[:,:,1].mean()
        mean_v = roi_hsv[:,:,2].mean()
        # 흰색 기준: 채도 낮고 명도 높아야 함
        if mean_s < 30 and mean_v > 200:
            return edges
        #[(x, y, w, h)], edges

    return edges
    #[], edges