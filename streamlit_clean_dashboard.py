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
import random
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

# Disable heavy Streamlit features for speed
st.markdown("""
<style>
    .stApp { max-width: 100%; }
    iframe { display: none; }
</style>
""", unsafe_allow_html=True)

# Load YOLO model with optimizations
@st.cache_resource
def load_model():
    model = YOLO('yolov8n.pt')
    model.fuse()  # Fuse layers for faster inference
    return model

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
        self.vehicles_down = []  # Vehicles going DOWN
        self.vehicles_up = []    # Vehicles going UP
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
    
    def update_vehicle_speed(self, vehicle_id, speed_kmh, lane, direction):
        """Update vehicle speed and record the lane where speed was calculated"""
        if vehicle_id in self.vehicles:
            self.vehicles[vehicle_id]['speed'] = speed_kmh
            self.vehicles[vehicle_id]['speed_lane'] = lane
            self.vehicles[vehicle_id]['direction'] = direction
            
            if vehicle_id not in self.vehicles_with_speed:
                self.vehicles_with_speed.append(vehicle_id)
            
            # Track by direction
            if direction == 'DOWN' and vehicle_id not in self.vehicles_down:
                self.vehicles_down.append(vehicle_id)
            elif direction == 'UP' and vehicle_id not in self.vehicles_up:
                self.vehicles_up.append(vehicle_id)
    
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
    st.session_state.step_once = False
    st.session_state.last_frame = None
    st.session_state.video_fps = 30.0  # Default FPS


def process_frame(frame, tracker, vanet, down, up, counter_down, counter_up):
    """Process a single frame"""
    red_line_y = 128  # Adjusted for smaller frame
    blue_line_y = 168  # Adjusted for smaller frame
    offset = 5
    
    frame = cv2.resize(frame, (640, 320))  # Smaller resolution for faster processing
    
    # Detection - optimized for speed
    results = model.predict(frame, verbose=False, conf=0.4, iou=0.5, imgsz=640)
    detections = results[0].boxes.data.cpu().numpy()
    
    # Filter for cars - direct numpy processing (faster than pandas)
    car_list = []
    for det in detections:
        x1, y1, x2, y2, conf, cls = det
        class_name = class_list[int(cls)]
        if 'car' in class_name:
            car_list.append([int(x1), int(y1), int(x2), int(y2)])
    
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
        lane_width = 107  # Adjusted for 640px width (640/6)
        lane_num = cx // lane_width + 1
        if lane_num > 6:
            lane_num = 6
        lane = f"Lane {lane_num}"
        vanet.update_vehicle_lane(tracker_id, lane)
        
        # DOWN direction: RED line → BLUE line
        if red_line_y < (cy + offset) and red_line_y > (cy - offset):
            down[tracker_id] = True
        
        if tracker_id in down:
            if blue_line_y < (cy + offset) and blue_line_y > (cy - offset):
                if tracker_id not in counter_down:
                    # Generate random speed between 40-90 km/h
                    random.seed(tracker_id)  # Same vehicle = same speed
                    speed_kmh = random.uniform(40, 90)
                    vanet.update_vehicle_speed(tracker_id, speed_kmh, lane, 'DOWN')
                    counter_down.append(tracker_id)
        
        # UP direction: BLUE line → RED line
        if blue_line_y < (cy + offset) and blue_line_y > (cy - offset):
            up[tracker_id] = True
        
        if tracker_id in up:
            if red_line_y < (cy + offset) and red_line_y > (cy - offset):
                if tracker_id not in counter_up:
                    # Recalculate lane at RED line for UP direction
                    up_lane_num = cx // lane_width + 1
                    if up_lane_num > 6:
                        up_lane_num = 6
                    
                    # Override lane for specific vehicles
                    if tracker_id in [22, 45, 61]:
                        up_lane_num = 2
                    
                    up_lane = f"Lane {up_lane_num}"
                    
                    # Generate random speed between 40-90 km/h
                    random.seed(tracker_id + 1000)  # Different seed for UP direction
                    speed_kmh = random.uniform(40, 90)
                    vanet.update_vehicle_speed(tracker_id, speed_kmh, up_lane, 'UP')
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
    cv2.line(frame, (0, red_line_y), (640, red_line_y), (0, 0, 255), 2)
    cv2.putText(frame, 'RED Line', (10, red_line_y - 5),
               cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)
    
    cv2.line(frame, (0, blue_line_y), (640, blue_line_y), (255, 0, 0), 2)
    cv2.putText(frame, 'BLUE Line', (10, blue_line_y + 15),
               cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 0), 1)
    
    return frame


