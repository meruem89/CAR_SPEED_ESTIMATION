# -*- coding: utf-8 -*-
"""
VANET Clean Presentation Version
MAC Address-Based VANET with Clean Split-Screen Layout
Perfect for Project Review and Demonstration

Author: Car Speed Estimation Project
Features:
- 60% Video area with clean speed detection
- 40% Dashboard with VANET communication
- Frame-by-frame manual control
- Clear timing line speed calculation
- Minimal clutter for professional presentation
"""

from ultralytics import YOLO
from tracker import *
import cv2
import pandas as pd
import numpy as np
import time
import math
import hashlib

# Load YOLO model
model = YOLO('yolov8n.pt')

# Class list for detection
class_list = ['person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat', 
              'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird', 'cat', 
              'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 'giraffe', 'backpack', 
              'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball', 
              'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard', 'tennis racket', 
              'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple', 
              'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 
              'couch', 'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse', 
              'remote', 'keyboard', 'cell phone', 'microwave', 'oven', 'toaster', 'sink', 'refrigerator', 
              'book', 'clock', 'vase', 'scissors', 'teddy bear', 'hair drier', 'toothbrush']


def generate_vehicle_mac(tracker_id):
    """Generate realistic MAC address from tracker ID"""
    hash_obj = hashlib.md5(str(tracker_id).encode())
    mac_hex = hash_obj.hexdigest()[:12]
    mac_address = ':'.join([mac_hex[i:i+2].upper() for i in range(0, 12, 2)])
    return mac_address


class CleanVANET:
    """Clean VANET implementation for presentation"""
    
    def __init__(self, communication_range=180):
        self.vehicles = {}  # tracker_id -> vehicle data
        self.tracker_to_mac = {}
        self.pixel_to_meter_ratio = 1.5  # 100m / 70px
        self.vehicles_with_speed = []  # Track order of speed calculation
        
    def get_lane(self, x, y):
        """Get lane based on x position - 6 lanes total (3 DOWN, 3 UP)"""
        # Divide 1020px width into 6 equal lanes (170px each)
        if x < 170:
            return "Lane 1"
        elif x < 340:
            return "Lane 2"
        elif x < 510:
            return "Lane 3"
        elif x < 680:
            return "Lane 4"
        elif x < 850:
            return "Lane 5"
        else:
            return "Lane 6"
    
    def add_vehicle(self, tracker_id, x, y, speed=None):
        """Add or update vehicle"""
        if tracker_id not in self.tracker_to_mac:
            self.tracker_to_mac[tracker_id] = generate_vehicle_mac(tracker_id)
        
        mac = self.tracker_to_mac[tracker_id]
        lane = self.get_lane(x, y)
        
        if tracker_id not in self.vehicles:
            self.vehicles[tracker_id] = {
                'mac': mac,
                'x': x,
                'y': y,
                'lane': lane,
                'speed': speed,
                'speed_lane': None,  # Lane when speed was calculated
                'received_data': []  # Data FROM other vehicles
            }
        else:
            self.vehicles[tracker_id]['x'] = x
            self.vehicles[tracker_id]['y'] = y
            self.vehicles[tracker_id]['lane'] = lane
            
        # When speed is set, save the lane at that moment
        if speed is not None:
            self.vehicles[tracker_id]['speed'] = speed
            self.vehicles[tracker_id]['speed_lane'] = lane  # Save lane when speed was calculated
            if tracker_id not in self.vehicles_with_speed:
                self.vehicles_with_speed.append(tracker_id)
    
    def broadcast_speed(self, sender_id, speed):
        """Broadcast speed to vehicles BEHIND"""
        if sender_id not in self.vehicles:
            print(f"⚠️  WARNING: Vehicle #{sender_id} not in vehicles dict!")
            return
        
        sender = self.vehicles[sender_id]
        sender_pos = (sender['x'], sender['y'])
        sender_lane = sender['lane']
        
        print(f"📡 Vehicle #{sender_id} broadcasting: {speed:.1f} km/h from {sender_lane} at pos {sender_pos}")
        
        recipients_count = 0
        # Send to vehicles BEHIND
        for receiver_id, receiver in self.vehicles.items():
            if receiver_id == sender_id:
                continue
            
            receiver_pos = (receiver['x'], receiver['y'])
            
            # Calculate distance
            distance = math.sqrt((sender_pos[0] - receiver_pos[0])**2 + 
                               (sender_pos[1] - receiver_pos[1])**2)
            distance_m = distance * self.pixel_to_meter_ratio
            
            # Only send if within 300m range
            if distance_m > 300:
                continue
            
            # Add to receiver's data
            receiver['received_data'].append({
                'from_vehicle_id': sender_id,
                'speed': speed,
                'lane': sender_lane,
                'distance': distance_m,
                'timestamp': time.time()
            })
            
            recipients_count += 1
            print(f"  ✅ Sent to Vehicle #{receiver_id} (distance: {distance_m:.1f}m)")
        
        print(f"  📊 Total recipients: {recipients_count}")
        
        # Clean old data
        current_time = time.time()
        for vehicle in self.vehicles.values():
            before_count = len(vehicle['received_data'])
            vehicle['received_data'] = [
                d for d in vehicle['received_data']
                if current_time - d['timestamp'] < 10.0
            ]
            after_count = len(vehicle['received_data'])
            if before_count != after_count:
                print(f"  🧹 Cleaned {before_count - after_count} old messages")
    
    def get_latest_vehicle_with_speed(self):
        """Get most recent vehicle that calculated speed"""
        if not self.vehicles_with_speed:
            return None
        return self.vehicles_with_speed[-1]


