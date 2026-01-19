# ⚽ SimpleSoccerDetector  
### OpenCV-based Real-time Soccer Object Detection & Tracking System (No Deep Learning)

딥러닝 없이 **전통적인 OpenCV 기반 영상처리 기법만을 활용하여**  
축구 경기 영상에서 **선수와 공을 실시간으로 탐지 및 추적**하는 경량화 시스템입니다.  
GPU 없이도 높은 FPS와 정확도를 달성하는 것을 목표로 설계되었습니다.

---

## 📌 Key Features

- 🧠 **No Deep Learning**  
  - TensorFlow / PyTorch 미사용  
  - 규칙 기반 전통 Computer Vision 파이프라인

- ⚡ **Real-time Performance**
  - 평균 **51 FPS (Full Pipeline)**
  - CPU-only 환경에서 실시간 처리 가능

- 🪶 **Lightweight & Efficient**
  - 메모리 사용량 약 **173 MB**
  - CPU 점유율 약 **11%**

- 🎯 **High Accuracy**
  - Precision **95%**
  - Recall **96%**

- 🧩 **Modular Architecture**
  - Detection / Tracking / Visualization 분리 설계

---

## 🧠 System Overview

본 시스템은 다음 **5개의 모듈**로 구성됩니다.

1. **Input & Preprocessing**
   - 영상 입력 및 해상도 표준화 (640×360)
   - 실시간 잔디 색상 추출

2. **Color & Grass Masking**
   - HSV/BGR 기반 잔디 제거
   - 팀별 유니폼 색상 마스킹
   - Morphological 연산으로 노이즈 제거

3. **Object Detection**
   - Player Detection: Contour 기반 바운딩 박스 추출
   - Ball Detection: Canny Edge + Blob Detector 활용

4. **Tracking**
   - Histogram 기반 Player Tracking
   - 공 속도 예측 및 플레이어 점유 판별
   - 객체 유실 및 충돌 관리

5. **Visualization & Output**
   - Bounding Box 및 Label 시각화
   - 실시간 OpenCV GUI 출력
   - 콘솔 기반 상태 로그 출력

---
### 🎯 Result
데모영상: https://www.youtube.com/watch?v=JhD-FGbmyys
Player Deetection & Team Classification
<img width="1580" height="1012" alt="KakaoTalk_20250616_133406284_04" src="https://github.com/user-attachments/assets/91124f5a-ab77-4207-9244-76dcf73bef3d" />
데모영상: https://www.youtube.com/watch?v=JhD-FGbmyys
