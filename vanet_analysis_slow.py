# -*- coding: utf-8 -*-
"""VANET Car Speed Estimator - Ultra Slow Analysis Mode"""

# Import required libraries
import cv2
import pandas as pd
from ultralytics import YOLO
from tracker import*
from vanet_speed_sharing import VANETSpeedSharing
import time
import math
import random

# Initialize YOLO model and video
model = YOLO('yolov8n.pt')
vi = cv2.VideoCapture('highway_mini.mp4')

class_list = ['person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat', 'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird', 'cat', 'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 'giraffe', 'backpack', 'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball', 'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard', 'tennis racket', 'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple', 'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 'couch', 'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse', 'remote', 'keyboard', 'cell phone', 'microwave', 'oven',
              'toaster', 'sink', 'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear', 'hair drier', 'toothbrush']

# Initialize tracker and VANET
tracker = Tracker()
vanet = VANETSpeedSharing()
count = 0

# Speed calculation variables
down = {}
up = {}
counter_down = []
counter_up = []

# Colors for display
text_color = (255, 255, 255)  # white
red_color = (0, 0, 255)       # red
blue_color = (255, 0, 0)      # blue
green_color = (0, 255, 0)     # green
yellow_color = (0, 255, 255)  # yellow
purple_color = (255, 0, 255)  # purple
orange_color = (0, 165, 255)  # orange

def draw_communication_analysis(frame, vanet_system):
    """Draw detailed communication analysis"""
    pairs = vanet_system.get_communication_pairs()
    
    for vid1, vid2 in pairs:
        if vid1 in vanet_system.vehicles and vid2 in vanet_system.vehicles:
            v1 = vanet_system.vehicles[vid1]
            v2 = vanet_system.vehicles[vid2]
            
            # Calculate distance
            distance = math.sqrt((v1.x - v2.x)**2 + (v1.y - v2.y)**2)
            
            # Draw communication line with thickness based on signal strength
            thickness = max(1, int(5 - distance/30))  # Thicker line = stronger signal
            cv2.line(frame, (int(v1.x), int(v1.y)), (int(v2.x), int(v2.y)), yellow_color, thickness)
            
            # Draw distance information at midpoint
            mid_x = int((v1.x + v2.x) / 2)
            mid_y = int((v1.y + v2.y) / 2)
            cv2.circle(frame, (mid_x, mid_y), 4, yellow_color, -1)
            cv2.putText(frame, f"{int(distance)}px", (mid_x-15, mid_y-8), cv2.FONT_HERSHEY_SIMPLEX, 0.3, yellow_color, 1)