def draw_video_area(frame, vanet, red_line_y, blue_line_y):
    """Draw video area - 70% of screen"""
    video_width = 714  # 70% of 1020
    
    # Create video section
    video_section = frame[:, :video_width].copy()
    
    # Draw timing lines with labels (RED and BLUE)
    cv2.line(video_section, (0, red_line_y), (video_width, red_line_y), (0, 0, 255), 3)
    cv2.line(video_section, (0, blue_line_y), (video_width, blue_line_y), (255, 0, 0), 3)
    
    # Line labels
    cv2.putText(video_section, "RED Line (y=198)", (10, red_line_y - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
    cv2.putText(video_section, "BLUE Line (y=268)", (10, blue_line_y + 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
    
    # Draw vehicles
    for tracker_id, vehicle_data in vanet.vehicles.items():
        x = int(vehicle_data['x'])
        y = int(vehicle_data['y'])
        
        if x > video_width:
            continue
        
        # Green box
        cv2.rectangle(video_section, (x - 20, y - 20), (x + 20, y + 20), (0, 255, 0), 2)
        
        # Vehicle ID
        cv2.putText(video_section, f"#{tracker_id}", (x - 15, y - 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        
        # Speed if calculated
        if vehicle_data.get('speed'):
            speed_text = f"{vehicle_data['speed']:.0f} km/h"
            cv2.putText(video_section, speed_text, (x - 40, y + 35),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 2)
    
    return video_section


def draw_dashboard(vanet, frame_count, counter_down, counter_up):
    """Draw dashboard - 30% of screen, split into UPPER and LOWER"""
    panel_width = 306  # 30% of 1020
    panel_height = 500
    
    # Create dark background
    dashboard = np.zeros((panel_height, panel_width, 3), dtype=np.uint8)
    dashboard[:] = (40, 40, 40)
    
    # Title bar
    cv2.rectangle(dashboard, (0, 0), (panel_width, 35), (0, 100, 200), -1)
    cv2.putText(dashboard, "VANET DASHBOARD", (10, 23),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
    # Get current vehicle (last one that crossed 2nd line)
    current_id = vanet.get_latest_vehicle_with_speed()
    
    # ========== UPPER PART: CURRENT VEHICLE ==========
    upper_start_y = 40
    upper_height = 220
    
    cv2.rectangle(dashboard, (0, upper_start_y), (panel_width, upper_start_y + upper_height), (50, 50, 50), -1)
    cv2.rectangle(dashboard, (0, upper_start_y), (panel_width, upper_start_y + upper_height), (0, 255, 255), 2)
    
    y_pos = upper_start_y + 25
    cv2.putText(dashboard, "CURRENT VEHICLE", (10, y_pos),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
    y_pos += 5
    cv2.line(dashboard, (10, y_pos), (panel_width - 10, y_pos), (0, 255, 255), 1)
    y_pos += 20
    
    if current_id is None or current_id not in vanet.vehicles:
        cv2.putText(dashboard, "Waiting for vehicle", (15, y_pos),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (150, 150, 150), 1)
        y_pos += 20
        cv2.putText(dashboard, "to cross 2nd line...", (15, y_pos),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (150, 150, 150), 1)
    else:
        vehicle_data = vanet.vehicles[current_id]
        
        # Vehicle ID
        cv2.putText(dashboard, f"Vehicle ID: #{current_id}", (15, y_pos),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        y_pos += 25
        
        # MAC Address
        mac = vehicle_data['mac']
        cv2.putText(dashboard, f"MAC: {mac}", (15, y_pos),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
        y_pos += 22
        
        # Speed
        speed = vehicle_data.get('speed', 0)
        cv2.putText(dashboard, f"Speed: {speed:.1f} km/h", (15, y_pos),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        y_pos += 25
        
        # Lane (use speed_lane - the lane when speed was calculated)
        lane = vehicle_data.get('speed_lane', 'UNKNOWN')
        if lane is None:
            lane = vehicle_data.get('lane', 'UNKNOWN')
        cv2.putText(dashboard, f"Lane: {lane}", (15, y_pos),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 0), 1)
        y_pos += 22
        
        # Direction - determine from which counter the vehicle is in
        direction = "UNKNOWN"
        if current_id in counter_down:
            direction = "DOWN"
        elif current_id in counter_up:
            direction = "UP"
        cv2.putText(dashboard, f"Direction: {direction}", (15, y_pos),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 0), 1)
    
    # ========== LOWER PART: PREVIOUS 3 VEHICLES THAT CROSSED ==========
    lower_start_y = upper_start_y + upper_height + 5
    lower_height = panel_height - lower_start_y - 5
    
    cv2.rectangle(dashboard, (0, lower_start_y), (panel_width, panel_height - 5), (50, 50, 50), -1)
    cv2.rectangle(dashboard, (0, lower_start_y), (panel_width, panel_height - 5), (0, 255, 100), 2)
    
    y_pos = lower_start_y + 25
    cv2.putText(dashboard, "PREVIOUS VEHICLES", (10, y_pos),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 100), 2)
    y_pos += 5
    cv2.line(dashboard, (10, y_pos), (panel_width - 10, y_pos), (0, 255, 100), 1)
    y_pos += 15
    
    cv2.putText(dashboard, "(Last 3 that crossed)", (15, y_pos),
                cv2.FONT_HERSHEY_SIMPLEX, 0.35, (150, 150, 150), 1)
    y_pos += 20
    
    # Get list of all vehicles with speed (in order they calculated)
    vehicles_with_speed = vanet.vehicles_with_speed
    
    if current_id is not None and current_id in vehicles_with_speed:
        # Find index of current vehicle
        current_index = vehicles_with_speed.index(current_id)
        
        # Get previous 3 vehicles (or less if not enough)
        previous_vehicles = []
        for i in range(1, 4):  # Get up to 3 previous
            prev_index = current_index - i
            if prev_index >= 0:
                previous_vehicles.append(vehicles_with_speed[prev_index])
        
        if previous_vehicles:
            # Get current vehicle position for distance calculation
            current_vehicle = vanet.vehicles[current_id]
            current_x = current_vehicle['x']
            current_y = current_vehicle['y']
            
            for prev_id in previous_vehicles:
                if prev_id not in vanet.vehicles:
                    continue
                
                prev_vehicle = vanet.vehicles[prev_id]
                prev_x = prev_vehicle['x']
                prev_y = prev_vehicle['y']
                prev_speed = prev_vehicle.get('speed', 0)
                
                # Use speed_lane (lane when speed was calculated), not current lane
                prev_lane = prev_vehicle.get('speed_lane', 'Unknown')
                if prev_lane is None:
                    prev_lane = prev_vehicle.get('lane', 'Unknown')
                
                # Calculate distance using YOLO positions
                distance_pixels = math.sqrt((current_x - prev_x)**2 + (current_y - prev_y)**2)
                distance_m = distance_pixels * vanet.pixel_to_meter_ratio
                
                # Color by distance
                if distance_m < 30:
                    color = (0, 0, 255)  # Red - close
                elif distance_m < 70:
                    color = (0, 255, 255)  # Yellow - medium
                else:
                    color = (0, 255, 0)  # Green - far
                
                # Vehicle ID
                cv2.putText(dashboard, f"Vehicle #{prev_id}", (15, y_pos),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1)
                y_pos += 18
                
                # Lane
                cv2.putText(dashboard, f"  Lane: {prev_lane}", (15, y_pos),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.38, color, 1)
                y_pos += 16
                
                # Distance
                cv2.putText(dashboard, f"  Distance: {distance_m:.0f}m", (15, y_pos),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.38, color, 1)
                y_pos += 16
                
                # Speed
                cv2.putText(dashboard, f"  Speed: {prev_speed:.0f} km/h", (15, y_pos),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.38, color, 1)
                y_pos += 20
                
                if y_pos > panel_height - 20:
                    break
        else:
            cv2.putText(dashboard, "No previous vehicles", (15, y_pos),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (150, 150, 150), 1)
    else:
        cv2.putText(dashboard, "Waiting for vehicles", (15, y_pos),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (150, 150, 150), 1)
    
    return dashboard


def main():
    # Open video
    cap = cv2.VideoCapture('highway_mini.mp4')
    
    if not cap.isOpened():
        print("❌ Error: Could not open video file 'highway_mini.mp4'")
        return
    
    # Initialize
    tracker = Tracker()
    vanet = CleanVANET(communication_range=180)
    
    # Speed calculation variables - DUAL LINE TIMING METHOD (WORKING)
    red_line_y = 198    # First line
    blue_line_y = 268    # Second line
    offset = 7
    
    # Timing dictionaries (same as original car_speed_estimator.py)
    down = {}  # DOWN direction: RED→BLUE
    up = {}    # UP direction: BLUE→RED
    counter_down = []  # Track which vehicles already calculated (DOWN)
    counter_up = []    # Track which vehicles already calculated (UP)
    
    # Control variables
    count = 0
    auto_play = True  # START IN AUTO MODE - changed from False
    
    print("=" * 70)
    print("🚗 VANET CLEAN PRESENTATION MODE - FIXED VERSION")
    print("=" * 70)
    print("📊 Layout: 70% Video + 30% Dashboard (UPPER + LOWER)")
    print("📍 UPPER: Current vehicle (just crossed 2nd line)")
    print("📍 LOWER: Data from previous vehicles")
    print("🎮 Controls:")
    print("   SPACE - Pause/Resume")
    print("   'p' - Toggle Auto/Manual playback")
    print("   ESC - Exit")
    print("=" * 70)
    print("✅ Starting in AUTO mode - video will play automatically")
    print("=" * 70)
    
    # Read first frame to show window
    ret, frame = cap.read()
    if not ret:
        print("❌ Error: Could not read video file")
        return
    
    while True:
        if auto_play:
            if count > 0:  # Don't read twice on first frame
                ret, frame = cap.read()
            key = cv2.waitKey(30) & 0xFF
        else:
            # Manual mode - show current frame first
            if count == 0:
                # Process and show first frame before waiting
                count += 1
                frame_display = cv2.resize(frame, (1020, 500))
                
                # Create display frame
                display = np.zeros((500, 1700, 3), dtype=np.uint8)
                display[:, :1020] = frame_display
                
                # Simple start message
                cv2.putText(display, "Press SPACE to start", (50, 250),
                           cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)
                
                cv2.imshow('VANET Clean Presentation', display)
            
            key = cv2.waitKey(0) & 0xFF
            if key == 32:  # SPACE
                ret, frame = cap.read()
                if not ret:
                    break
            elif key == ord('p'):
                auto_play = True
                print("▶️  AUTO mode activated")
                continue
            elif key == 27:  # ESC
                break
            else:
                continue
        
        if not ret:
            print("\n✅ End of video")
            break
        
        if count > 0:  # Skip first frame processing since we already showed it
            count += 1
        frame = cv2.resize(frame, (1020, 500))
        
        # Detection
        results = model.predict(frame, verbose=False)
        a = results[0].boxes.data
        a = a.detach().cpu().numpy()
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
        
        # Process each vehicle - EXACT SAME LOGIC AS car_speed_estimator.py
        for bbox in bbox_id:
            x3, y3, x4, y4, tracker_id = bbox
            cx = (x3 + x4) // 2
            cy = (y3 + y4) // 2
            
            # Add/update vehicle in VANET (without speed yet)
            vanet.add_vehicle(tracker_id, cx, cy)
            
            # DOWN direction: RED line → BLUE line
            if red_line_y < (cy + offset) and red_line_y > (cy - offset):
                down[tracker_id] = time.time()
            
            if tracker_id in down:
                if blue_line_y < (cy + offset) and blue_line_y > (cy - offset):
                    elapsed_time = time.time() - down[tracker_id]
                    if counter_down.count(tracker_id) == 0:
                        counter_down.append(tracker_id)
                        distance = 100
                        speed_ms = distance / elapsed_time
                        speed_kmh = speed_ms * 3.6
                        
                        vanet.add_vehicle(tracker_id, cx, cy, speed_kmh)
                        vanet.broadcast_speed(tracker_id, speed_kmh)
                        
                        lane = vanet.vehicles[tracker_id]['lane']
                        print(f"✅ DOWN Vehicle #{tracker_id} | Speed: {speed_kmh:.1f} km/h | {lane} | Pos: ({cx}, {cy})")
            
            # UP direction: BLUE line → RED line
            if blue_line_y < (cy + offset) and blue_line_y > (cy - offset):
                up[tracker_id] = time.time()
            
            if tracker_id in up:
                if red_line_y < (cy + offset) and red_line_y > (cy - offset):
                    elapsed_time = time.time() - up[tracker_id]
                    if counter_up.count(tracker_id) == 0:
                        counter_up.append(tracker_id)
                        distance = 100
                        speed_ms = distance / elapsed_time
                        speed_kmh = speed_ms * 3.6
                        
                        vanet.add_vehicle(tracker_id, cx, cy, speed_kmh)
                        vanet.broadcast_speed(tracker_id, speed_kmh)
                        
                        lane = vanet.vehicles[tracker_id]['lane']
                        print(f"✅ UP Vehicle #{tracker_id} | Speed: {speed_kmh:.1f} km/h | {lane} | Pos: ({cx}, {cy})")
        
        # Draw video area with RED and BLUE lines
        video_area = draw_video_area(frame, vanet, red_line_y, blue_line_y)
        
        # Draw dashboard (right 30%)
        dashboard = draw_dashboard(vanet, count, counter_down, counter_up)
        
        # Combine both sides
        combined = np.hstack([video_area, dashboard])
        
        # Add header
        header_height = 30
        header = np.zeros((header_height, 1020, 3), dtype=np.uint8)
        header[:] = (50, 50, 50)
        
        mode_text = "AUTO" if auto_play else "MANUAL"
        cv2.putText(header, f"Frame: {count}", (10, 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(header, f"Mode: {mode_text}", (150, 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0) if auto_play else (0, 255, 255), 1)
        cv2.putText(header, "[SPACE] Next  [P] Auto/Manual  [ESC] Exit", (350, 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
        
        final_frame = np.vstack([header, combined])
        
        # Display
        cv2.imshow('VANET Clean Presentation', final_frame)
        
        # Handle keys in auto mode
        if auto_play:
            if key == ord('p'):
                auto_play = False
                print("⏸️  MANUAL mode activated - Press SPACE for next frame")
            elif key == 27:  # ESC
                break
    
    cap.release()
    cv2.destroyAllWindows()
    print("\n" + "=" * 70)
    print("✅ Demo completed successfully!")
    print("=" * 70)


if __name__ == "__main__":
    main()
