"""
VANET Speed Estimation - Streamlit Clean Dashboard
Same dashboard style as vanet_clean_presentation.py but in web browser
With keyboard control using streamlit-keyup
"""

import streamlit as st
import cv2
import pandas as pd
import numpy as np
from ultralytics import YOLO
import time
import hashlib
import math
from tracker import Tracker
from PIL import Image

try:
    from st_keyup import st_keyup
    KEYUP_AVAILABLE = True
except ImportError:
    KEYUP_AVAILABLE = False

# Page config
st.set_page_config(
    page_title="VANET Clean Dashboard",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Load YOLO model
@st.cache_resource
def load_model():
    return YOLO('yolov8n.pt')

model = load_model()
class_list = model.names


def generate_vehicle_mac(tracker_id):
    """Generate a MAC address from tracker ID"""
    hash_object = hashlib.md5(str(tracker_id).encode())
    hash_hex = hash_object.hexdigest()
    mac = ':'.join([hash_hex[i:i+2] for i in range(0, 12, 2)])
    return mac.upper()


class CleanVANET:
    def __init__(self, communication_range=300):
        self.communication_range = communication_range
        self.vehicles = {}
        self.vehicles_with_speed = []
        self.pixel_to_meter_ratio = 1.5
    
    def add_vehicle(self, vehicle_id, x, y):
        """Add or update vehicle position"""
        if vehicle_id not in self.vehicles:
            self.vehicles[vehicle_id] = {
                'id': vehicle_id,
                'mac': generate_vehicle_mac(vehicle_id),
                'x': x,
                'y': y,
                'lane': None,
                'speed': None,
                'speed_lane': None,
                'last_update': time.time()
            }
        else:
            self.vehicles[vehicle_id]['x'] = x
            self.vehicles[vehicle_id]['y'] = y
            self.vehicles[vehicle_id]['last_update'] = time.time()
    
    def update_vehicle_speed(self, vehicle_id, speed_kmh, lane):
        """Update vehicle speed and record the lane where speed was calculated"""
        if vehicle_id in self.vehicles:
            self.vehicles[vehicle_id]['speed'] = speed_kmh
            self.vehicles[vehicle_id]['speed_lane'] = lane
            
            if vehicle_id not in self.vehicles_with_speed:
                self.vehicles_with_speed.append(vehicle_id)
    
    def update_vehicle_lane(self, vehicle_id, lane):
        """Update current lane"""
        if vehicle_id in self.vehicles:
            self.vehicles[vehicle_id]['lane'] = lane
    
    def get_latest_vehicle_with_speed(self):
        """Get the most recent vehicle that crossed the 2nd line"""
        if not self.vehicles_with_speed:
            return None
        return self.vehicles_with_speed[-1]


# Initialize session state
if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    st.session_state.frame_idx = 0
    st.session_state.playing = False
    st.session_state.tracker = Tracker()
    st.session_state.vanet = CleanVANET(communication_range=180)
    st.session_state.down = {}
    st.session_state.up = {}
    st.session_state.counter_down = []
    st.session_state.counter_up = []
    st.session_state.cap = None


def process_frame(frame, tracker, vanet, down, up, counter_down, counter_up):
    """Process a single frame"""
    red_line_y = 198
    blue_line_y = 268
    offset = 7
    
    frame = cv2.resize(frame, (1020, 500))
    
    # Detection
    results = model.predict(frame, verbose=False)
    a = results[0].boxes.data.detach().cpu().numpy()
    px = pd.DataFrame(a).astype("float")
    
    # Filter for cars
    car_list = []
    for index, row in px.iterrows():
        x1, y1, x2, y2 = int(row[0]), int(row[1]), int(row[2]), int(row[3])
        d = int(row[5])
        c = class_list[d]
        if 'car' in c:
            car_list.append([x1, y1, x2, y2])
    
    # Update tracker
    bbox_id = tracker.update(car_list)
    
    # Process each vehicle
    for bbox in bbox_id:
        x3, y3, x4, y4, tracker_id = bbox
        cx = (x3 + x4) // 2
        cy = (y3 + y4) // 2
        
        # Add/update vehicle in VANET
        vanet.add_vehicle(tracker_id, cx, cy)
        
        # Determine lane
        lane_width = 170
        lane_num = cx // lane_width + 1
        if lane_num > 6:
            lane_num = 6
        lane = f"Lane {lane_num}"
        vanet.update_vehicle_lane(tracker_id, lane)
        
        # DOWN direction: RED line → BLUE line
        if red_line_y < (cy + offset) and red_line_y > (cy - offset):
            down[tracker_id] = time.time()
        
        if tracker_id in down:
            if blue_line_y < (cy + offset) and blue_line_y > (cy - offset):
                if tracker_id not in counter_down:
                    elapsed_time = time.time() - down[tracker_id]
                    if elapsed_time > 0:
                        distance = 100  # meters
                        speed_ms = distance / elapsed_time
                        speed_kmh = speed_ms * 3.6
                        vanet.update_vehicle_speed(tracker_id, speed_kmh, lane)
                        counter_down.append(tracker_id)
        
        # UP direction: BLUE line → RED line
        if blue_line_y < (cy + offset) and blue_line_y > (cy - offset):
            up[tracker_id] = time.time()
        
        if tracker_id in up:
            if red_line_y < (cy + offset) and red_line_y > (cy - offset):
                if tracker_id not in counter_up:
                    elapsed_time = time.time() - up[tracker_id]
                    if elapsed_time > 0:
                        distance = 100  # meters
                        speed_ms = distance / elapsed_time
                        speed_kmh = speed_ms * 3.6
                        vanet.update_vehicle_speed(tracker_id, speed_kmh, lane)
                        counter_up.append(tracker_id)
        
        # Draw bounding box
        cv2.rectangle(frame, (x3, y3), (x4, y4), (0, 255, 0), 2)
        cv2.putText(frame, f"ID:{tracker_id}", (x3, y3 - 5),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Show speed if available
        if tracker_id in vanet.vehicles:
            vehicle_speed = vanet.vehicles[tracker_id].get('speed')
            if vehicle_speed:
                cv2.putText(frame, f"{vehicle_speed:.0f} km/h", (x3, y4 + 15),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    
    # Draw speed lines
    cv2.line(frame, (0, red_line_y), (1020, red_line_y), (0, 0, 255), 2)
    cv2.putText(frame, 'RED Line', (10, red_line_y - 5),
               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
    
    cv2.line(frame, (0, blue_line_y), (1020, blue_line_y), (255, 0, 0), 2)
    cv2.putText(frame, 'BLUE Line', (10, blue_line_y + 20),
               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
    
    return frame


# Custom CSS for clean dashboard
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #0066cc 0%, #0099ff 100%);
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        color: white;
        margin-bottom: 20px;
    }
    .dashboard-section {
        background-color: #2d2d2d;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 15px;
        border: 2px solid #00ffff;
    }
    .current-vehicle-section {
        border-color: #00ffff !important;
    }
    .previous-vehicles-section {
        border-color: #00ff66 !important;
    }
    .vehicle-card {
        background-color: #3d3d3d;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .metric-label {
        color: #aaaaaa;
        font-size: 14px;
    }
    .metric-value {
        color: #ffffff;
        font-size: 18px;
        font-weight: bold;
    }
    .speed-value {
        color: #00ff00;
        font-size: 24px;
        font-weight: bold;
    }
    .section-title {
        font-size: 18px;
        font-weight: bold;
        margin-bottom: 15px;
    }
    .current-title {
        color: #00ffff;
    }
    .previous-title {
        color: #00ff66;
    }
    .distance-close {
        color: #ff0000;
    }
    .distance-medium {
        color: #ffff00;
    }
    .distance-far {
        color: #00ff00;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="main-header"><h1>🚗 VANET CLEAN DASHBOARD</h1></div>', unsafe_allow_html=True)

# Keyboard control section
if KEYUP_AVAILABLE:
    col_info, col_keyup = st.columns([3, 1])
    with col_info:
        st.info("⌨️ **Keyboard Control**: Press **P** key to pause/resume")
    with col_keyup:
        key_pressed = st_keyup("", key="keyboard_input", debounce=300)
        if key_pressed and key_pressed.lower() == "p":  # P key
            st.session_state.playing = not st.session_state.playing

# Control buttons
col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 2])

with col1:
    if st.button("▶️ Start Analysis", use_container_width=True):
        if st.session_state.cap is None:
            st.session_state.cap = cv2.VideoCapture('highway_mini.mp4')
        st.session_state.playing = True
        st.session_state.frame_idx = 0
        # Reset state
        st.session_state.tracker = Tracker()
        st.session_state.vanet = CleanVANET(communication_range=180)
        st.session_state.down = {}
        st.session_state.up = {}
        st.session_state.counter_down = []
        st.session_state.counter_up = []

with col2:
    if st.button("⏸️ Pause", use_container_width=True):
        st.session_state.playing = False

with col3:
    if st.button("▶️ Resume", use_container_width=True):
        st.session_state.playing = True

with col4:
    if st.button("⏭️ Next Frame", use_container_width=True):
        st.session_state.playing = False
        st.session_state.frame_idx += 1

with col5:
    if st.button("⏹️ Stop", use_container_width=True):
        st.session_state.playing = False
        if st.session_state.cap is not None:
            st.session_state.cap.release()
            st.session_state.cap = None
        st.session_state.frame_idx = 0

st.markdown("---")

# Main content
if st.session_state.cap is not None:
    # Create two columns: video (70%) and dashboard (30%)
    video_col, dashboard_col = st.columns([7, 3])
    
    # Process frame
    if st.session_state.playing or st.session_state.frame_idx > 0:
        st.session_state.cap.set(cv2.CAP_PROP_POS_FRAMES, st.session_state.frame_idx)
        ret, frame = st.session_state.cap.read()
        
        if ret:
            processed_frame = process_frame(
                frame,
                st.session_state.tracker,
                st.session_state.vanet,
                st.session_state.down,
                st.session_state.up,
                st.session_state.counter_down,
                st.session_state.counter_up
            )
            
            # Display video
            with video_col:
                st.subheader(f"📹 Video - Frame {st.session_state.frame_idx + 1}")
                frame_rgb = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
                # Convert to PIL Image to avoid Streamlit media storage issues
                from PIL import Image as PILImage
                pil_image = PILImage.fromarray(frame_rgb)
                st.image(pil_image, use_container_width=True)
            
            # Display dashboard
            with dashboard_col:
                st.subheader("📊 Dashboard")
                
                current_id = st.session_state.vanet.get_latest_vehicle_with_speed()
                
                # ========== CURRENT VEHICLE ==========
                st.markdown('<div class="dashboard-section current-vehicle-section">', unsafe_allow_html=True)
                st.markdown('<div class="section-title current-title">CURRENT VEHICLE</div>', unsafe_allow_html=True)
                
                if current_id is None or current_id not in st.session_state.vanet.vehicles:
                    st.markdown('<div class="metric-label">Waiting for vehicle to cross 2nd line...</div>', unsafe_allow_html=True)
                else:
                    vehicle_data = st.session_state.vanet.vehicles[current_id]
                    
                    st.markdown(f'<div class="metric-label">Vehicle ID</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="metric-value">#{current_id}</div>', unsafe_allow_html=True)
                    
                    st.markdown(f'<div class="metric-label">MAC Address</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="metric-value" style="font-size: 14px;">{vehicle_data["mac"]}</div>', unsafe_allow_html=True)
                    
                    speed = vehicle_data.get('speed', 0)
                    st.markdown(f'<div class="metric-label">Speed</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="speed-value">{speed:.1f} km/h</div>', unsafe_allow_html=True)
                    
                    lane = vehicle_data.get('speed_lane', 'UNKNOWN')
                    if lane is None:
                        lane = vehicle_data.get('lane', 'UNKNOWN')
                    st.markdown(f'<div class="metric-label">Lane</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="metric-value">{lane}</div>', unsafe_allow_html=True)
                    
                    direction = "UNKNOWN"
                    if current_id in st.session_state.counter_down:
                        direction = "DOWN"
                    elif current_id in st.session_state.counter_up:
                        direction = "UP"
                    st.markdown(f'<div class="metric-label">Direction</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="metric-value">{direction}</div>', unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True)
                
                # ========== PREVIOUS VEHICLES ==========
                st.markdown('<div class="dashboard-section previous-vehicles-section">', unsafe_allow_html=True)
                st.markdown('<div class="section-title previous-title">PREVIOUS VEHICLES</div>', unsafe_allow_html=True)
                st.markdown('<div class="metric-label">(Last 3 that crossed)</div>', unsafe_allow_html=True)
                
                vehicles_with_speed = st.session_state.vanet.vehicles_with_speed
                
                if current_id is not None and current_id in vehicles_with_speed:
                    current_index = vehicles_with_speed.index(current_id)
                    previous_vehicles = []
                    for i in range(1, 4):
                        prev_index = current_index - i
                        if prev_index >= 0:
                            previous_vehicles.append(vehicles_with_speed[prev_index])
                    
                    if previous_vehicles:
                        current_vehicle = st.session_state.vanet.vehicles[current_id]
                        current_x = current_vehicle['x']
                        current_y = current_vehicle['y']
                        
                        for prev_id in previous_vehicles:
                            if prev_id not in st.session_state.vanet.vehicles:
                                continue
                            
                            prev_vehicle = st.session_state.vanet.vehicles[prev_id]
                            prev_x = prev_vehicle['x']
                            prev_y = prev_vehicle['y']
                            prev_speed = prev_vehicle.get('speed', 0)
                            prev_lane = prev_vehicle.get('speed_lane', 'Unknown')
                            if prev_lane is None:
                                prev_lane = prev_vehicle.get('lane', 'Unknown')
                            
                            distance_pixels = math.sqrt((current_x - prev_x)**2 + (current_y - prev_y)**2)
                            distance_m = distance_pixels * st.session_state.vanet.pixel_to_meter_ratio
                            
                            if distance_m < 30:
                                color_class = "distance-close"
                            elif distance_m < 70:
                                color_class = "distance-medium"
                            else:
                                color_class = "distance-far"
                            
                            st.markdown('<div class="vehicle-card">', unsafe_allow_html=True)
                            st.markdown(f'<div class="{color_class}"><strong>Vehicle #{prev_id}</strong></div>', unsafe_allow_html=True)
                            st.markdown(f'<div class="{color_class}">Lane: {prev_lane}</div>', unsafe_allow_html=True)
                            st.markdown(f'<div class="{color_class}">Distance: {distance_m:.0f}m</div>', unsafe_allow_html=True)
                            st.markdown(f'<div class="{color_class}">Speed: {prev_speed:.0f} km/h</div>', unsafe_allow_html=True)
                            st.markdown('</div>', unsafe_allow_html=True)
                    else:
                        st.markdown('<div class="metric-label">No previous vehicles</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="metric-label">Waiting for vehicles...</div>', unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Auto-advance if playing
            if st.session_state.playing:
                st.session_state.frame_idx += 1
                time.sleep(0.03)  # ~30 FPS
                st.rerun()
        else:
            st.info("✅ End of video")
            st.session_state.playing = False
            if st.session_state.cap is not None:
                st.session_state.cap.release()
                st.session_state.cap = None
else:
    st.info("👆 Click **Start Analysis** to begin processing the video")
    st.markdown("""
    ### Features:
    - 🎥 **Automatic frame-by-frame playback**
    - 🚗 **Vehicle detection and tracking** with YOLOv8
    - 📏 **Speed calculation** using dual-line timing method
    - 📡 **VANET dashboard** showing current and previous vehicles
    - 🎯 **Clean, simple interface** - same as terminal version
    
    ### Controls:
    - **Start Analysis**: Begin processing from frame 1
    - **Pause**: Stop playback
    - **Resume**: Continue playback
    - **Next Frame**: Advance one frame (manual mode)
    - **Stop**: Reset and stop
    """)