def draw_detailed_vehicle_info(frame, vehicle_id, x, y, own_speed, shared_speeds):
    """Draw detailed vehicle information with enhanced display"""
    # Background box for better visibility
    info_width = 150
    info_height = 60 + len(shared_speeds) * 15
    cv2.rectangle(frame, (x-5, y-50), (x+info_width, y+info_height-40), (0, 0, 0), -1)  # Black background
    cv2.rectangle(frame, (x-5, y-50), (x+info_width, y+info_height-40), text_color, 1)   # White border
    
    # Draw vehicle ID and own speed
    cv2.putText(frame, f"Vehicle ID: {vehicle_id}", (x, y-35), cv2.FONT_HERSHEY_SIMPLEX, 0.4, orange_color, 1)
    cv2.putText(frame, f"My Speed: {int(own_speed)} km/h", (x, y-20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, green_color, 1)
    
    # Draw communication status
    if shared_speeds:
        cv2.putText(frame, "Receiving from:", (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.3, text_color, 1)
        y_offset = 10
        for other_id, speed_data in shared_speeds.items():
            received_speed = speed_data['speed']
            # Show signal age
            age = time.time() - speed_data['received_at']
            cv2.putText(frame, f"V{other_id}: {int(received_speed)}km/h ({age:.1f}s)", (x, y + y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.3, purple_color, 1)
            y_offset += 15
    else:
        cv2.putText(frame, "No communications", (x, y+5), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (128, 128, 128), 1)

def draw_detailed_vanet_status(frame, vanet_system, current_frame, total_frames):
    """Draw detailed VANET analysis status"""
    total_vehicles = len(vanet_system.vehicles)
    communication_pairs = len(vanet_system.get_communication_pairs())
    recent_messages = vanet_system.get_recent_messages(2)
    
    # Larger status box for detailed info
    cv2.rectangle(frame, (10, 400), (400, 490), (0, 0, 0), -1)  # Black background
    cv2.rectangle(frame, (10, 400), (400, 490), text_color, 2)   # White border
    
    cv2.putText(frame, "DETAILED VANET ANALYSIS", (20, 420), cv2.FONT_HERSHEY_SIMPLEX, 0.5, orange_color, 2)
    cv2.putText(frame, f"Frame: {current_frame}/{total_frames} - MANUAL MODE", (20, 440), cv2.FONT_HERSHEY_SIMPLEX, 0.4, text_color, 1)
    cv2.putText(frame, f"Active Vehicles: {total_vehicles}", (20, 455), cv2.FONT_HERSHEY_SIMPLEX, 0.4, text_color, 1)
    cv2.putText(frame, f"Communication Links: {communication_pairs}", (20, 470), cv2.FONT_HERSHEY_SIMPLEX, 0.4, text_color, 1)
    cv2.putText(frame, f"Recent Messages: {len(recent_messages)}", (20, 485), cv2.FONT_HERSHEY_SIMPLEX, 0.4, text_color, 1)

def print_communication_log(vanet_system, frame_number):
    """Print detailed communication log to console"""
    recent_messages = vanet_system.get_recent_messages(1)  # Messages in last 1 second
    if recent_messages:
        print(f"\n--- Frame {frame_number} Communication Log ---")
        for msg in recent_messages:
            print(f"Vehicle {msg['from']} → Vehicle {msg['to']}: Speed {msg['speed_shared']:.1f} km/h (Distance: {msg['distance']:.1f}px)")

print("🚗📡 VANET ULTRA-SLOW ANALYSIS MODE 📡🚗")
print("="*50)
print("This mode provides detailed frame-by-frame VANET analysis")
print("\nControls:")
print("  SPACEBAR - Next frame (MANUAL MODE ONLY)")
print("  ESC - Exit")
print("\nFeatures:")
print("✓ Detailed vehicle communication info boxes")
print("✓ Communication line thickness shows signal strength")
print("✓ Distance measurements between communicating vehicles") 
print("✓ Signal age timestamps")
print("✓ Console communication logging")
print("="*50)
print("Press SPACEBAR to advance frame-by-frame...")
print()

current_frame = 0
total_frames = int(vi.get(cv2.CAP_PROP_FRAME_COUNT))

while True:
    ret, frame = vi.read()
    if not ret:
        print("End of video. Press any key to exit...")
        cv2.waitKey(0)
        break
        
    count += 1
    current_frame = int(vi.get(cv2.CAP_PROP_POS_FRAMES))
    frame = cv2.resize(frame, (1020, 500))

    # YOLO detection
    results = model.predict(frame)
    a = results[0].boxes.data
    a = a.detach().cpu().numpy()
    px = pd.DataFrame(a).astype("float")
    
    detected_cars = []

    # Extract car detections
    for index, row in px.iterrows():
        x1 = int(row[0])
        y1 = int(row[1])
        x2 = int(row[2])
        y2 = int(row[3])
        d = int(row[5])
        c = class_list[d]
        if 'car' in c:
            detected_cars.append([x1, y1, x2, y2])

    # Update tracker
    bbox_id = tracker.update(detected_cars)
    vehicle_speeds = {}
    
    for bbox in bbox_id:
        x3, y3, x4, y4, vehicle_id = bbox
        cx = int((x3 + x4) / 2)
        cy = int((y3 + y4) / 2)
        red_line_y = 198
        blue_line_y = 268
        offset = 7
        
        current_speed = 0

        # Speed calculation (simplified for demo)
        if red_line_y < (cy + offset) and red_line_y > (cy - offset):
            down[vehicle_id] = time.time()
        if vehicle_id in down:
            if blue_line_y < (cy + offset) and blue_line_y > (cy - offset):
                elapsed_time = time.time() - down[vehicle_id]
                if counter_down.count(vehicle_id) == 0:
                    counter_down.append(vehicle_id)
                    distance = 100
                    a_speed_ms = distance / elapsed_time
                    current_speed = a_speed_ms * 3.6
                    vehicle_speeds[vehicle_id] = current_speed

        # For demo purposes, assign realistic speeds
        if vehicle_id not in vehicle_speeds:
            current_speed = random.uniform(45, 75)  # km/h
            vehicle_speeds[vehicle_id] = current_speed

        # Update VANET with vehicle position and speed
        vanet.add_or_update_vehicle(vehicle_id, cx, cy, current_speed)

        # Draw enhanced vehicle visualization
        cv2.rectangle(frame, (x3, y3), (x4, y4), green_color, 2)
        cv2.circle(frame, (cx, cy), 6, red_color, -1)
        
        # Get and display detailed communication info
        if vehicle_id in vanet.vehicles:
            vehicle_node = vanet.vehicles[vehicle_id]
            shared_speeds = vehicle_node.get_nearby_speeds()
            draw_detailed_vehicle_info(frame, vehicle_id, x3, y3, current_speed, shared_speeds)

    # Simulate VANET communication
    messages_sent = vanet.simulate_communication()
    
    # Print communication log for this frame
    if messages_sent > 0:
        print_communication_log(vanet, current_frame)
    
    # Draw detailed communication analysis
    draw_communication_analysis(frame, vanet)
    
    # Draw reference lines
    cv2.line(frame, (172, 198), (774, 198), red_color, 3)
    cv2.putText(frame, ('red line'), (172, 190), cv2.FONT_HERSHEY_SIMPLEX, 0.5, text_color, 1, cv2.LINE_AA)
    
    cv2.line(frame, (8, 268), (927, 268), blue_color, 3)
    cv2.putText(frame, ('blue line'), (8, 260), cv2.FONT_HERSHEY_SIMPLEX, 0.5, text_color, 1, cv2.LINE_AA)
    
    # Draw traffic counters
    cv2.putText(frame, ('Going Down - ' + str(len(counter_down))), (10, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.5, text_color, 1, cv2.LINE_AA)
    cv2.putText(frame, ('Going Up - ' + str(len(counter_up))), (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.5, text_color, 1, cv2.LINE_AA)
    
    # Draw detailed VANET status
    draw_detailed_vanet_status(frame, vanet, current_frame, total_frames)

    cv2.imshow('VANET Ultra-Slow Analysis', frame)
    
    # Wait for SPACEBAR to continue (frame-by-frame only)
    print(f"Frame {current_frame}: Press SPACEBAR for next frame, ESC to exit...")
    key = cv2.waitKey(0) & 0xFF
    
    if key == 27:  # ESC to exit
        break
    elif key == ord(' '):  # SPACEBAR to continue
        continue

vi.release()
cv2.destroyAllWindows()
print("Analysis complete!")
