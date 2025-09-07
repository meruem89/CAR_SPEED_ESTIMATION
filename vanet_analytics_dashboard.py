# -*- coding: utf-8 -*-
"""
VANET Analytics Dashboard - Professional Implementation
Real-time analytics and performance metrics for project presentations
"""

import cv2
import pandas as pd
from ultralytics import YOLO
from tracker import*
from vanet_speed_sharing import VANETSpeedSharing
import time
import math
import numpy as np
import json
from datetime import datetime
import matplotlib.pyplot as plt
from collections import defaultdict, deque

class VANETAnalytics:
    def __init__(self):
        self.start_time = time.time()
        self.frame_count = 0
        
        # Performance Metrics
        self.processing_times = deque(maxlen=100)
        self.detection_counts = deque(maxlen=100)
        self.communication_counts = deque(maxlen=100)
        
        # Traffic Analytics
        self.speed_history = defaultdict(list)
        self.vehicle_classifications = defaultdict(int)
        self.communication_matrix = {}
        
        # Network Metrics
        self.message_success_rate = []
        self.network_density = []
        self.average_speeds = []
        
        # Real-time Statistics
        self.current_stats = {
            'total_vehicles_detected': 0,
            'active_communications': 0,
            'average_speed': 0,
            'network_efficiency': 0,
            'processing_fps': 0
        }
        
    def update_performance(self, processing_time, detections, communications):
        """Update real-time performance metrics"""
        self.frame_count += 1
        self.processing_times.append(processing_time)
        self.detection_counts.append(detections)
        self.communication_counts.append(communications)
        
        # Calculate FPS
        if len(self.processing_times) > 0:
            avg_time = np.mean(self.processing_times)
            self.current_stats['processing_fps'] = 1.0 / avg_time if avg_time > 0 else 0
    
    def update_traffic_metrics(self, vehicles_data, speeds):
        """Update traffic analysis metrics"""
        if speeds:
            current_avg = np.mean([s for s in speeds.values() if s > 0])
            self.average_speeds.append(current_avg)
            self.current_stats['average_speed'] = current_avg
        
        self.current_stats['total_vehicles_detected'] = len(vehicles_data)
        
        # Network density calculation
        if len(vehicles_data) > 1:
            positions = [(v['x'], v['y']) for v in vehicles_data.values()]
            distances = []
            for i, pos1 in enumerate(positions):
                for pos2 in positions[i+1:]:
                    dist = math.sqrt((pos1[0]-pos2[0])**2 + (pos1[1]-pos2[1])**2)
                    distances.append(dist)
            
            if distances:
                avg_distance = np.mean(distances)
                density = 1000.0 / avg_distance if avg_distance > 0 else 0
                self.network_density.append(density)
    
    def update_communication_metrics(self, messages_sent, total_possible):
        """Update VANET communication efficiency"""
        if total_possible > 0:
            success_rate = messages_sent / total_possible
            self.message_success_rate.append(success_rate)
            self.current_stats['network_efficiency'] = success_rate
        
        self.current_stats['active_communications'] = messages_sent
    
    def export_analytics(self, filename="analytics_report.json"):
        """Export comprehensive analytics report"""
        report = {
            'session_info': {
                'start_time': datetime.fromtimestamp(self.start_time).isoformat(),
                'duration_seconds': time.time() - self.start_time,
                'total_frames': self.frame_count,
                'average_fps': self.current_stats['processing_fps']
            },
            'traffic_metrics': {
                'average_vehicle_speed': float(np.mean(self.average_speeds)) if self.average_speeds else 0,
                'speed_variance': float(np.var(self.average_speeds)) if self.average_speeds else 0,
                'peak_vehicle_count': max(self.detection_counts) if self.detection_counts else 0,
                'network_density_avg': float(np.mean(self.network_density)) if self.network_density else 0
            },
            'communication_metrics': {
                'total_messages': sum(self.communication_counts),
                'average_success_rate': float(np.mean(self.message_success_rate)) if self.message_success_rate else 0,
                'peak_communications': max(self.communication_counts) if self.communication_counts else 0
            },
            'performance_metrics': {
                'average_processing_time': float(np.mean(self.processing_times)) if self.processing_times else 0,
                'min_processing_time': float(np.min(self.processing_times)) if self.processing_times else 0,
                'max_processing_time': float(np.max(self.processing_times)) if self.processing_times else 0
            },
            'current_snapshot': self.current_stats
        }
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        return report

