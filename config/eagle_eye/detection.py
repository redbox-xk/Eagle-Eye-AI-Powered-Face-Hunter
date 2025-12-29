from mtcnn import MTCNN
import cv2

detector = MTCNN()

def detect_faces(image_path):
    image = cv2.imread(image_path)
    result = detector.detect_faces(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    return result
