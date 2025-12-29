from eagle_eye.detection import detect_faces
from eagle_eye.recognition import recognize_faces
import yaml

def load_config(path="config/cameras.yaml"):
    with open(path, "r") as f:
        return yaml.safe_load(f)

def main():
    config = load_config()
    print("Eagle Eye initialized with cameras:", config.get("cameras", []))
    
    # Example flow
    image_path = "data/sample_images/sample1.jpg"
    faces = detect_faces(image_path)
    recognized = recognize_faces(faces)
    print("Recognition results:", recognized)

if __name__ == "__main__":
    main()
