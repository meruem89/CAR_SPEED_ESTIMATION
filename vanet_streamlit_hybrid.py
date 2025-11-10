# -*- coding: utf-8 -*-
"""
VANET Hybrid Version - Frame-by-Frame with Streamlit Display
Combines OpenCV keyboard control with Streamlit visualization
"""

import cv2
from ultralytics import YOLO
from tracker import Tracker
import pandas as pd
import numpy as np
import time
import math
import hashlib

# MAC address generation
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
        self.communication_range = 300
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

# Draw dashboard on frame
def draw_dashboard(frame, vanet, counter_down, counter_up, current_id):
    h, w = frame.shape[:2]
    dashboard_x = int(w * 0.7)  # 70% for video, 30% for dashboard
    
    # Draw vertical separator
    cv2.line(frame, (dashboard_x, 0), (dashboard_x, h), (255, 255, 255), 2)
    
    # Dashboard background
    cv2.rectangle(frame, (dashboard_x, 0), (w, h), (40, 40, 40), -1)
    
    # Header
    cv2.putText(frame, 'VANET Dashboard', (dashboard_x + 20, 30),
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    y_offset = 70
    
    if current_id is not None and current_id in vanet.vehicles:
        current = vanet.vehicles[current_id]
        
        # Current Vehicle Section
        cv2.putText(frame, 'Current Vehicle:', (dashboard_x + 10, y_offset),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
        y_offset += 25
        
        cv2.putText(frame, f"ID: #{current_id}", (dashboard_x + 10, y_offset),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        y_offset += 20
        
        cv2.putText(frame, f"MAC: {current['mac'][:17]}", (dashboard_x + 10, y_offset),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255, 255, 255), 1)
        y_offset += 20
        
        if current['speed']:
            cv2.putText(frame, f"Speed: {int(current['speed'])} km/h", (dashboard_x + 10, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
            y_offset += 20
        
        cv2.putText(frame, f"Lane: {current['speed_lane']}", (dashboard_x + 10, y_offset),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        y_offset += 20
        
        direction = 'DOWN' if current_id in counter_down else 'UP'
        cv2.putText(frame, f"Direction: {direction}", (dashboard_x + 10, y_offset),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        y_offset += 35
        
        # Previous Vehicles
        cv2.putText(frame, 'Previous Vehicles:', (dashboard_x + 10, y_offset),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
        y_offset += 25
        
        previous_ids = vanet.get_previous_vehicles(current_id, 3)
        
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
                    color = (0, 0, 255)  # Red
                elif distance_meters < 70:
                    color = (0, 255, 255)  # Yellow
                else:
                    color = (0, 255, 0)  # Green
                
                cv2.putText(frame, f"Vehicle #{prev_id}", (dashboard_x + 10, y_offset),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
                y_offset += 18
                
                cv2.putText(frame, f"  {prev['speed_lane']} | {int(distance_meters)}m | {int(prev['speed'])}km/h",
                           (dashboard_x + 10, y_offset),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255, 255, 255), 1)
                y_offset += 20
        else:
            cv2.putText(frame, 'No previous vehicles', (dashboard_x + 10, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (128, 128, 128), 1)
            y_offset += 25
    
    # Statistics
    y_offset = h - 100
    cv2.putText(frame, 'Statistics:', (dashboard_x + 10, y_offset),
               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
    y_offset += 25
    
    total_vehicles = len(counter_down) + len(counter_up)
    cv2.putText(frame, f"Total: {total_vehicles} | DOWN: {len(counter_down)} | UP: {len(counter_up)}",
               (dashboard_x + 10, y_offset),
               cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255, 255, 255), 1)
    
    return frame

# Main function
def main():
    print("=" * 60)
    print(" VANET Frame-by-Frame Analysis")
    print("=" * 60)
    print("\nControls:")
    print("  SPACEBAR - Pause/Resume")
    print("  Q - Quit")
    print("\nStarting...\n")
    
    # Load YOLO model
    model = YOLO('yolov8n.pt')
    
    # Class list
    class_list = ['person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck']
    
    # Initialize
    tracker = Tracker()
    vanet = CleanVANET()
    
    down = {}
    up = {}
    counter_down = []
    counter_up = []
    
    red_line_y = 198
    blue_line_y = 268
    offset = 7
    
    # Open video
    cap = cv2.VideoCapture('highway_mini.mp4')
    
    if not cap.isOpened():
        print("Error: Could not open video file!")
        return
    
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    
    print(f"Video: {total_frames} frames @ {fps} FPS")
    print("Processing started...\n")
    
    # Create window
    window_name = 'VANET Analysis (SPACE=Pause, Q=Quit)'
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, 1400, 700)
    
    frame_count = 0
    paused = False
    
    while cap.isOpened():
        if not paused:
            ret, frame = cap.read()
            if not ret:
                print("\nVideo processing complete!")
                break
            
            frame_count += 1
            
            # Resize frame
            frame_resized = cv2.resize(frame, (1020, 500))
            
            # YOLO detection
            results = model.predict(frame_resized)
            detections = results[0].boxes.data
            px = pd.DataFrame(detections).astype("float")
            
            # Filter vehicles
            vehicle_list = []
            for index, row in px.iterrows():
                x1, y1, x2, y2, _, d = int(row[0]), int(row[1]), int(row[2]), int(row[3]), int(row[4]), int(row[5])
                c = class_list[d] if d < len(class_list) else 'unknown'
                if 'car' in c or 'truck' in c or 'bus' in c:
                    vehicle_list.append([x1, y1, x2, y2])
            
            # Track vehicles
            bbox_id = tracker.update(vehicle_list)
            
            # Process each tracked vehicle
            for bbox in bbox_id:
                x3, y3, x4, y4, tracker_id = bbox
                cx, cy = (x3 + x4) // 2, (y3 + y4) // 2
                
                vanet.add_vehicle(tracker_id, cx, cy)
                
                # Speed calculation - DOWN
                if red_line_y < (cy + offset) and red_line_y > (cy - offset):
                    down[tracker_id] = time.time()
                
                if tracker_id in down:
                    if blue_line_y < (cy + offset) and blue_line_y > (cy - offset):
                        elapsed_time = time.time() - down[tracker_id]
                        if counter_down.count(tracker_id) == 0:
                            counter_down.append(tracker_id)
                            speed_kmh = (100 / elapsed_time) * 3.6
                            vanet.add_vehicle(tracker_id, cx, cy, speed_kmh)
                            vanet.broadcast_speed(tracker_id, speed_kmh)
                
                # Speed calculation - UP
                if blue_line_y < (cy + offset) and blue_line_y > (cy - offset):
                    up[tracker_id] = time.time()
                
                if tracker_id in up:
                    if red_line_y < (cy + offset) and red_line_y > (cy - offset):
                        elapsed_time = time.time() - up[tracker_id]
                        if counter_up.count(tracker_id) == 0:
                            counter_up.append(tracker_id)
                            speed_kmh = (100 / elapsed_time) * 3.6
                            vanet.add_vehicle(tracker_id, cx, cy, speed_kmh)
                            vanet.broadcast_speed(tracker_id, speed_kmh)
                
                # Draw bounding box
                cv2.rectangle(frame_resized, (x3, y3), (x4, y4), (0, 255, 0), 2)
                cv2.putText(frame_resized, f'ID:{tracker_id}', (x3, y3-10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
                
                if tracker_id in vanet.vehicles and vanet.vehicles[tracker_id]['speed']:
                    speed = vanet.vehicles[tracker_id]['speed']
                    cv2.putText(frame_resized, f'{int(speed)}km/h', (x3, y4+20),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
            
            # Draw lines
            cv2.line(frame_resized, (0, red_line_y), (714, red_line_y), (0, 0, 255), 2)
            cv2.putText(frame_resized, 'RED LINE', (10, red_line_y-10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            
            cv2.line(frame_resized, (0, blue_line_y), (714, blue_line_y), (255, 0, 0), 2)
            cv2.putText(frame_resized, 'BLUE LINE', (10, blue_line_y+25),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
            
            # Draw counters
            cv2.putText(frame_resized, f'DOWN: {len(counter_down)}', (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(frame_resized, f'UP: {len(counter_up)}', (10, 60),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Create full frame with dashboard (70% video + 30% dashboard)
            full_frame = np.zeros((500, 1440, 3), dtype=np.uint8)
            full_frame[:, :1020] = frame_resized
            
            # Get current vehicle and draw dashboard
            current_id = vanet.get_latest_vehicle_with_speed()
            full_frame = draw_dashboard(full_frame, vanet, counter_down, counter_up, current_id)
            
            # Add progress bar
            progress_width = 1400
            progress_height = 20
            progress_y = 680
            cv2.rectangle(full_frame, (20, progress_y), (20 + progress_width, progress_y + progress_height),
                         (60, 60, 60), -1)
            filled_width = int((frame_count / total_frames) * progress_width)
            cv2.rectangle(full_frame, (20, progress_y), (20 + filled_width, progress_y + progress_height),
                         (0, 255, 0), -1)
            cv2.putText(full_frame, f'Frame: {frame_count}/{total_frames}', (20, progress_y - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # Display
            cv2.imshow(window_name, full_frame)
        
        # Keyboard control
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord(' '):  # Spacebar
            paused = not paused
            if paused:
                print(f"\n⏸️  PAUSED at frame {frame_count}/{total_frames}")
                print("   Press SPACEBAR to resume, Q to quit")
            else:
                print(f"▶️  RESUMED from frame {frame_count}")
        
        elif key == ord('q') or key == ord('Q'):
            print("\n🛑 Stopping...")
            break
    
    cap.release()
    cv2.destroyAllWindows()
    print("\n✅ Processing complete!")
    print(f"   Total vehicles: {len(counter_down) + len(counter_up)}")
    print(f"   DOWN: {len(counter_down)} | UP: {len(counter_up)}")

if __name__ == "__main__":
    main()
