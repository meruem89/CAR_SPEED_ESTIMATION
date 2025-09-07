# 🚗📡 Car Speed Estimation with VANET Communication

**Advanced Vehicle Speed Detection System with Vehicular Ad-hoc Network (VANET) Integration**

This project combines computer vision-based vehicle speed estimation with VANET communication protocols, enabling vehicles to share speed information in real-time through simulated Vehicle-to-Vehicle (V2V) communication.

## 🌟 Features

- **🎯 Real-time Vehicle Detection**: Uses YOLOv8 for accurate car detection
- **⚡ Speed Calculation**: Measures vehicle speeds using dual-line timing method
- **📡 VANET Communication**: Simulates V2V speed sharing between vehicles
- **🎮 Interactive Control**: Frame-by-frame analysis with multiple viewing modes
- **📊 Range-based Broadcasting**: Vehicles share speeds with others within communication range
- **🔍 Visual Feedback**: Clean visualization with communication links and status panels

## 🏗️ System Architecture

### Core Components
1. **YOLOv8 Detection Engine** - Identifies vehicles in video frames
2. **Vehicle Tracking System** - Maintains vehicle identities across frames
3. **Speed Calculation Module** - Computes speeds using reference line crossings
4. **VANET Communication Layer** - Handles V2V message broadcasting and reception
5. **Visualization Engine** - Renders vehicles, communications, and data overlays

### Speed Calculation Method
- **Dual-line System**: Red line (y=198) and Blue line (y=268)
- **Distance**: 100 meters between reference lines
- **Formula**: Speed = Distance / Time_elapsed
- **Accuracy**: Real-time calculation when vehicles cross both lines

## 📁 Project Files

### 🎯 Main Applications
- **`vanet_range_based.py`** ⭐ - **Primary Implementation**
  - Range-based VANET communication (180px range)
  - Clean vehicle visualization (green squares + red dots)
  - Speed display above all communicating vehicles
  - Frame-by-frame control

- **`vanet_analysis_slow.py`** - **Research Mode**
  - Ultra-detailed VANET analysis
  - Console communication logging
  - Signal strength visualization
  - Pure manual frame stepping

- **`car_speed_estimator_vanet.py`** - **Enhanced Version**
  - VANET with advanced frame control
  - Video restart capability
  - Multiple viewing modes

### 🔧 Supporting Files
- **`car_speed_estimator_frame_control.py`** - Frame control without VANET
- **`car_speed_estimator.py`** - Basic speed estimation
- **`vanet_speed_sharing.py`** - VANET communication module
- **`tracker.py`** - Vehicle tracking algorithm

## 🎥 Live Demo

### 🎬 Demo Video
*Coming Soon: Upload a demo video/GIF showing the VANET communication in action*

### 🌐 Online Demo
*Future Enhancement: Web-based demo using Streamlit or Gradio*

---

## 🚀 Quick Start Guide

### 📋 Prerequisites

**System Requirements:**
- Python 3.8 or higher
- Git (for cloning)
- Webcam or video file (highway_mini.mp4 included)

**Install Dependencies:**
```bash
pip install ultralytics opencv-python pandas numpy
```

### 📥 Installation Steps

**1. Clone the Repository:**
```bash
git clone https://github.com/meruem89/CAR_SPEED_ESTIMATION.git
cd CAR_SPEED_ESTIMATION
```

**2. Install Required Packages:**
```bash
# Install all dependencies at once
pip install ultralytics opencv-python pandas numpy

# Or use requirements.txt (if available)
# pip install -r requirements.txt
```

**3. Verify Installation:**
```bash
python -c "import cv2, pandas, ultralytics; print('✅ All dependencies installed successfully!')"
```

### 🎮 Running the Application

**🌟 Main VANET Implementation (Recommended):**
```bash
python vanet_range_based.py
```
*Features: Range-based communication, clean visualization, real-time V2V*

**🔬 Research/Analysis Mode:**
```bash
python vanet_analysis_slow.py
```
*Features: Detailed logs, frame-by-frame analysis, research insights*

**⚡ Enhanced VANET Version:**
```bash
python car_speed_estimator_vanet.py
```
*Features: Advanced controls, video restart, multiple modes*

### 🎛️ Controls & Usage

**Basic Controls:**
- **SPACEBAR** - Next frame (manual mode)
- **'p'** - Toggle auto/manual playback  
- **'r'** - Restart video (where available)
- **ESC** - Exit application

**What You'll See:**
- 🟢 **Green rectangles** - Detected vehicles
- 🔴 **Red dots** - Vehicle center points
- 🟡 **Yellow lines** - Active V2V communications
- 🟡 **Yellow circles** - Communication range
- 📊 **Speed data** - Above communicating vehicles

