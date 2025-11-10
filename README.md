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

- **`vanet_mac_dashboard.py`** ⭐ **NEW - MAC Address-Based VANET with Dashboard** (RECOMMENDED)

  - **Realistic vehicle identification using MAC addresses**
  - **Multi-directional dashboard** showing surrounding vehicles
  - **Position-based identification** (Front, Left, Right zones)
  - **Distance calculation** in meters/kilometers
  - **Filters out vehicles behind** - shows only relevant vehicles ahead and on sides
  - **Continuous speed broadcasting** - not just at timing lines
  - **Professional dashboard interface** with color-coded warnings
  - Addresses academic review concerns about vehicle identification

- **`vanet_universal.py`** ✨ - **Universal Video Support**

  - **Works with ANY video file**
  - Auto-detects video dimensions and adapts
  - Command-line interface with options
  - Save output videos
  - Smart scenario detection

- **`vanet_range_based.py`** - **Basic VANET Implementation**

  - Range-based VANET communication (180px range)
  - Clean vehicle visualization (green squares + red dots)
  - Speed display above all communicating vehicles
  - Frame-by-frame control
  - Works with highway_mini.mp4

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

_Coming Soon: Upload a demo video/GIF showing the VANET communication in action_

### 🌐 Online Demo

_Future Enhancement: Web-based demo using Streamlit or Gradio_

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
# Option 1: Use requirements.txt (Recommended)
pip install -r requirements.txt

# Option 2: Install manually
pip install ultralytics opencv-python pandas numpy torch Pillow
```

**3. Verify Installation:**

```bash
python -c "import cv2, pandas, ultralytics; print('✅ All dependencies installed successfully!')"
```

### 🎟️ Running the Application

**⭐ NEW - MAC-Based VANET with Dashboard (RECOMMENDED):**

```bash
python vanet_mac_dashboard.py
```

_Features: Realistic MAC addressing, multi-directional dashboard, position-based vehicle identification, distance display, filters vehicles behind, continuous speed broadcasting_

**✨ Universal Version (Works with ANY video):**

```bash
# Use your own video file
python vanet_universal.py --video your_video.mp4

# With custom settings
python vanet_universal.py --video traffic.mp4 --range 250 --distance 50

# Save output video
python vanet_universal.py --video input.mp4 --output result.mp4
```

_Features: Any video format, auto-adaptation, command-line options_

**🌟 Basic VANET Implementation (Highway video):**

```bash
python vanet_range_based.py
```

_Features: Range-based communication, clean visualization, real-time V2V_

**🔬 Research/Analysis Mode:**

```bash
python vanet_analysis_slow.py
```

_Features: Detailed logs, frame-by-frame analysis, research insights_

**⚡ Enhanced VANET Version:**

```bash
python car_speed_estimator_vanet.py
```

_Features: Advanced controls, video restart, multiple modes_

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
git clone https://github.com/meruem89/CAR_SPEED_ESTIMATION.git && cd CAR_SPEED_ESTIMATION && pip install -r requirements.txt && python vanet_range_based.py
```

---

## 🔧 Troubleshooting

### Common Issues & Solutions

**❌ Issue: `ModuleNotFoundError: No module named 'ultralytics'`**

```bash
# Solution: Install missing dependencies
pip install -r requirements.txt
```

**❌ Issue: `cv2.error` or OpenCV issues**

```bash
# Solution: Reinstall OpenCV
pip uninstall opencv-python
pip install opencv-python
```

**❌ Issue: YOLO model download fails**

```bash
# Solution: Manual model download
wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt
# Or download from: https://github.com/ultralytics/ultralytics
```

**❌ Issue: Video file not found**

- Ensure `highway_mini.mp4` is in the project directory
- Or replace with your own video file in the code

**❌ Issue: Performance is slow**

```bash
# Solution: Install GPU support (if available)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

### Platform-Specific Instructions

**🐧 Linux/Ubuntu:**

```bash
# Install system dependencies
sudo apt update
sudo apt install python3-pip git

# Clone and install
git clone https://github.com/meruem89/CAR_SPEED_ESTIMATION.git
cd CAR_SPEED_ESTIMATION
pip3 install -r requirements.txt
python3 vanet_range_based.py
```

**🍎 macOS:**

```bash
# Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python and Git
brew install python git

