# -*- coding: utf-8 -*-
"""
VANET Streamlit Dashboard
Web-based interface for Vehicle Speed Estimation and VANET Communication
"""

import streamlit as st
import cv2
from ultralytics import YOLO
from tracker import Tracker
import pandas as pd
import numpy as np
import time
import math
import hashlib
from PIL import Image
import io

# Page configuration
st.set_page_config(
    page_title="VANET Speed Estimation",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        padding: 1rem;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #1f77b4;
    }
    .vehicle-info {
        background-color: #e8f4f8;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
    .previous-vehicle {
        background-color: #fff3cd;
        padding: 0.8rem;
        border-radius: 6px;
        margin: 0.5rem 0;
        border-left: 3px solid #ffc107;
    }
    </style>
""", unsafe_allow_html=True)

# MAC address generation function
def generate_vehicle_mac(tracker_id):
    hash_object = hashlib.md5(str(tracker_id).encode())
    hex_dig = hash_object.hexdigest()
    mac = ':'.join([hex_dig[i:i+2] for i in range(0, 12, 2)])
    return mac.upper()

# VANET Class
class CleanVANET:
    def __init__(self):
        self.vehicles = {}
        self.vehicles_with_speed = []
        self.communication_range = 300  # meters
        self.pixel_per_meter = 1.5
        self.messages = {}
        self.message_lifetime = 10
        
    def get_lane(self, x, y):
        lane_width = 170
        lane_number = int(x / lane_width) + 1
        lane_number = min(max(lane_number, 1), 6)
        return f"Lane {lane_number}"
    
    def add_vehicle(self, tracker_id, x, y, speed=None):
        current_time = time.time()
        lane = self.get_lane(x, y)
        
        if tracker_id not in self.vehicles:
            self.vehicles[tracker_id] = {
                'x': x,
                'y': y,
                'speed': None,
                'lane': lane,
                'speed_lane': None,
                'last_update': current_time,
                'mac': generate_vehicle_mac(tracker_id)
            }
        else:
            self.vehicles[tracker_id]['x'] = x
            self.vehicles[tracker_id]['y'] = y
            self.vehicles[tracker_id]['lane'] = lane
            self.vehicles[tracker_id]['last_update'] = current_time
        
        if speed is not None:
            self.vehicles[tracker_id]['speed'] = speed
            self.vehicles[tracker_id]['speed_lane'] = lane
            if tracker_id not in self.vehicles_with_speed:
                self.vehicles_with_speed.append(tracker_id)
    
    def broadcast_speed(self, sender_id, speed):
        if sender_id not in self.vehicles:
            return
        
        sender = self.vehicles[sender_id]
        current_time = time.time()
        
        for vehicle_id, vehicle in self.vehicles.items():
            if vehicle_id == sender_id:
                continue
            
            distance = math.sqrt((sender['x'] - vehicle['x'])**2 + (sender['y'] - vehicle['y'])**2)
            distance_meters = distance / self.pixel_per_meter
            
            if distance_meters <= self.communication_range:
                message_key = f"{sender_id}_to_{vehicle_id}"
                self.messages[message_key] = {
                    'from_vehicle': sender_id,
                    'to_vehicle': vehicle_id,
                    'speed': speed,
                    'distance': distance_meters,
                    'timestamp': current_time,
                    'lane': sender['speed_lane'] if sender['speed_lane'] else sender['lane']
                }
        
        self.messages = {k: v for k, v in self.messages.items() 
                        if current_time - v['timestamp'] < self.message_lifetime}
    
    def get_latest_vehicle_with_speed(self):
        if not self.vehicles_with_speed:
            return None
        return self.vehicles_with_speed[-1]
    
    def get_previous_vehicles(self, current_id, count=3):
        if current_id not in self.vehicles_with_speed:
            return []
        
        current_index = self.vehicles_with_speed.index(current_id)
        previous_vehicles = []
        
        for i in range(1, count + 1):
            prev_index = current_index - i
            if prev_index >= 0:
                previous_vehicles.append(self.vehicles_with_speed[prev_index])
        
        return previous_vehicles

# Load YOLO model
@st.cache_resource
def load_model():
    return YOLO('yolov8n.pt')

# Class list
class_list = ['person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat', 
              'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird', 'cat', 
              'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 'giraffe', 'backpack', 
              'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball', 
              'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard', 'tennis racket', 
              'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple', 
              'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 
              'couch', 'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse', 'remote', 
              'keyboard', 'cell phone', 'microwave', 'oven', 'toaster', 'sink', 'refrigerator', 'book', 
              'clock', 'vase', 'scissors', 'teddy bear', 'hair drier', 'toothbrush']

# Process single frame
def process_frame(frame, model, tracker, vanet, down, up, counter_down, counter_up, 
                  red_line_y, blue_line_y, count):
    offset = 7
    frame_resized = cv2.resize(frame, (1020, 500))
    
    # YOLO detection
    results = model.predict(frame_resized)
    detections = results[0].boxes.data
    px = pd.DataFrame(detections).astype("float")
    
    # Filter vehicles
    vehicle_list = []
    for index, row in px.iterrows():
        x1, y1, x2, y2, _, d = int(row[0]), int(row[1]), int(row[2]), int(row[3]), int(row[4]), int(row[5])
        c = class_list[d]
        if 'car' in c or 'truck' in c or 'bus' in c:
            vehicle_list.append([x1, y1, x2, y2])
    
    # Track vehicles
    bbox_id = tracker.update(vehicle_list)
    
    # Process each tracked vehicle
    for bbox in bbox_id:
        x3, y3, x4, y4, tracker_id = bbox
        cx, cy = (x3 + x4) // 2, (y3 + y4) // 2
        
        # Add vehicle to VANET
        vanet.add_vehicle(tracker_id, cx, cy)
        
        # Speed calculation - DOWN direction
        if red_line_y < (cy + offset) and red_line_y > (cy - offset):
            down[tracker_id] = time.time()
        
        if tracker_id in down:
            if blue_line_y < (cy + offset) and blue_line_y > (cy - offset):
                elapsed_time = time.time() - down[tracker_id]
                if counter_down.count(tracker_id) == 0:
                    counter_down.append(tracker_id)
                    distance = 100  # meters
                    speed_ms = distance / elapsed_time
                    speed_kmh = speed_ms * 3.6
                    vanet.add_vehicle(tracker_id, cx, cy, speed_kmh)
                    vanet.broadcast_speed(tracker_id, speed_kmh)
        
        # Speed calculation - UP direction
        if blue_line_y < (cy + offset) and blue_line_y > (cy - offset):
            up[tracker_id] = time.time()
        
        if tracker_id in up:
            if red_line_y < (cy + offset) and red_line_y > (cy - offset):
                elapsed_time = time.time() - up[tracker_id]
                if counter_up.count(tracker_id) == 0:
                    counter_up.append(tracker_id)
                    distance = 100  # meters
                    speed_ms = distance / elapsed_time
                    speed_kmh = speed_ms * 3.6
                    vanet.add_vehicle(tracker_id, cx, cy, speed_kmh)
                    vanet.broadcast_speed(tracker_id, speed_kmh)
        
        # Draw bounding box
        cv2.rectangle(frame_resized, (x3, y3), (x4, y4), (0, 255, 0), 2)
        cv2.putText(frame_resized, f'ID:{tracker_id}', (x3, y3-10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        
        # Draw speed if available
        if tracker_id in vanet.vehicles and vanet.vehicles[tracker_id]['speed']:
            speed = vanet.vehicles[tracker_id]['speed']
            cv2.putText(frame_resized, f'{int(speed)}km/h', (x3, y4+20), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
    
    # Draw lines
    cv2.line(frame_resized, (0, red_line_y), (1020, red_line_y), (0, 0, 255), 2)
    cv2.putText(frame_resized, 'RED LINE', (10, red_line_y-10), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
    
    cv2.line(frame_resized, (0, blue_line_y), (1020, blue_line_y), (255, 0, 0), 2)
    cv2.putText(frame_resized, 'BLUE LINE', (10, blue_line_y+25), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
    
    # Draw counters
    cv2.putText(frame_resized, f'DOWN: {len(counter_down)}', (10, 30), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(frame_resized, f'UP: {len(counter_up)}', (10, 60), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    return frame_resized, vanet, count + 1

# Main Streamlit App
def main():
    # Header
    st.markdown('<div class="main-header">🚗 VANET Vehicle Speed Estimation Dashboard</div>', 
                unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("📁 Upload Video")
        uploaded_file = st.file_uploader("Choose a video file", type=['mp4', 'avi', 'mov'])
        
        st.markdown("---")
        st.info("💡 **Note:** Upload your video file. The system will process it frame-by-frame using YOLO object detection and VANET communication.")
        
        st.markdown("---")
        st.header("⚙️ Settings")
        show_stats = st.checkbox("Show Statistics", value=True)
        
        st.markdown("---")
        st.header("🎮 Controls")
        st.info("🎯 **Frame-by-frame mode**\n\nPress **SPACE** to pause/resume\n\nPress **Q** to quit")
        
        run_button = st.button("▶️ Run Analysis", type="primary", use_container_width=True)
        stop_button = st.button("⏹️ Stop", use_container_width=True)
    
    # Main content area - Two columns (70%-30%)
    col1, col2 = st.columns([7, 3])
    
    with col1:
        st.subheader("📹 Video Stream")
        video_placeholder = st.empty()
        progress_bar = st.progress(0)
        status_text = st.empty()
    
    with col2:
        st.subheader("📊 VANET Dashboard")
        
        # Current Vehicle Section
        st.markdown("### 🚘 Current Vehicle")
        current_vehicle_container = st.container()
        
        # Previous Vehicles Section
        st.markdown("### 📋 Previous Vehicles")
        previous_vehicles_container = st.container()
        
        # Statistics Section
        if show_stats:
            st.markdown("### 📈 Statistics")
            stats_container = st.container()
    
    # Run analysis
    if run_button or st.session_state.get('running', False):
        if not uploaded_file and not st.session_state.get('running', False):
            st.warning("⚠️ Please upload a video file first!")
            return
        
        st.session_state['running'] = True
        
        # Use the existing highway_mini.mp4 (ignore uploaded file for now)
        video_path = 'highway_mini.mp4'
        
        # Initialize
        model = load_model()
        tracker = Tracker()
        vanet = CleanVANET()
        
        down = {}
        up = {}
        counter_down = []
        counter_up = []
        count = 0
        
        red_line_y = 198
        blue_line_y = 268
        
        # Open video
        cap = cv2.VideoCapture(video_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        
        status_text.text(f"📹 Processing video: {total_frames} frames @ {fps} FPS | Press SPACE to pause/resume, Q to quit")
        
        # Create OpenCV window for keyboard control
        cv2.namedWindow('VANET Control (Press SPACE to pause, Q to quit)', cv2.WINDOW_NORMAL)
        cv2.resizeWindow('VANET Control (Press SPACE to pause, Q to quit)', 400, 100)
        
        # Create a control image
        control_img = np.zeros((100, 400, 3), dtype=np.uint8)
        cv2.putText(control_img, 'Press SPACE to Pause/Resume', (20, 40), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(control_img, 'Press Q to Quit', (20, 70), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.imshow('VANET Control (Press SPACE to pause, Q to quit)', control_img)
        
        frame_count = 0
        paused = False
        
        while cap.isOpened() and st.session_state.get('running', False):
            if not paused:
                ret, frame = cap.read()
                if not ret:
                    break
                
                frame_count += 1
                
                # Process frame
                processed_frame, vanet, count = process_frame(
                    frame, model, tracker, vanet, down, up, 
                    counter_down, counter_up, red_line_y, blue_line_y, count
                )
                
                # Convert BGR to RGB for Streamlit
                processed_frame_rgb = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
                
                # Display video
                video_placeholder.image(processed_frame_rgb, channels="RGB", use_container_width=True)
                
                # Update progress
                progress = frame_count / total_frames
                progress_bar.progress(progress)
                
                # Update dashboard
                current_vehicle_id = vanet.get_latest_vehicle_with_speed()
                
                if current_vehicle_id is not None:
                    current = vanet.vehicles[current_vehicle_id]
                    
                    with current_vehicle_container:
                        st.markdown(f"""
                        <div class="vehicle-info">
                            <strong>Vehicle ID:</strong> #{current_vehicle_id}<br>
                            <strong>MAC Address:</strong> {current['mac']}<br>
                            <strong>Speed:</strong> {int(current['speed'])} km/h<br>
                            <strong>Lane:</strong> {current['speed_lane']}<br>
                            <strong>Direction:</strong> {'DOWN' if current_vehicle_id in counter_down else 'UP'}
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Previous vehicles
                    previous_ids = vanet.get_previous_vehicles(current_vehicle_id, 3)
                    
                    with previous_vehicles_container:
                        if previous_ids:
                            for prev_id in previous_ids:
                                prev = vanet.vehicles[prev_id]
                                
                                # Calculate distance
                                distance = math.sqrt(
                                    (current['x'] - prev['x'])**2 + 
                                    (current['y'] - prev['y'])**2
                                )
                                distance_meters = distance / vanet.pixel_per_meter
                                
                                # Color based on distance
                                if distance_meters < 30:
                                    color = "🔴"
                                elif distance_meters < 70:
                                    color = "🟡"
                                else:
                                    color = "🟢"
                                
                                st.markdown(f"""
                                <div class="previous-vehicle">
                                    {color} <strong>Vehicle #{prev_id}</strong><br>
                                    Lane: {prev['speed_lane']}<br>
                                    Distance: {int(distance_meters)}m<br>
                                    Speed: {int(prev['speed'])} km/h
                                </div>
                                """, unsafe_allow_html=True)
                        else:
                            st.info("No previous vehicles")
                
                # Statistics
                if show_stats:
                    with stats_container:
                        total_vehicles = len(counter_down) + len(counter_up)
                        speeds = [v['speed'] for v in vanet.vehicles.values() if v['speed'] is not None]
                        avg_speed = np.mean(speeds) if speeds else 0
                        avg_speed_display = int(avg_speed) if (speeds and not np.isnan(avg_speed)) else 0
                        
                        col_a, col_b = st.columns(2)
                        col_a.metric("Total Vehicles", total_vehicles)
                        col_b.metric("Avg Speed", f"{avg_speed_display} km/h")
                        
                        col_c, col_d = st.columns(2)
                        col_c.metric("DOWN", len(counter_down))
                        col_d.metric("UP", len(counter_up))
            
            # Check for keyboard input (frame-by-frame control)
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord(' '):  # Spacebar - pause/resume
                paused = not paused
                if paused:
                    status_text.text("⏸️ PAUSED - Press SPACE to resume, Q to quit")
                    control_img = np.zeros((100, 400, 3), dtype=np.uint8)
                    cv2.putText(control_img, '⏸️ PAUSED', (120, 40), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                    cv2.putText(control_img, 'Press SPACE to Resume', (70, 70), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                    cv2.imshow('VANET Control (Press SPACE to pause, Q to quit)', control_img)
                else:
                    status_text.text(f"▶️ PLAYING - Frame {frame_count}/{total_frames}")
                    control_img = np.zeros((100, 400, 3), dtype=np.uint8)
                    cv2.putText(control_img, '▶️ PLAYING', (120, 40), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                    cv2.putText(control_img, 'Press SPACE to Pause', (70, 70), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                    cv2.imshow('VANET Control (Press SPACE to pause, Q to quit)', control_img)
            
            elif key == ord('q') or key == ord('Q'):  # Q - quit
                st.session_state['running'] = False
                break
            
            # Stop button check
            if stop_button:
                st.session_state['running'] = False
                break
        
        cap.release()
        cv2.destroyAllWindows()
        st.session_state['running'] = False
        status_text.text("✅ Processing complete!")
        st.success("🎉 Video processing finished!")
    
    if stop_button:
        st.session_state['running'] = False
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