class EnhancedVANET(VANETSpeedSharing):
    def __init__(self):
        super().__init__()
        self.analytics = VANETAnalytics()
        self.message_log = []
        
    def simulate_communication(self):
        """Enhanced communication with analytics tracking"""
        start_time = time.time()
        messages_sent = super().simulate_communication()
        
        # Calculate possible communications
        total_possible = 0
        vehicle_ids = list(self.vehicles.keys())
        for i, vid1 in enumerate(vehicle_ids):
            for vid2 in vehicle_ids[i+1:]:
                if self.vehicles[vid1].can_communicate_with(self.vehicles[vid2]):
                    total_possible += 2  # Bidirectional
        
        self.analytics.update_communication_metrics(messages_sent, total_possible)
        
        # Log message details
        if messages_sent > 0:
            self.message_log.append({
                'timestamp': time.time(),
                'messages_sent': messages_sent,
                'total_possible': total_possible,
                'success_rate': messages_sent / total_possible if total_possible > 0 else 0
            })
        
        return messages_sent

def draw_professional_dashboard(frame, vanet_system, frame_count, processing_time):
    """Draw comprehensive analytics dashboard"""
    height, width = frame.shape[:2]
    
    # Update analytics
    detections = len(vanet_system.vehicles)
    communications = len(vanet_system.get_recent_broadcasts())
    speeds = {vid: v.speed for vid, v in vanet_system.vehicles.items() if v.speed}
    
    vanet_system.analytics.update_performance(processing_time, detections, communications)
    vanet_system.analytics.update_traffic_metrics(vanet_system.vehicles, speeds)
    
    # Main Dashboard Panel
    panel_width = 350
    panel_height = 200
    panel_x = width - panel_width - 10
    panel_y = 10
    
    # Dashboard background
    cv2.rectangle(frame, (panel_x, panel_y), (width-10, panel_y + panel_height), (20, 20, 20), -1)
    cv2.rectangle(frame, (panel_x, panel_y), (width-10, panel_y + panel_height), (0, 255, 255), 2)
    
    # Title
    cv2.putText(frame, "VANET ANALYTICS DASHBOARD", (panel_x + 10, panel_y + 25), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
    
    # Current Statistics
    stats = vanet_system.analytics.current_stats
    y_offset = 50
    line_height = 20
    
    metrics = [
        f"Processing FPS: {stats['processing_fps']:.1f}",
        f"Active Vehicles: {stats['total_vehicles_detected']}",
        f"Communications: {stats['active_communications']}",
        f"Average Speed: {stats['average_speed']:.1f} km/h",
        f"Network Efficiency: {stats['network_efficiency']:.2%}",
        f"Frame: {frame_count}",
        f"Runtime: {time.time() - vanet_system.analytics.start_time:.0f}s"
    ]
    
    for i, metric in enumerate(metrics):
        cv2.putText(frame, metric, (panel_x + 15, panel_y + y_offset + i * line_height), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
    
    # Performance Graph (Mini)
    if len(vanet_system.analytics.processing_times) > 1:
        graph_x = panel_x + 180
        graph_y = panel_y + 60
        graph_w = 150
        graph_h = 60
        
        # Graph background
        cv2.rectangle(frame, (graph_x, graph_y), (graph_x + graph_w, graph_y + graph_h), (40, 40, 40), -1)
        cv2.rectangle(frame, (graph_x, graph_y), (graph_x + graph_w, graph_y + graph_h), (100, 100, 100), 1)
        
        # Plot FPS over time
        fps_data = [1.0/t if t > 0 else 0 for t in list(vanet_system.analytics.processing_times)[-50:]]
        if fps_data:
            max_fps = max(fps_data) if max(fps_data) > 0 else 1
            normalized = [int((fps/max_fps) * graph_h) for fps in fps_data]
            
            for i in range(len(normalized)-1):
                x1 = graph_x + int((i / len(normalized)) * graph_w)
                y1 = graph_y + graph_h - normalized[i]
                x2 = graph_x + int(((i+1) / len(normalized)) * graph_w)
                y2 = graph_y + graph_h - normalized[i+1]
                cv2.line(frame, (x1, y1), (x2, y2), (0, 255, 0), 1)
        
        cv2.putText(frame, "FPS Graph", (graph_x + 5, graph_y + 15), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 255, 255), 1)
    
    # Communication Network Visualization
    network_panel_y = panel_y + panel_height + 20
    network_panel_h = 120
    
    cv2.rectangle(frame, (panel_x, network_panel_y), (width-10, network_panel_y + network_panel_h), (20, 20, 20), -1)
    cv2.rectangle(frame, (panel_x, network_panel_y), (width-10, network_panel_y + network_panel_h), (255, 165, 0), 2)
    
    cv2.putText(frame, "NETWORK TOPOLOGY", (panel_x + 10, network_panel_y + 25), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 165, 0), 2)
    
    # Mini network graph
    if len(vanet_system.vehicles) > 1:
        mini_graph_area = (panel_x + 20, network_panel_y + 35, panel_width - 40, network_panel_h - 50)
        draw_mini_network_topology(frame, vanet_system, mini_graph_area)