# Clone and install
git clone https://github.com/meruem89/CAR_SPEED_ESTIMATION.git
cd CAR_SPEED_ESTIMATION
pip3 install -r requirements.txt
python3 vanet_range_based.py
```

**🧪 Windows:**

```powershell
# Using PowerShell
git clone https://github.com/meruem89/CAR_SPEED_ESTIMATION.git
cd CAR_SPEED_ESTIMATION
pip install -r requirements.txt
python vanet_range_based.py
```

### Getting Help

**💬 Need help?**

- Create an issue on GitHub: [Issues Page](https://github.com/meruem89/CAR_SPEED_ESTIMATION/issues)
- Check existing issues for solutions
- Provide system info, Python version, and error messages

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

### MAC Address-Based Vehicle Identification (NEW)

**Realistic Approach:**

- Each vehicle assigned unique MAC address (e.g., A3:4F:2E:D1:8C:9B)
- Simulates real VANET on-board unit identifiers
- Position-based vehicle identification system
- Driver dashboard shows contextual information, not technical MAC addresses

**Multi-Directional Detection:**

```
        FRONT-LEFT    FRONT    FRONT-RIGHT
              \        |        /
               \       |       /
                \      |      /
    LEFT -------- [YOUR CAR] -------- RIGHT

                  (Behind vehicles filtered out)
```

**Dashboard Display:**

- **Zone-based information**: Shows vehicles in Front, Front-Left, Front-Right, Left, Right zones
- **Distance measurement**: Displays distance in meters/kilometers
- **Speed information**: Real-time speed of surrounding vehicles
- **Color-coded warnings**: Red (< 20m), Yellow (20-50m), Green (> 50m)
- **Sorted by proximity**: Closest vehicles shown first

**Message Structure:**

```python
{
    'from_mac': 'A3:4F:2E:D1:8C:9B',  # Sender's MAC address
    'speed': 80.5,                     # Speed in km/h
    'position': (450, 200),            # Sender position
    'direction': 'UP',                 # Traffic direction
    'relative_direction': 'FRONT',    # Relative to receiver
    'distance': 50.0,                  # Distance in pixels
    'timestamp': 1699999999.123        # Message timestamp
}
```

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
    'from_vehicle': int,     # Sender vehicle ID (basic version)
    'from_mac': str,         # Sender MAC address (new version)
    'speed': float,          # Speed in km/h
    'direction': str,        # UP/DOWN traffic direction
    'relative_direction': str, # Front/Left/Right (new version)
    'distance': float,       # Distance to receiving vehicle
    'timestamp': float       # Message timestamp
}
```

## 🎯 Key Features Explained

### 1. Realistic Vehicle Identification

**Problem Solved:** How does a receiving vehicle identify which physical vehicle sent the message?

**Solution:**

- **Backend:** Uses MAC addresses for V2V communication (technical accuracy)
- **Frontend:** Shows position-based identification (Front, Left, Right) for driver
- **Position Calculation:** Uses Euclidean distance and angle calculations
- **Direction Filtering:** Ignores vehicles behind, shows only relevant vehicles

**Real-World Parallel:**

- Similar to modern Tesla/BMW collision warning systems
- Drivers see "Vehicle ahead: 80 km/h" not technical MAC addresses
- Position-based awareness for safety

### 2. Continuous Speed Broadcasting

**Enhancement:** Vehicles broadcast speed continuously, not just after crossing timing lines

**Implementation:**

- **Motion-based estimation:** Calculates speed from position changes across frames
- **Dual broadcast system:**
  - Estimated speed: Continuous updates during vehicle tracking
  - Calculated speed: Accurate measurement at timing lines
- **Real-time updates:** Other vehicles receive current speed information

### 3. Multi-Zone Dashboard

**Driver Interface:**

- Visual representation of surrounding vehicles
- Zone-based display (Front-Left, Front, Front-Right, Left, Right)
- Distance and speed for each zone
- Sorted list of nearest vehicles
- Color-coded proximity warnings

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

_Vehicles communicating speeds through VANET protocol with visual feedback_

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
