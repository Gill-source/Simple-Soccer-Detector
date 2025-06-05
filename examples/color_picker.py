import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import cv2

def get_dominant_colors(image, mask, n_colors=3):
    """numpy만 사용하여 dominant 색상 추출"""
    # 마스크 영역의 픽셀만 추출
    masked_pixels = image[mask == 255]
    
    if len(masked_pixels) == 0:
        return []
    
    # 색상 공간을 8단계로 줄여서 계산 속도 향상
    reduced_pixels = (masked_pixels // 32) * 32
    
    # 고유한 색상과 빈도 계산
    unique_colors, counts = np.unique(reduced_pixels.reshape(-1, 3), 
                                     axis=0, return_counts=True)
    
    # 빈도 순으로 정렬
    sorted_indices = np.argsort(counts)[::-1]
    
    result = []
    total_pixels = len(masked_pixels)
    
    for i in range(min(n_colors, len(unique_colors))):
        idx = sorted_indices[i]
        color_bgr = unique_colors[idx]
        color_rgb = color_bgr[::-1]  # BGR to RGB
        percentage = counts[idx] / total_pixels
        
        result.append({
            'color_bgr': tuple(color_bgr),
            'color_rgb': tuple(color_rgb),
            'percentage': percentage
        })
    
    return result

def create_color_bar_numpy(color_info, width=400, height=100):
    """numpy만 사용하여 색상 막대 생성"""
    if not color_info:
        return np.zeros((height, width, 3), dtype=np.uint8)
    
    color_bar = np.zeros((height, width, 3), dtype=np.uint8)
    start_x = 0
    
    for info in color_info:
        end_x = start_x + int(info['percentage'] * width)
        color_rgb = info['color_rgb']
        color_bar[:, start_x:end_x, :] = color_rgb
        start_x = end_x
    
    return color_bar

class RealTimeColorDisplay:
    def __init__(self):
        plt.ion()  # 인터랙티브 모드 활성화
        self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(10, 6))
        
        # 색상 막대 표시용
        self.ax1.set_title('Top 3 Dominant Colors')
        self.ax1.set_xlim(0, 400)
        self.ax1.set_ylim(0, 100)
        self.ax1.axis('off')
        
        # 색상 정보 텍스트 표시용
        self.ax2.set_xlim(0, 1)
        self.ax2.set_ylim(0, 1)
        self.ax2.axis('off')
        
    def update_display(self, color_info):
        # 이전 플롯 지우기
        self.ax1.clear()
        self.ax2.clear()
        
        # 축 설정 재적용
        self.ax1.set_title('Top 3 Dominant Colors (Real-time)')
        self.ax1.set_xlim(0, 400)
        self.ax1.set_ylim(0, 100)
        self.ax1.axis('off')
        
        self.ax2.set_xlim(0, 1)
        self.ax2.set_ylim(0, 1)
        self.ax2.axis('off')
        
        if color_info:
            # 색상 막대 생성
            color_bar = create_color_bar_numpy(color_info)
            
            # matplotlib에서 표시 (RGB 형태로 변환)
            color_bar_rgb = color_bar / 255.0  # 0-1 범위로 정규화
            self.ax1.imshow(color_bar_rgb, aspect='auto', extent=[0, 400, 0, 100])
            
            # 색상 정보 텍스트 표시
            text_info = ""
            for i, info in enumerate(color_info):
                rgb = info['color_rgb']
                percentage = info['percentage']
                text_info += f"Color {i+1}: RGB{rgb} - {percentage:.1%}\n"
            
            self.ax2.text(0.05, 0.8, text_info, fontsize=12, 
                         verticalalignment='top', fontfamily='monospace')
        
        # 화면 업데이트
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

# 실시간 비디오 처리에 통합하는 방법
def process_video_with_realtime_colors(video_path):
    import cv2  # 비디오 처리용
    
    cap = cv2.VideoCapture(video_path)
    color_display = RealTimeColorDisplay()
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        frame = cv2.resize(frame, (640, 360))
        
        # 여기에 기존의 마스크 생성 로직 추가
        # 예시로 간단한 마스크 생성
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        lower_bound = np.array([0, 50, 50])
        upper_bound = np.array([180, 255, 255])
        mask = cv2.inRange(hsv, lower_bound, upper_bound)
        
        # Top 3 dominant colors 추출
        dominant_colors = get_dominant_colors(frame, mask, n_colors=3)
        
        # 실시간 색상 display 업데이트
        color_display.update_display(dominant_colors)
        
        # OpenCV 창에도 결과 표시
        cv2.imshow('Original', frame)
        cv2.imshow('Mask', mask)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    plt.close('all')

# 기존 코드에 통합하는 간단한 방법
def integrate_realtime_colors(frame, combined_mask, color_display):
    """
    기존 process_video 함수에 추가할 수 있는 함수.
    get_dominant_colors가 {'color_rgb': (R, G, B), 'percentage': ...} 형태로 반환한다고 가정.
    """
    
    # Top 3 dominant colors 추출
    dominant_colors = get_dominant_colors(frame, combined_mask, n_colors=3)
    
    # 실시간 display 업데이트
    color_display.update_display(dominant_colors)
    
    # 콘솔에도 출력 (RGB 기준)
    if dominant_colors:
        print("Top 3 Colors (RGB):")
        for i, color in enumerate(dominant_colors):
            rgb = color['color_rgb']
            print(f"  {i+1}. RGB{rgb} - {color['percentage']:.1%}")
    
    # dominant_colors가 비어있으면 None 반환
    if not dominant_colors:
        return None
    
    # 가장 우세한 색상을 찾아서 BGR 형식으로 변환하여 반환
    # - 'color_rgb'가 (R, G, B) 형태라고 가정
    # - OpenCV는 (B, G, R) 순서를 사용하므로 순서만 뒤집어 줌
    dominant_colors.sort(key=lambda x: x['percentage'], reverse=True)
    top_bgr = dominant_colors[0]['color_bgr']  # 예: (R, G, B)

    # HSV로 변환
    top_bgr_np = np.uint8([[list(top_bgr)]])  # 1x1 이미지로 변환
    top_hsv_np = cv2.cvtColor(top_bgr_np, cv2.COLOR_BGR2HSV)
    top_hsv = tuple(int(c) for c in top_hsv_np[0, 0])
    
    
    return top_hsv


# 사용 예제
if __name__ == "__main__":
    # 실시간 색상 display 객체 생성
    color_display = RealTimeColorDisplay()
    
    # 기존 process_video 함수에서 다음과 같이 사용:
    # dominant_colors = integrate_realtime_colors(frame, combined_mask, color_display)
