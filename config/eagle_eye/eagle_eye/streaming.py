import cv2

def stream_camera(stream_url):
    cap = cv2.VideoCapture(stream_url)
    if not cap.isOpened():
        raise ValueError(f"Cannot open camera stream: {stream_url}")
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        yield frame
    cap.release()