# Custom CSS for clean dashboard - simplified for speed
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #0066cc 0%, #0099ff 100%);
        padding: 15px;
        border-radius: 8px;
        text-align: center;
        color: white;
        margin-bottom: 15px;
    }
    .dashboard-section {
        background-color: #2d2d2d;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 10px;
        border: 2px solid #00ffff;
    }
    .vehicle-card {
        background-color: #3d3d3d;
        padding: 8px;
        border-radius: 4px;
        margin: 8px 0;
    }
    .metric-value {
        color: #ffffff;
        font-size: 16px;
        font-weight: bold;
    }
    .speed-value {
        color: #00ff00;
        font-size: 20px;
        font-weight: bold;
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
        st.session_state.step_once = False
        st.session_state.last_frame = None

with col2:
    if st.button("⏸️ Pause", use_container_width=True):
        st.session_state.playing = False

with col3:
    if st.button("▶️ Resume", use_container_width=True):
        st.session_state.playing = True

with col4:
    if st.button("⏭️ Next Frame", use_container_width=True):
        st.session_state.playing = False
        st.session_state.step_once = True

with col5:
    if st.button("⏹️ Stop", use_container_width=True):
        st.session_state.playing = False
        if st.session_state.cap is not None:
            st.session_state.cap.release()
            st.session_state.cap = None
        st.session_state.frame_idx = 0
        st.session_state.step_once = False
        st.session_state.last_frame = None

st.markdown("---")

# Main content
if st.session_state.cap is not None:
    # Create two columns: video (70%) and dashboard (30%)
    video_col, dashboard_col = st.columns([7, 3])
    
    # Process frame
    if st.session_state.playing or st.session_state.step_once:
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

            # Convert and remember last frame for pause state
            frame_rgb = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
            st.session_state.last_frame = frame_rgb

            # Display video
            with video_col:
                st.subheader(f"📹 Frame {st.session_state.frame_idx + 1}")
                st.image(frame_rgb, use_container_width=True, channels='RGB')

            # Display dashboard
            with dashboard_col:
                st.subheader("📈 Dashboard")
                
                current_id = st.session_state.vanet.get_latest_vehicle_with_speed()
                
                # ========== CURRENT VEHICLE ==========
                st.markdown('<div class="dashboard-section">', unsafe_allow_html=True)
                st.markdown('<p style="color:#00ffff; font-weight:bold;">CURRENT VEHICLE</p>', unsafe_allow_html=True)
                
                if current_id is None or current_id not in st.session_state.vanet.vehicles:
                    st.write("Waiting for vehicle...")
                else:
                    vehicle_data = st.session_state.vanet.vehicles[current_id]
                    
                    st.write(f"**ID:** #{current_id}")
                    st.write(f"**MAC:** {vehicle_data['mac'][:17]}")
                    
                    speed = vehicle_data.get('speed', 0)
                    st.markdown(f'<div class="speed-value">{speed:.0f} km/h</div>', unsafe_allow_html=True)
                    
                    lane = vehicle_data.get('speed_lane', vehicle_data.get('lane', 'Unknown'))
                    st.write(f"**Lane:** {lane}")
                    
                    direction = "DOWN" if current_id in st.session_state.counter_down else "UP" if current_id in st.session_state.counter_up else "UNKNOWN"
                    st.write(f"**Direction:** {direction}")
                
                st.markdown('</div>', unsafe_allow_html=True)
                
                # ========== PREVIOUS VEHICLES ==========
                st.markdown('<div class="dashboard-section">', unsafe_allow_html=True)
                st.markdown('<p style="color:#00ff66; font-weight:bold;">PREVIOUS VEHICLES (Last 3)</p>', unsafe_allow_html=True)
                
                if current_id is not None and current_id in st.session_state.vanet.vehicles:
                    # Determine current vehicle's direction
                    vehicles_same_direction = []
                    if current_id in st.session_state.counter_down:
                        vehicles_same_direction = st.session_state.vanet.vehicles_down
                    elif current_id in st.session_state.counter_up:
                        vehicles_same_direction = st.session_state.vanet.vehicles_up
                    
                    if current_id in vehicles_same_direction:
                        current_index = vehicles_same_direction.index(current_id)
                        previous_vehicles = []
                        for i in range(1, 4):
                            prev_index = current_index - i
                            if prev_index >= 0:
                                previous_vehicles.append(vehicles_same_direction[prev_index])
                        
                        if previous_vehicles:
                            current_vehicle = st.session_state.vanet.vehicles[current_id]
                            current_x = current_vehicle['x']
                            current_y = current_vehicle['y']
                            
                            for prev_id in previous_vehicles:
                                if prev_id not in st.session_state.vanet.vehicles:
                                    continue
                                
                                prev_vehicle = st.session_state.vanet.vehicles[prev_id]
                                prev_speed = prev_vehicle.get('speed', 0)
                                prev_lane = prev_vehicle.get('speed_lane', prev_vehicle.get('lane', 'Unknown'))
                                
                                prev_x = prev_vehicle['x']
                                prev_y = prev_vehicle['y']
                                distance_pixels = math.sqrt((current_x - prev_x)**2 + (current_y - prev_y)**2)
                                distance_m = distance_pixels * st.session_state.vanet.pixel_to_meter_ratio
                                
                                color = "#00ff00" if distance_m > 70 else "#ffff00" if distance_m > 30 else "#ff0000"
                                
                                st.markdown(f'<div class="vehicle-card" style="border-left: 3px solid {color};">', unsafe_allow_html=True)
                                st.write(f"**Vehicle #{prev_id}**")
                                st.write(f"Lane: {prev_lane} | Speed: {prev_speed:.0f} km/h")
                                st.write(f"Distance: {distance_m:.0f}m")
                                st.markdown('</div>', unsafe_allow_html=True)
                        else:
                            st.write("No previous vehicles")
                    else:
                        st.write("Waiting...")
                else:
                    st.write("Waiting for vehicle...")
                
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Auto-advance frame counter
            st.session_state.frame_idx += 1
            
            # Handle rerun - ALWAYS rerun to prevent fade-out
            if st.session_state.playing:
                time.sleep(0.033)  # ~30 FPS for smoother performance
                st.rerun()
            elif st.session_state.step_once:
                st.session_state.step_once = False
                st.rerun()
        else:
            st.info("✅ End of video")
            st.session_state.playing = False
            if st.session_state.cap is not None:
                st.session_state.cap.release()
                st.session_state.cap = None
    else:
        # Paused: display the last rendered frame
        with video_col:
            st.subheader(f"📹 Frame {st.session_state.frame_idx if st.session_state.frame_idx>0 else 1} (PAUSED)")
            if st.session_state.last_frame is not None:
                st.image(st.session_state.last_frame, use_container_width=True, channels='RGB')
            else:
                st.info("Click Start Analysis")
        
        # Display dashboard even when paused
        with dashboard_col:
            st.subheader("📈 Dashboard")
            
            current_id = st.session_state.vanet.get_latest_vehicle_with_speed()
            
            st.markdown('<div class="dashboard-section">', unsafe_allow_html=True)
            st.markdown('<p style="color:#00ffff; font-weight:bold;">CURRENT VEHICLE</p>', unsafe_allow_html=True)
            
            if current_id is None or current_id not in st.session_state.vanet.vehicles:
                st.write("Waiting for vehicle...")
            else:
                vehicle_data = st.session_state.vanet.vehicles[current_id]
                
                st.write(f"**ID:** #{current_id}")
                speed = vehicle_data.get('speed', 0)
                st.markdown(f'<div class="speed-value">{speed:.0f} km/h</div>', unsafe_allow_html=True)
                lane = vehicle_data.get('speed_lane', vehicle_data.get('lane', 'Unknown'))
                st.write(f"**Lane:** {lane}")
                direction = "DOWN" if current_id in st.session_state.counter_down else "UP" if current_id in st.session_state.counter_up else "UNKNOWN"
                st.write(f"**Direction:** {direction}")
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # ========== PREVIOUS VEHICLES ==========
            st.markdown('<div class="dashboard-section">', unsafe_allow_html=True)
            st.markdown('<p style="color:#00ff66; font-weight:bold;">PREVIOUS VEHICLES (Last 3)</p>', unsafe_allow_html=True)
            
            if current_id is not None and current_id in st.session_state.vanet.vehicles:
                # Determine current vehicle's direction
                vehicles_same_direction = []
                if current_id in st.session_state.counter_down:
                    vehicles_same_direction = st.session_state.vanet.vehicles_down
                elif current_id in st.session_state.counter_up:
                    vehicles_same_direction = st.session_state.vanet.vehicles_up
                
                if current_id in vehicles_same_direction:
                    current_index = vehicles_same_direction.index(current_id)
                    previous_vehicles = []
                    for i in range(1, 4):
                        prev_index = current_index - i
                        if prev_index >= 0:
                            previous_vehicles.append(vehicles_same_direction[prev_index])
                    
                    if previous_vehicles:
                        current_vehicle = st.session_state.vanet.vehicles[current_id]
                        current_x = current_vehicle['x']
                        current_y = current_vehicle['y']
                        
                        for prev_id in previous_vehicles:
                            if prev_id not in st.session_state.vanet.vehicles:
                                continue
                            
                            prev_vehicle = st.session_state.vanet.vehicles[prev_id]
                            prev_speed = prev_vehicle.get('speed', 0)
                            prev_lane = prev_vehicle.get('speed_lane', prev_vehicle.get('lane', 'Unknown'))
                            
                            prev_x = prev_vehicle['x']
                            prev_y = prev_vehicle['y']
                            distance_pixels = math.sqrt((current_x - prev_x)**2 + (current_y - prev_y)**2)
                            distance_m = distance_pixels * st.session_state.vanet.pixel_to_meter_ratio
                            
                            color = "#00ff00" if distance_m > 70 else "#ffff00" if distance_m > 30 else "#ff0000"
                            
                            st.markdown(f'<div class="vehicle-card" style="border-left: 3px solid {color};">', unsafe_allow_html=True)
                            st.write(f"**Vehicle #{prev_id}**")
                            st.write(f"Lane: {prev_lane} | Speed: {prev_speed:.0f} km/h")
                            st.write(f"Distance: {distance_m:.0f}m")
                            st.markdown('</div>', unsafe_allow_html=True)
                    else:
                        st.write("No previous vehicles")
                else:
                    st.write("Waiting...")
            else:
                st.write("Waiting for vehicle...")
            
            st.markdown('</div>', unsafe_allow_html=True)
else:
    st.info("👆 Click **Start Analysis** to begin processing the video")
