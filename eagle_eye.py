#!/usr/bin/env python3
"""
\033[1;33m
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║  ███████╗ █████╗  ██████╗ ██╗     ███████╗    ███████╗██╗   ██╗███████╗  ║
║  ██╔════╝██╔══██╗██╔════╝ ██║     ██╔════╝    ██╔════╝╚██╗ ██╔╝██╔════╝  ║
║  █████╗  ███████║██║  ███╗██║     █████╗      █████╗   ╚████╔╝ █████╗    ║
║  ██╔══╝  ██╔══██║██║   ██║██║     ██╔══╝      ██╔══╝    ╚██╔╝  ██╔══╝    ║
║  ███████╗██║  ██║╚██████╔╝███████╗███████╗    ██║        ██║   ███████╗  ║
║  ╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚══════╝    ╚═╝        ╚═╝   ╚══════╝  ║
║                                                               ║
║        AI-POWERED FACE HUNTER - MANUAL SEARCH MODE           ║
║           Upload Image → Find Face → Get Location            ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
\033[0m\033[1;37m
"""

import os
import sys
import cv2
import numpy as np
import torch
import faiss
import hashlib
import json
import time
import sqlite3
import base64
import threading
import queue
import asyncio
import aiohttp
from datetime import datetime
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, asdict
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# GOLDEN COLOR SCHEME
# ============================================================================

class Colors:
    GOLD = '\033[1;33m'
    BOLD_GOLD = '\033[1;38;5;220m'
    WHITE = '\033[1;37m'
    BRIGHT_WHITE = '\033[1;38;5;255m'
    RED = '\033[1;31m'
    GREEN = '\033[1;32m'
    CYAN = '\033[1;36m'
    BLUE = '\033[1;34m'
    MAGENTA = '\033[1;35m'
    RESET = '\033[0m'
    
    @staticmethod
    def print_gold(text: str):
        print(f"{Colors.GOLD}{text}{Colors.RESET}")
    
    @staticmethod
    def print_white(text: str):
        print(f"{Colors.WHITE}{text}{Colors.RESET}")
    
    @staticmethod
    def print_alert(text: str):
        print(f"{Colors.RED}🚨 {text}{Colors.RESET}")
    
    @staticmethod
    def print_success(text: str):
        print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")
    
    @staticmethod
    def print_info(text: str):
        print(f"{Colors.CYAN}ℹ {text}{Colors.RESET}")

# ============================================================================
# FACE HUNTER ENGINE
# ============================================================================

