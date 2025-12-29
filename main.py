from eagle_eye.detection import detect_faces
from eagle_eye.recognition import recognize_faces
from eagle_eye.database import init_db, save_observation
from eagle_eye.alerts import send_alert
from eagle_eye.streaming import stream_camera
import yaml

def load_config(path="config/cameras.yaml"):
    with open(path, "r") as f:
        return yaml.safe_load(f)

def main():
    init_db()
    config = load_config()
    for camera in config.get("cameras", []):
        print(f"Streaming from camera: {camera['name']}")
        for frame in stream_camera(camera["stream_url"]):
            faces = detect_faces(frame)
            recognized = recognize_faces(faces)
            for face_data in recognized:
                identity = face_data["identity"]
                save_observation(camera["name"], str(face_data["face"]), identity)
                send_alert(identity, camera["name"])

if __name__ == "__main__":
    main()