def draw_mini_network_topology(frame, vanet_system, area):
    """Draw a miniaturized network topology"""
    x, y, w, h = area
    vehicles = list(vanet_system.vehicles.items())
    
    if len(vehicles) < 2:
        return
    
    # Position vehicles in mini graph
    positions = {}
    for i, (vid, vehicle) in enumerate(vehicles[:8]):  # Limit to 8 for clarity
        angle = (2 * math.pi * i) / len(vehicles)
        px = x + w//2 + int((w//3) * math.cos(angle))
        py = y + h//2 + int((h//3) * math.sin(angle))
        positions[vid] = (px, py)
        
        # Draw vehicle node
        cv2.circle(frame, (px, py), 8, (0, 255, 0), -1)
        cv2.putText(frame, str(vid), (px-5, py+3), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0, 0, 0), 1)
    
    # Draw communication links
    for vid1, pos1 in positions.items():
        vehicle1 = vanet_system.vehicles[vid1]
        for vid2, pos2 in positions.items():
            if vid1 != vid2 and vid2 in vanet_system.vehicles:
                if vehicle1.can_communicate_with(vanet_system.vehicles[vid2]):
                    cv2.line(frame, pos1, pos2, (0, 255, 255), 1)

def main():
    print("🚀 VANET Professional Analytics Dashboard")
    print("=" * 50)
    print("Features:")
    print("✓ Real-time performance metrics")
    print("✓ Traffic analytics")
    print("✓ Network topology visualization") 
    print("✓ Communication efficiency tracking")
    print("✓ Professional reporting")
    print("=" * 50)
    
    # Initialize components
    model = YOLO('yolov8n.pt')
    tracker = Tracker()
    vanet = EnhancedVANET()
    
    vi = cv2.VideoCapture('highway_mini.mp4')
    
    class_list = ['person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck']
    
    # Analytics variables
    down = {}
    up = {}
    counter_down = []
    counter_up = []
    frame_count = 0
    
    print("📊 Starting professional analysis...")
    
    while True:
        frame_start_time = time.time()
        
        ret, frame = vi.read()
        if not ret:
            break
            
        frame_count += 1
        frame = cv2.resize(frame, (1400, 700))  # Larger for dashboard
        
        # YOLO detection
        results = model.predict(frame, verbose=False)
        a = results[0].boxes.data
        a = a.detach().cpu().numpy()
        px = pd.DataFrame(a).astype("float")
        
        detected_cars = []
        for index, row in px.iterrows():
            x1, y1, x2, y2 = int(row[0]), int(row[1]), int(row[2]), int(row[3])
            d = int(row[5])
            c = class_list[min(d, len(class_list)-1)]
            if 'car' in c.lower():
                detected_cars.append([x1, y1, x2, y2])
        
        # Update tracker and VANET
        bbox_id = tracker.update(detected_cars)
        vehicle_speeds = {}
        
        for bbox in bbox_id:
            x3, y3, x4, y4, vehicle_id = bbox
            cx = int((x3 + x4) / 2)
            cy = int((y3 + y4) / 2)
            
            # Add to VANET
            vanet.add_or_update_vehicle(vehicle_id, cx, cy, 0)
            
            # Speed calculations
            red_line_y = 280
            blue_line_y = 420
            offset = 7
            
            if red_line_y < (cy + offset) and red_line_y > (cy - offset):
                down[vehicle_id] = time.time()
                
            if vehicle_id in down:
                if blue_line_y < (cy + offset) and blue_line_y > (cy - offset):
                    elapsed_time = time.time() - down[vehicle_id]
                    if counter_down.count(vehicle_id) == 0:
                        counter_down.append(vehicle_id)
                        distance = 100
                        calculated_speed = (distance / elapsed_time) * 3.6
                        vehicle_speeds[vehicle_id] = calculated_speed
                        
                        # Update VANET with calculated speed
                        vanet.add_or_update_vehicle(vehicle_id, cx, cy, calculated_speed)
            
            # Draw vehicle
            cv2.rectangle(frame, (x3, y3), (x4, y4), (0, 255, 0), 2)
            cv2.circle(frame, (cx, cy), 4, (0, 0, 255), -1)
            cv2.putText(frame, f"ID:{vehicle_id}", (x3, y3-5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        
        # VANET communication
        vanet.simulate_communication()
        
        # Draw reference lines
        cv2.line(frame, (0, 280), (1400, 280), (0, 0, 255), 3)
        cv2.line(frame, (0, 420), (1400, 420), (255, 0, 0), 3)
        
        # Calculate processing time
        processing_time = time.time() - frame_start_time
        
        # Draw professional dashboard
        draw_professional_dashboard(frame, vanet, frame_count, processing_time)
        
        cv2.imshow('VANET Professional Analytics Dashboard', frame)
        
        # Controls
        key = cv2.waitKey(30) & 0xFF
        if key == 27:  # ESC
            break
        elif key == ord('s'):  # Save analytics report
            report = vanet.analytics.export_analytics(f"vanet_report_{int(time.time())}.json")
            print(f"📊 Analytics report saved!")
            print(f"   Average FPS: {report['current_snapshot']['processing_fps']:.1f}")
            print(f"   Total Vehicles: {report['traffic_metrics']['peak_vehicle_count']}")
            print(f"   Network Efficiency: {report['communication_metrics']['average_success_rate']:.2%}")
    
    # Final report
    final_report = vanet.analytics.export_analytics("final_analytics_report.json")
    print("\n🎯 FINAL ANALYTICS REPORT")
    print("=" * 40)
    print(f"📊 Session Duration: {final_report['session_info']['duration_seconds']:.1f}s")
    print(f"🚗 Peak Vehicles: {final_report['traffic_metrics']['peak_vehicle_count']}")
    print(f"⚡ Average FPS: {final_report['session_info']['average_fps']:.1f}")
    print(f"📡 Network Efficiency: {final_report['communication_metrics']['average_success_rate']:.2%}")
    print(f"💾 Report saved: final_analytics_report.json")
    
    vi.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