class FaceHunter:
    """AI-powered face hunting engine with real-time CCTV scanning"""
    
    def __init__(self):
        self.device = self._get_device()
        self.face_detector = self._init_detector()
        self.face_recognizer = self._init_recognizer()
        self.camera_network = CameraNetwork()
        self.results_db = self._init_database()
        self.search_queue = queue.Queue()
        self.is_searching = False
        self.current_search_id = None
        
    def _get_device(self) -> str:
        """Get best available device"""
        if torch.cuda.is_available():
            return "cuda"
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            return "mps"
        return "cpu"
    
    def _init_detector(self):
        """Initialize face detector"""
        try:
            # Try YOLO for best accuracy
            from ultralytics import YOLO
            return YOLO('yolov8n-face.pt')  # Face detection model
        except:
            try:
                # Try MTCNN
                from mtcnn import MTCNN
                return MTCNN()
            except:
                # Use OpenCV Haar Cascade
                cascade = cv2.CascadeClassifier(
                    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
                )
                return cascade
    
    def _init_recognizer(self):
        """Initialize face recognizer"""
        try:
            from insightface.app import FaceAnalysis
            app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
            app.prepare(ctx_id=0, det_size=(640, 640))
            return app
        except:
            # Fallback to OpenCV LBPH
            recognizer = cv2.face.LBPHFaceRecognizer_create()
            return recognizer
    
    def _init_database(self) -> sqlite3.Connection:
        """Initialize results database"""
        conn = sqlite3.connect('face_hunt_results.db', check_same_thread=False)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS searches (
                search_id TEXT PRIMARY KEY,
                query_image_path TEXT,
                query_embedding BLOB,
                timestamp REAL,
                search_radius_km INTEGER,
                max_results INTEGER,
                status TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS matches (
                match_id TEXT PRIMARY KEY,
                search_id TEXT,
                camera_id TEXT,
                camera_name TEXT,
                latitude REAL,
                longitude REAL,
                similarity_score REAL,
                timestamp REAL,
                frame_path TEXT,
                alert_sent INTEGER DEFAULT 0,
                metadata TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cameras (
                camera_id TEXT PRIMARY KEY,
                name TEXT,
                url TEXT,
                latitude REAL,
                longitude REAL,
                city TEXT,
                country TEXT,
                is_active INTEGER DEFAULT 1,
                last_checked REAL
            )
        ''')
        
        conn.commit()
        return conn
    
    def load_query_image(self, image_path: str) -> Optional[np.ndarray]:
        """Load query image and detect face"""
        if not os.path.exists(image_path):
            Colors.print_alert(f"Image not found: {image_path}")
            return None
        
        Colors.print_info(f"Loading query image: {image_path}")
        img = cv2.imread(image_path)
        if img is None:
            Colors.print_alert("Failed to load image")
            return None
        
        # Detect face
        face_img = self.detect_single_face(img)
        if face_img is None:
            Colors.print_alert("No face detected in query image")
            return None
        
        Colors.print_success("Face detected in query image")
        return face_img
    
    def detect_single_face(self, image: np.ndarray) -> Optional[np.ndarray]:
        """Detect the largest face in image"""
        faces = self.detect_faces(image)
        if not faces:
            return None
        
        # Get largest face by bounding box area
        largest_face = max(faces, key=lambda f: (f[2]-f[0])*(f[3]-f[1]))
        x1, y1, x2, y2 = largest_face
        face_img = image[y1:y2, x1:x2]
        
        # Resize to standard size
        face_img = cv2.resize(face_img, (112, 112))
        return face_img
    
    def detect_faces(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """Detect all faces in image"""
        faces = []
        
        if isinstance(self.face_detector, type(YOLO)) if 'YOLO' in globals() else False:
            # YOLO detection
            results = self.face_detector(image, conf=0.5)
            for result in results:
                boxes = result.boxes
                if boxes:
                    for box in boxes:
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        faces.append((x1, y1, x2, y2))
        
        elif isinstance(self.face_detector, type(MTCNN)) if 'MTCNN' in globals() else False:
            # MTCNN detection
            results = self.face_detector.detect_faces(image)
            for res in results:
                if res['confidence'] > 0.9:
                    x1, y1, w, h = res['box']
                    x2, y2 = x1 + w, y1 + h
                    faces.append((x1, y1, x2, y2))
        
        else:
            # OpenCV Haar Cascade
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            face_rects = self.face_detector.detectMultiScale(gray, 1.1, 5)
            for (x, y, w, h) in face_rects:
                faces.append((x, y, x + w, y + h))
        
        return faces
    
    def extract_embedding(self, face_image: np.ndarray) -> np.ndarray:
        """Extract face embedding"""
        try:
            if hasattr(self.face_recognizer, 'get'):
                # InsightFace
                faces = self.face_recognizer.get(face_image)
                if faces:
                    return faces[0].embedding
            
            # Fallback: Generate embedding from face features
            # Convert to grayscale and resize
            gray = cv2.cvtColor(face_image, cv2.COLOR_BGR2GRAY)
            gray = cv2.resize(gray, (128, 128))
            
            # Apply histogram equalization
            gray = cv2.equalizeHist(gray)
            
            # Flatten and normalize
            embedding = gray.flatten().astype(np.float32)
            embedding = embedding / np.linalg.norm(embedding)
            
            # Pad or truncate to 512 dimensions
            if len(embedding) > 512:
                step = len(embedding) // 512
                embedding = embedding[::step][:512]
            elif len(embedding) < 512:
                padding = 512 - len(embedding)
                embedding = np.pad(embedding, (0, padding), 'constant')
            
            return embedding
            
        except Exception as e:
            Colors.print_alert(f"Embedding extraction failed: {e}")
            # Return random embedding as last resort
            return np.random.randn(512).astype(np.float32)
    
    def search_camera(self, camera_url: str, query_embedding: np.ndarray, 
                     search_id: str, camera_info: Dict) -> List[Dict]:
        """Search for face in a single camera"""
        matches = []
        
        try:
            Colors.print_info(f"Searching camera: {camera_info.get('name', 'Unknown')}")
            
            cap = cv2.VideoCapture(camera_url)
            if not cap.isOpened():
                Colors.print_alert(f"Failed to open camera: {camera_url}")
                return matches
            
            frame_count = 0
            max_frames = 300  # Limit frames per camera
            start_time = time.time()
            
            while frame_count < max_frames:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Process every 10th frame for speed
                if frame_count % 10 == 0:
                    # Detect faces
                    face_boxes = self.detect_faces(frame)
                    
                    for box in face_boxes:
                        x1, y1, x2, y2 = box
                        face_img = frame[y1:y2, x1:x2]
                        
                        try:
                            # Extract embedding from detected face
                            face_embedding = self.extract_embedding(face_img)
                            
                            # Calculate similarity
                            similarity = self.calculate_similarity(query_embedding, face_embedding)
                            
                            if similarity > 0.75:  # Match threshold
                                match_data = {
                                    'search_id': search_id,
                                    'camera_id': camera_info['id'],
                                    'camera_name': camera_info['name'],
                                    'latitude': camera_info['latitude'],
                                    'longitude': camera_info['longitude'],
                                    'similarity_score': similarity,
                                    'timestamp': time.time(),
                                    'frame': frame.copy(),
                                    'bounding_box': box,
                                    'frame_count': frame_count
                                }
                                matches.append(match_data)
                                
                                Colors.print_alert(f"MATCH FOUND! Similarity: {similarity:.2%}")
                                Colors.print_info(f"  Location: {camera_info['name']}")
                                Colors.print_info(f"  Coordinates: {camera_info['latitude']:.4f}, {camera_info['longitude']:.4f}")
                                
                                # Save match frame
                                self.save_match_frame(match_data, search_id)
                        
                        except Exception as e:
                            continue
                
                frame_count += 1
                
                # Timeout after 30 seconds per camera
                if time.time() - start_time > 30:
                    break
            
            cap.release()
            
        except Exception as e:
            Colors.print_alert(f"Camera search error: {e}")
        
        return matches
    
    def calculate_similarity(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        """Calculate cosine similarity between embeddings"""
        # Normalize embeddings
        emb1_norm = emb1 / np.linalg.norm(emb1)
        emb2_norm = emb2 / np.linalg.norm(emb2)
        
        # Cosine similarity
        similarity = np.dot(emb1_norm, emb2_norm)
        
        # Apply sigmoid for better distribution
        similarity = 1 / (1 + np.exp(-10 * (similarity - 0.5)))
        
        return float(similarity)
    
    def save_match_frame(self, match_data: Dict, search_id: str):
        """Save match frame to disk"""
        try:
            # Create directory for search
            search_dir = f"search_results/{search_id}"
            os.makedirs(search_dir, exist_ok=True)
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = f"{search_dir}/match_{timestamp}.jpg"
            
            # Draw bounding box on frame
            frame = match_data['frame']
            x1, y1, x2, y2 = match_data['bounding_box']
            
            # Draw rectangle
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 3)
            
            # Add text
            text = f"Match: {match_data['similarity_score']:.2%}"
            cv2.putText(frame, text, (x1, y1 - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
            
            # Save frame
            cv2.imwrite(filename, frame)
            
            # Update match data with frame path
            match_data['frame_path'] = filename
            
        except Exception as e:
            Colors.print_alert(f"Failed to save match frame: {e}")
    
    def save_match_to_db(self, match_data: Dict):
        """Save match to database"""
        try:
            cursor = self.results_db.cursor()
            
            metadata = {
                'bounding_box': match_data['bounding_box'],
                'frame_count': match_data.get('frame_count', 0),
                'saved_frame_path': match_data.get('frame_path', '')
            }
            
            cursor.execute('''
                INSERT INTO matches 
                (match_id, search_id, camera_id, camera_name, latitude, 
                 longitude, similarity_score, timestamp, frame_path, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                hashlib.md5(f"{match_data['search_id']}_{time.time()}".encode()).hexdigest(),
                match_data['search_id'],
                match_data['camera_id'],
                match_data['camera_name'],
                match_data['latitude'],
                match_data['longitude'],
                match_data['similarity_score'],
                match_data['timestamp'],
                match_data.get('frame_path', ''),
                json.dumps(metadata)
            ))
            
            self.results_db.commit()
            
        except Exception as e:
            Colors.print_alert(f"Failed to save match to DB: {e}")
    
    def generate_search_report(self, search_id: str) -> Dict:
        """Generate search report"""
        cursor = self.results_db.cursor()
        
        # Get search info
        cursor.execute('SELECT * FROM searches WHERE search_id = ?', (search_id,))
        search_info = cursor.fetchone()
        
        # Get matches
        cursor.execute('SELECT * FROM matches WHERE search_id = ? ORDER BY similarity_score DESC', 
                      (search_id,))
        matches = cursor.fetchall()
        
        report = {
            'search_id': search_id,
            'timestamp': search_info[3] if search_info else time.time(),
            'total_matches': len(matches),
            'matches': []
        }
        
        for match in matches:
            match_data = {
                'camera': match[3],
                'location': {
                    'latitude': match[4],
                    'longitude': match[5]
                },
                'similarity': match[6],
                'time': datetime.fromtimestamp(match[7]).strftime('%Y-%m-%d %H:%M:%S'),
                'frame_path': match[8]
            }
            report['matches'].append(match_data)
        
        return report
    
    def show_map(self, matches: List[Dict]):
        """Generate HTML map with match locations"""
        try:
            import folium
            
            # Create map centered on average location
            if matches:
                avg_lat = np.mean([m['latitude'] for m in matches])
                avg_lng = np.mean([m['longitude'] for m in matches])
            else:
                avg_lat, avg_lng = 0, 0
            
            m = folium.Map(location=[avg_lat, avg_lng], zoom_start=10)
            
            # Add markers for each match
            for match in matches:
                popup_html = f"""
                <b>{match['camera_name']}</b><br>
                Similarity: {match['similarity_score']:.2%}<br>
                Time: {datetime.fromtimestamp(match['timestamp']).strftime('%H:%M:%S')}
                """
                
                folium.Marker(
                    location=[match['latitude'], match['longitude']],
                    popup=popup_html,
                    icon=folium.Icon(color='red', icon='user', prefix='fa')
                ).add_to(m)
            
            # Save map
            map_file = f"search_results/{self.current_search_id}/map.html"
            m.save(map_file)
            
            Colors.print_success(f"Interactive map saved: {map_file}")
            Colors.print_info("Open the HTML file in browser to view locations")
            
        except ImportError:
            Colors.print_alert("Folium not installed. Install with: pip install folium")
            
            # Create simple text map
            Colors.print_gold("\n📍 MATCH LOCATIONS:")
            for match in matches:
                print(f"  • {match['camera_name']}")
                print(f"    Coordinates: {match['latitude']:.4f}, {match['longitude']:.4f}")
                print(f"    Similarity: {match['similarity_score']:.2%}")
                print()

# ============================================================================
# CAMERA NETWORK MANAGER
# ============================================================================

class CameraNetwork:
    """Manage network of CCTV cameras"""
    
    def __init__(self):
        self.cameras = []
        self.load_cameras()
    
    def load_cameras(self):
        """Load camera database"""
        # Sample cameras - in real system, these would be from database or API
        self.cameras = [
            {
                'id': 'nyc_traffic_1',
                'name': 'NYC Times Square Traffic',
                'url': 'http://207.251.86.238/cctv265.jpg',  # NYC Traffic Camera
                'latitude': 40.7580,
                'longitude': -73.9855,
                'city': 'New York',
                'country': 'USA'
            },
            {
                'id': 'london_traffic_1',
                'name': 'London Parliament',
                'url': 'https://s3.eu-west-2.amazonaws.com/live.camsecure.co.uk/HouseOfParliament/HouseOfParliament.stream/playlist.m3u8',
                'latitude': 51.4993,
                'longitude': -0.1246,
                'city': 'London',
                'country': 'UK'
            },
            {
                'id': 'tokyo_street_1',
                'name': 'Tokyo Shibuya Crossing',
                'url': 'https://www.youtube.com/watch?v=YOUR_YOUTUBE_LIVE_ID',  # Would need actual stream
                'latitude': 35.6595,
                'longitude': 139.7004,
                'city': 'Tokyo',
                'country': 'Japan'
            }
        ]
        
        # Try to load from database
        try:
            conn = sqlite3.connect('face_hunt_results.db', check_same_thread=False)
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM cameras WHERE is_active = 1')
            
            for row in cursor.fetchall():
                self.cameras.append({
                    'id': row[0],
                    'name': row[1],
                    'url': row[2],
                    'latitude': row[3],
                    'longitude': row[4],
                    'city': row[5],
                    'country': row[6]
                })
            
            conn.close()
        except:
            pass
    
    def get_cameras_in_area(self, center_lat: float, center_lng: float, 
                           radius_km: float = 100) -> List[Dict]:
        """Get cameras within specified area"""
        cameras_in_area = []
        
        for cam in self.cameras:
            distance = self.calculate_distance(
                center_lat, center_lng, cam['latitude'], cam['longitude']
            )
            
            if distance <= radius_km:
                cameras_in_area.append(cam)
        
        return cameras_in_area
    
    def calculate_distance(self, lat1: float, lng1: float, 
                          lat2: float, lng2: float) -> float:
        """Calculate distance between two coordinates in km"""
        from math import radians, sin, cos, sqrt, atan2
        
        # Convert to radians
        lat1, lng1, lat2, lng2 = map(radians, [lat1, lng1, lat2, lng2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlng = lng2 - lng1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlng/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        radius_earth = 6371  # Earth's radius in km
        return radius_earth * c
    
    def discover_public_cameras(self, country: str = None) -> List[Dict]:
        """Discover public CCTV cameras"""
        discovered = []
        
        # Common public camera sources
        public_sources = [
            'https://www.insecam.org',
            'https://www.webcamtaxi.com',
            'https://www.earthcam.com'
        ]
        
        Colors.print_info("Searching for public cameras...")
        
        # In a real system, this would scrape websites or use APIs
        # For demo, add some example cameras
        discovered.extend([
            {
                'id': 'public_1',
                'name': 'Moscow Red Square',
                'url': 'http://webcam.moscow/russia/red-square',
                'latitude': 55.7539,
                'longitude': 37.6208,
                'city': 'Moscow',
                'country': 'Russia'
            },
            {
                'id': 'public_2',
                'name': 'Paris Eiffel Tower',
                'url': 'https://www.earthcam.com/world/france/paris/?cam=tour-eiffel',
                'latitude': 48.8584,
                'longitude': 2.2945,
                'city': 'Paris',
                'country': 'France'
            }
        ])
        
        return discovered

# ============================================================================
# ALERT SYSTEM
# ============================================================================

class AlertSystem:
    """Real-time alert system for face matches"""
    
    def __init__(self):
        self.alerts_sent = []
    
    def send_alert(self, match_data: Dict):
        """Send alert for face match"""
        Colors.print_alert("\n" + "="*60)
        Colors.print_alert("🚨 FACE MATCH ALERT! 🚨")
        Colors.print_alert("="*60)
        
        # Build alert message
        alert_msg = f"""
📍 LOCATION FOUND:
   Camera: {match_data['camera_name']}
   Coordinates: {match_data['latitude']:.4f}, {match_data['longitude']:.4f}
   Similarity: {match_data['similarity_score']:.2%}
   Time: {datetime.fromtimestamp(match_data['timestamp']).strftime('%Y-%m-%d %H:%M:%S')}

🗺️ GEO-LOCATION:
   https://maps.google.com/?q={match_data['latitude']},{match_data['longitude']}

📸 Evidence saved to: {match_data.get('frame_path', 'N/A')}
        """
        
        print(alert_msg)
        
        # Save alert to file
        self.save_alert_to_file(match_data)
        
        # Send email alert (if configured)
        self.send_email_alert(match_data)
        
        # Play alert sound
        self.play_alert_sound()
        
        self.alerts_sent.append(match_data)
    
    def save_alert_to_file(self, match_data: Dict):
        """Save alert to JSON file"""
        try:
            alerts_dir = "alerts"
            os.makedirs(alerts_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            alert_file = f"{alerts_dir}/alert_{timestamp}.json"
            
            alert_data = {
                'timestamp': time.time(),
                'match_data': match_data,
                'alert_type': 'face_match',
                'severity': 'high'
            }
            
            with open(alert_file, 'w') as f:
                json.dump(alert_data, f, indent=2)
            
            Colors.print_success(f"Alert saved: {alert_file}")
            
        except Exception as e:
            Colors.print_alert(f"Failed to save alert: {e}")
    
    def send_email_alert(self, match_data: Dict):
        """Send email alert"""
        # This would require email configuration
        # For now, just print message
        Colors.print_info("Email alert would be sent here")
    
    def play_alert_sound(self):
        """Play alert sound"""
        try:
            import platform
            if platform.system() == 'Darwin':  # macOS
                os.system('afplay /System/Library/Sounds/Glass.aiff')
            elif platform.system() == 'Windows':
                import winsound
                winsound.Beep(1000, 1000)
            else:  # Linux
                os.system('paplay /usr/share/sounds/freedesktop/stereo/complete.oga')
        except:
            pass

# ============================================================================
# MAIN SEARCH INTERFACE
# ============================================================================

class ManualFaceSearch:
    """Manual face search interface with AI-powered hunting"""
    
    def __init__(self):
        self.hunter = FaceHunter()
        self.alert_system = AlertSystem()
        self.current_search = None
        
        Colors.print_gold("\n" + "═"*60)
        Colors.print_gold("        EAGLE EYE - AI FACE HUNTER")
        Colors.print_gold("        Upload → Search → Locate")
        Colors.print_gold("═"*60)
        print()
    
    def start_search(self):
        """Start manual face search"""
        Colors.print_white("📁 STEP 1: Upload Face Image")
        print("-"*40)
        
        # Get image path
        image_path = input(f"{Colors.CYAN}Enter image path: {Colors.RESET}").strip()
        
        if not os.path.exists(image_path):
            Colors.print_alert("File does not exist!")
            return
        
        # Load and process image
        face_img = self.hunter.load_query_image(image_path)
        if face_img is None:
            return
        
        # Extract embedding
        Colors.print_info("Extracting face embedding...")
        query_embedding = self.hunter.extract_embedding(face_img)
        Colors.print_success(f"Embedding extracted: {len(query_embedding)} dimensions")
        
        # Search parameters
        Colors.print_white("\n🎯 STEP 2: Set Search Parameters")
        print("-"*40)
        
        try:
            radius = float(input(f"{Colors.CYAN}Search radius (km) [100]: {Colors.RESET}") or "100")
            max_cameras = int(input(f"{Colors.CYAN}Max cameras to scan [10]: {Colors.RESET}") or "10")
            similarity_threshold = float(input(f"{Colors.CYAN}Similarity threshold (0.7-0.95) [0.75]: {Colors.RESET}") or "0.75")
        except:
            Colors.print_alert("Invalid input! Using defaults.")
            radius, max_cameras, similarity_threshold = 100, 10, 0.75
        
        # Location filter
        use_location = input(f"{Colors.CYAN}Filter by location? (y/n) [n]: {Colors.RESET}").lower() == 'y'
        
        center_lat, center_lng = 0, 0
        if use_location:
            try:
                center_lat = float(input(f"{Colors.CYAN}Center latitude: {Colors.RESET}"))
                center_lng = float(input(f"{Colors.CYAN}Center longitude: {Colors.RESET}"))
            except:
                Colors.print_alert("Invalid coordinates! Searching globally.")
                use_location = False
        
        # Start search
        Colors.print_white("\n🔍 STEP 3: Start Face Hunt")
        print("-"*40)
        
        search_id = hashlib.md5(f"{image_path}_{time.time()}".encode()).hexdigest()[:16]
        self.hunter.current_search_id = search_id
        
        Colors.print_info(f"Search ID: {search_id}")
        Colors.print_info(f"Scanning up to {max_cameras} cameras...")
        Colors.print_info("Press Ctrl+C to stop search\n")
        
        # Get cameras to scan
        if use_location:
            cameras = self.hunter.camera_network.get_cameras_in_area(
                center_lat, center_lng, radius
            )
        else:
            cameras = self.hunter.camera_network.cameras
        
        cameras = cameras[:max_cameras]
        
        if not cameras:
            Colors.print_alert("No cameras found in search area!")
            return
        
        Colors.print_info(f"Found {len(cameras)} cameras to scan")
        
        # Start scanning
        all_matches = []
        start_time = time.time()
        
        try:
            # Use ThreadPool for concurrent scanning
            from concurrent.futures import ThreadPoolExecutor, as_completed
            
            with ThreadPoolExecutor(max_workers=5) as executor:
                future_to_camera = {
                    executor.submit(
                        self.hunter.search_camera,
                        cam['url'],
                        query_embedding,
                        search_id,
                        cam
                    ): cam for cam in cameras
                }
                
                for future in as_completed(future_to_camera):
                    cam = future_to_camera[future]
                    try:
                        matches = future.result(timeout=45)
                        if matches:
                            Colors.print_alert(f"Found {len(matches)} matches in {cam['name']}")
                            all_matches.extend(matches)
                            
                            # Send alerts and save matches
                            for match in matches:
                                self.alert_system.send_alert(match)
                                self.hunter.save_match_to_db(match)
                    
                    except Exception as e:
                        Colors.print_alert(f"Camera {cam['name']} failed: {e}")
                    
                    # Check for interrupt
                    if not self.check_continue():
                        break
        
        except KeyboardInterrupt:
            Colors.print_info("\nSearch interrupted by user")
        
        search_time = time.time() - start_time
        
        # Generate report
        Colors.print_white("\n📊 STEP 4: Search Results")
        print("-"*40)
        
        if all_matches:
            Colors.print_success(f"✅ FOUND {len(all_matches)} MATCHES!")
            Colors.print_info(f"Search time: {search_time:.1f} seconds")
            
            # Show matches
            for i, match in enumerate(all_matches[:10]):  # Show first 10
                Colors.print_gold(f"\nMatch {i+1}:")
                Colors.print_white(f"  Camera: {match['camera_name']}")
                Colors.print_white(f"  Location: {match['latitude']:.4f}, {match['longitude']:.4f}")
                Colors.print_white(f"  Similarity: {match['similarity_score']:.2%}")
                Colors.print_white(f"  Time: {datetime.fromtimestamp(match['timestamp']).strftime('%H:%M:%S')}")
            
            # Generate map
            if len(all_matches) > 0:
                Colors.print_info("\nGenerating location map...")
                self.hunter.show_map(all_matches)
            
            # Save report
            report = self.hunter.generate_search_report(search_id)
            report_file = f"search_results/{search_id}/report.json"
            
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            Colors.print_success(f"\nFull report saved: {report_file}")
            
        else:
            Colors.print_alert("❌ NO MATCHES FOUND")
            Colors.print_info("Try adjusting search parameters or use a different image")
        
        Colors.print_gold("\n" + "═"*60)
        Colors.print_gold("        SEARCH COMPLETE")
        Colors.print_gold("═"*60)
    
    def check_continue(self) -> bool:
        """Check if user wants to continue"""
        # Non-blocking check for keyboard interrupt
        # In a real GUI, this would be different
        return True
    
    def batch_search(self):
        """Search multiple images at once"""
        Colors.print_white("📁 BATCH SEARCH MODE")
        print("-"*40)
        
        folder = input(f"{Colors.CYAN}Enter folder with images: {Colors.RESET}").strip()
        
        if not os.path.exists(folder):
            Colors.print_alert("Folder does not exist!")
            return
        
        # Find images
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif']
        image_files = []
        
        for ext in image_extensions:
            image_files.extend([f for f in os.listdir(folder) if f.lower().endswith(ext)])
        
        if not image_files:
            Colors.print_alert("No images found in folder!")
            return
        
        Colors.print_info(f"Found {len(image_files)} images")
        
        for img_file in image_files[:5]:  # Limit to 5 images
            img_path = os.path.join(folder, img_file)
            Colors.print_gold(f"\nSearching: {img_file}")
            
            face_img = self.hunter.load_query_image(img_path)
            if face_img:
                self.start_search()
    
    def view_history(self):
        """View search history"""
        Colors.print_white("📜 SEARCH HISTORY")
        print("-"*40)
        
        try:
            conn = sqlite3.connect('face_hunt_results.db', check_same_thread=False)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM searches ORDER BY timestamp DESC LIMIT 10')
            searches = cursor.fetchall()
            
            if not searches:
                Colors.print_info("No search history found")
                return
            
            for search in searches:
                search_id, img_path, _, timestamp, radius, max_results, status = search
                
                # Count matches
                cursor.execute('SELECT COUNT(*) FROM matches WHERE search_id = ?', (search_id,))
                match_count = cursor.fetchone()[0]
                
                Colors.print_gold(f"\nSearch: {search_id}")
                Colors.print_white(f"  Image: {os.path.basename(img_path)}")
                Colors.print_white(f"  Time: {datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')}")
                Colors.print_white(f"  Radius: {radius}km, Cameras: {max_results}")
                Colors.print_white(f"  Matches: {match_count}")
                Colors.print_white(f"  Status: {status}")
            
            conn.close()
        
        except Exception as e:
            Colors.print_alert(f"Failed to load history: {e}")
    
    def camera_manager(self):
        """Camera management interface"""
        Colors.print_white("📡 CAMERA MANAGER")
        print("-"*40)
        
        Colors.print_white("1. View all cameras")
        Colors.print_white("2. Add camera manually")
        Colors.print_white("3. Discover public cameras")
        Colors.print_white("4. Test camera connection")
        Colors.print_white("5. Back to main menu")
        
        choice = input(f"\n{Colors.CYAN}Select option (1-5): {Colors.RESET}").strip()
        
        if choice == '1':
            self.view_cameras()
        elif choice == '2':
            self.add_camera()
        elif choice == '3':
            self.discover_cameras()
        elif choice == '4':
            self.test_camera()
    
    def view_cameras(self):
        """View all cameras"""
        cameras = self.hunter.camera_network.cameras
        
        Colors.print_info(f"Total cameras: {len(cameras)}")
        
        for i, cam in enumerate(cameras[:20]):  # Show first 20
            Colors.print_gold(f"\nCamera {i+1}: {cam['name']}")
            Colors.print_white(f"  URL: {cam['url'][:50]}...")
            Colors.print_white(f"  Location: {cam['city']}, {cam['country']}")
            Colors.print_white(f"  Coordinates: {cam['latitude']:.4f}, {cam['longitude']:.4f}")
    
    def add_camera(self):
        """Add camera manually"""
        Colors.print_white("\n➕ ADD CAMERA")
        
        try:
            name = input(f"{Colors.CYAN}Camera name: {Colors.RESET}").strip()
            url = input(f"{Colors.CYAN}Stream URL: {Colors.RESET}").strip()
            lat = float(input(f"{Colors.CYAN}Latitude: {Colors.RESET}").strip())
            lng = float(input(f"{Colors.CYAN}Longitude: {Colors.RESET}").strip())
            city = input(f"{Colors.CYAN}City: {Colors.RESET}").strip()
            country = input(f"{Colors.CYAN}Country: {Colors.RESET}").strip()
            
            camera_id = hashlib.md5(f"{url}_{time.time()}".encode()).hexdigest()[:16]
            
            # Save to database
            conn = sqlite3.connect('face_hunt_results.db', check_same_thread=False)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO cameras 
                (camera_id, name, url, latitude, longitude, city, country, is_active, last_checked)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)
            ''', (camera_id, name, url, lat, lng, city, country, time.time()))
            
            conn.commit()
            conn.close()
            
            Colors.print_success("Camera added successfully!")
            
            # Reload cameras
            self.hunter.camera_network.load_cameras()
            
        except Exception as e:
            Colors.print_alert(f"Failed to add camera: {e}")
    
    def discover_cameras(self):
        """Discover public cameras"""
        Colors.print_info("Discovering public cameras...")
        
        discovered = self.hunter.camera_network.discover_public_cameras()
        
        if discovered:
            Colors.print_success(f"Found {len(discovered)} public cameras")
            
            # Add to database
            conn = sqlite3.connect('face_hunt_results.db', check_same_thread=False)
            cursor = conn.cursor()
            
            for cam in discovered:
                camera_id = hashlib.md5(cam['url'].encode()).hexdigest()[:16]
                
                cursor.execute('''
                    INSERT OR IGNORE INTO cameras 
                    (camera_id, name, url, latitude, longitude, city, country, is_active, last_checked)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)
                ''', (camera_id, cam['name'], cam['url'], cam['latitude'], 
                     cam['longitude'], cam['city'], cam['country'], time.time()))
            
            conn.commit()
            conn.close()
            
            Colors.print_success("Cameras added to database!")
            
            # Reload cameras
            self.hunter.camera_network.load_cameras()
        
        else:
            Colors.print_alert("No public cameras found")
    
    def test_camera(self):
        """Test camera connection"""
        url = input(f"{Colors.CYAN}Enter camera URL to test: {Colors.RESET}").strip()
        
        Colors.print_info(f"Testing connection to: {url}")
        
        cap = cv2.VideoCapture(url)
        if cap.isOpened():
            ret, frame = cap.read()
            cap.release()
            
            if ret and frame is not None:
                Colors.print_success("✓ Camera is accessible")
                Colors.print_info(f"  Frame size: {frame.shape[1]}x{frame.shape[0]}")
                
                # Save test frame
                test_dir = "camera_tests"
                os.makedirs(test_dir, exist_ok=True)
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                test_file = f"{test_dir}/test_{timestamp}.jpg"
                cv2.imwrite(test_file, frame)
                
                Colors.print_info(f"  Test frame saved: {test_file}")
            else:
                Colors.print_alert("✗ Camera stream empty")
        else:
            Colors.print_alert("✗ Cannot open camera stream")

# ============================================================================
# MAIN MENU
# ============================================================================

def main_menu():
    """Main menu interface"""
    search_engine = ManualFaceSearch()
    
    while True:
        Colors.print_gold("\n" + "═"*60)
        Colors.print_gold("          EAGLE EYE - MAIN MENU")
        Colors.print_gold("═"*60)
        print()
        
        Colors.print_white("1. 🔍 Start Face Search (Upload Image)")
        Colors.print_white("2. 📁 Batch Search (Multiple Images)")
        Colors.print_white("3. 📜 View Search History")
        Colors.print_white("4. 📡 Camera Manager")
        Colors.print_white("5. 🗺️  View Last Search Map")
        Colors.print_white("6. ⚙️  Settings")
        Colors.print_white("7. 🚪 Exit")
        
        choice = input(f"\n{Colors.CYAN}Select option (1-7): {Colors.RESET}").strip()
        
        if choice == '1':
            search_engine.start_search()
        elif choice == '2':
            search_engine.batch_search()
        elif choice == '3':
            search_engine.view_history()
        elif choice == '4':
            search_engine.camera_manager()
        elif choice == '5':
            Colors.print_info("Opening last search map...")
            # Implementation for viewing map
        elif choice == '6':
            Colors.print_info("Settings menu would be here")
        elif choice == '7':
            Colors.print_gold("\n👋 Thank you for using Eagle Eye!")
            break
        else:
            Colors.print_alert("Invalid choice!")

# ============================================================================
# STARTUP
# ============================================================================

if __name__ == "__main__":
    # Create necessary directories
    os.makedirs("search_results", exist_ok=True)
    os.makedirs("alerts", exist_ok=True)
    os.makedirs("camera_tests", exist_ok=True)
    
    # Check dependencies
    try:
        import cv2
        import numpy as np
        import torch
    except ImportError as e:
        Colors.print_alert(f"Missing dependency: {e}")
        Colors.print_info("Install with: pip install opencv-python numpy torch")
        sys.exit(1)
    
    # Welcome message
    Colors.print_gold("\n" + "★"*60)
    Colors.print_gold("                 WELCOME TO EAGLE EYE")
    Colors.print_gold("         AI-Powered Face Hunter System")
    Colors.print_gold("★"*60)
    Colors.print_info("\nFeatures:")
    Colors.print_white("  • Upload face image")
    Colors.print_white("  • AI-powered face recognition")
    Colors.print_white("  • Real-time CCTV scanning")
    Colors.print_white("  • Geo-location tracking")
    Colors.print_white("  • Instant alerts")
    Colors.print_white("  • Interactive maps")
    Colors.print_info("\nReady to hunt!")
    
    # Start main menu
    try:
        main_menu()
    except KeyboardInterrupt:
        Colors.print_gold("\n\n👋 Goodbye!")
    except Exception as e:
        Colors.print_alert(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()