### ⚡ Quick Test

**Run this for instant demo:**
```bash
# Clone and run in one go
git clone https://github.com/meruem89/CAR_SPEED_ESTIMATION.git && cd CAR_SPEED_ESTIMATION && pip install ultralytics opencv-python pandas numpy && python vanet_range_based.py
```

## 🎮 Application Modes

### 1. Range-Based VANET (`vanet_range_based.py`) ⭐
**Perfect for demonstrations and real-world simulation**
- All vehicles shown as green rectangles with red center dots
- Speed calculated when crossing second reference line
- Broadcasts to ALL vehicles within 180-pixel communication range
- Received speeds displayed above vehicles
- Yellow communication lines show active V2V links
- Real-time status panel with VANET statistics

### 2. Analysis Mode (`vanet_analysis_slow.py`)
**Ideal for research and detailed study**
- Step-by-step frame analysis
- Detailed communication logs in console
- Signal strength indicators
- Distance measurements between communicating vehicles
- Enhanced information panels for each vehicle

### 3. Enhanced VANET (`car_speed_estimator_vanet.py`)
**Full-featured with advanced controls**
- Multiple playback modes
- Video restart capability
- Frame counter and progress tracking
- Comprehensive VANET status monitoring

## 📊 VANET Communication Protocol

### Communication Flow
1. **Detection Phase**: YOLOv8 detects vehicles in frame
2. **Tracking Phase**: Tracker maintains vehicle identities
3. **Speed Calculation**: Vehicle crosses reference lines → speed computed
4. **Broadcasting Phase**: Calculated speed sent to vehicles within range
5. **Reception Phase**: Nearby vehicles receive and display shared speeds
6. **Visualization**: Communication links and data shown on screen

### Message Structure
```python
{
    'from_vehicle': int,     # Sender vehicle ID
    'speed': float,          # Speed in km/h
    'direction': str,        # UP/DOWN traffic direction
    'timestamp': float,      # Message timestamp
    'distance': float        # Distance to receiving vehicle
}
```

## 📈 Technical Specifications

### Performance Metrics
- **Detection Accuracy**: YOLOv8n model on COCO dataset
- **Processing Speed**: Real-time on standard hardware
- **Communication Range**: 180 pixels (≈300 meters real-world)
- **Message Lifetime**: 8 seconds (configurable)
- **Frame Rate**: 30 FPS (adjustable)

### System Requirements
- **Python**: 3.8+
- **OpenCV**: 4.5+
- **Ultralytics**: Latest
- **Hardware**: GPU recommended for optimal performance

## 🎯 Use Cases

### Academic Research
- **VANET Protocol Studies**: Analyze V2V communication patterns
- **Traffic Flow Analysis**: Study vehicle speed distributions
- **Algorithm Testing**: Evaluate tracking and detection performance

### Industry Applications
- **Smart Traffic Systems**: Real-time traffic monitoring
- **Autonomous Vehicles**: V2V communication simulation
- **Transportation Planning**: Traffic pattern analysis

### Educational Purposes
- **Computer Vision**: Object detection and tracking
- **Networking**: VANET communication protocols
- **Data Visualization**: Real-time system monitoring

## 🔬 Research Insights

### Key Findings
- **Communication Effectiveness**: Range-based broadcasting reaches more vehicles than directional-only
- **Visual Clarity**: Clean visualization improves understanding of V2V interactions
- **Real-time Performance**: System maintains responsiveness with multiple communicating vehicles
- **Data Persistence**: 8-second message lifetime provides good balance between freshness and availability

## 🛠️ Customization Options

### Adjustable Parameters
```python
# Communication range (pixels)
communication_range = 180

# Message lifetime (seconds) 
message_lifetime = 8.0

# Reference line positions
red_line_y = 198
blue_line_y = 268

# Distance between lines (meters)
distance_between_lines = 100
```

## 📸 Example Output

![VANET Communication Visualization](model%20output.png)

*Vehicles communicating speeds through VANET protocol with visual feedback*

## 🤝 Contributing

Contributions are welcome! Areas for improvement:
- Enhanced tracking algorithms
- Additional VANET protocols
- Performance optimizations
- Extended visualization options

## 📄 License

This project is open source and available under standard academic use terms.

## 🏆 Acknowledgments

- **YOLOv8**: Ultralytics team for the detection model
- **OpenCV**: Computer vision library
- **VANET Research Community**: For protocol specifications and best practices

---

**🚗 Ready to explore the future of connected vehicles? Start with `vanet_range_based.py`! 📡**
