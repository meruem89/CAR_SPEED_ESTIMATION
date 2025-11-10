# 🎯 QUICK START GUIDE

## ⭐ RECOMMENDED: Frame-by-Frame Control

### Best for Project Review and Demonstrations

**Double-click:** `RUN_FRAME_BY_FRAME.bat`

**Or run:**
```bash
python vanet_streamlit_hybrid.py
```

### ✅ Why Use This Version?

- **Perfect Keyboard Control** - SPACEBAR to pause/resume, Q to quit
- **No Browser Issues** - Standalone OpenCV window
- **70% Video + 30% Dashboard** - Professional split-screen
- **Real-time Updates** - Dashboard updates as vehicles cross lines
- **Color-Coded Warnings**:
  - 🔴 Red: < 30m (too close)
  - 🟡 Yellow: 30-70m (moderate distance)
  - 🟢 Green: > 70m (safe distance)

### 🎮 Controls:

- **SPACEBAR** - Pause/Resume video
- **Q** - Quit application
- **Keep window in focus** to use keyboard

---

## 🌐 Alternative: Web Dashboard (Streamlit)

### For Web-Based Presentation

**Double-click:** `RUN_STREAMLIT.bat`

**Or run:**
```bash
python -m streamlit run streamlit_app.py
```

Then open: **http://localhost:8501**

### ✅ Why Use This Version?

- **Web Interface** - Runs in browser
- **File Upload** - Drag & drop videos
- **Cross-Platform** - Works on any OS
- **Remote Access** - Can demo from any device on network

### ⚠️ Limitations:

- Keyboard controls (SPACE/Q) work in separate control window
- May restart video on interaction
- Browser refresh issues

---

## 📂 Files Overview:

### Main Applications:

1. **`vanet_streamlit_hybrid.py`** ⭐ RECOMMENDED
   - Frame-by-frame control with SPACEBAR
   - 70% video + 30% dashboard
   - Perfect keyboard control
   - **Run:** `python vanet_streamlit_hybrid.py`

2. **`vanet_clean_presentation.py`**
   - Original terminal version
   - Manual frame advance (press any key)
   - **Run:** `python vanet_clean_presentation.py`

3. **`streamlit_app.py`**
   - Web dashboard version
   - Browser-based interface
   - **Run:** `python -m streamlit run streamlit_app.py`

### Quick Launchers:

- **`RUN_FRAME_BY_FRAME.bat`** ⭐ Best choice
- **`RUN_STREAMLIT.bat`** - Web version

### Support Files:

- **`tracker.py`** - Vehicle tracking module
- **`yolov8n.pt`** - YOLO model (6.3 MB)
- **`highway_mini.mp4`** - Test video (5.0 MB)
- **`requirements.txt`** - Python dependencies

---

## 🎓 For Project Review:

### Recommended Demo Flow:

1. **Start the frame-by-frame version:**
   ```bash
   Double-click: RUN_FRAME_BY_FRAME.bat
   ```

2. **Show features:**
   - Point out the 70%-30% split layout
   - Highlight real-time vehicle detection
   - Demonstrate spacebar pause/resume
   - Explain color-coded distance warnings

3. **Explain VANET:**
   - "Vehicles broadcast speeds to others within 300m range"
   - "Dashboard shows current vehicle + 3 previous vehicles"
   - "MAC addresses uniquely identify each vehicle"
   - "Speeds calculated using dual-line timing (100m distance)"

4. **Technical Details:**
   - YOLOv8 for detection
   - Custom tracker for ID consistency
   - OpenCV for video processing
   - Dual-line speed calculation (RED at y=198, BLUE at y=268)

---

## 💡 Troubleshooting:

### "Module not found" errors?
```bash
pip install ultralytics opencv-python pandas numpy torch
```

### Frame-by-frame not pausing?
- Make sure OpenCV window has focus (click on it)
- Press SPACEBAR (not mouse click)

### Streamlit not working?
```bash
pip install streamlit pillow
python -m streamlit run streamlit_app.py
```

### Video not loading?
- Check `highway_mini.mp4` is in the same folder
- Check `yolov8n.pt` model file exists

---

## 📊 What You'll See:

### Left Side (70% - Video):
- Vehicle bounding boxes (green)
- Vehicle IDs
- Speed labels (cyan)
- RED line (entry)
- BLUE line (exit)
- DOWN/UP counters

### Right Side (30% - Dashboard):

**Current Vehicle:**
- ID: #5
- MAC: A3:4F:2E:8B:C1:9D
- Speed: 65 km/h
- Lane: Lane 3
- Direction: DOWN

**Previous Vehicles (Last 3):**
- 🟢 Vehicle #4 - Lane 3 - 45m - 58 km/h
- 🟡 Vehicle #3 - Lane 2 - 65m - 72 km/h
- 🟢 Vehicle #2 - Lane 3 - 112m - 68 km/h

**Statistics:**
- Total: 8 vehicles
- DOWN: 5 | UP: 3

---

## ✅ Final Checklist:

Before presentation:

- [ ] Run `python vanet_streamlit_hybrid.py` to test
- [ ] Verify SPACEBAR pause/resume works
- [ ] Check dashboard updates correctly
- [ ] Confirm color-coded distances show
- [ ] Practice explaining VANET concept

---

**Created for:** CAR_SPEED_ESTIMATION Project  
**Best Version:** `vanet_streamlit_hybrid.py` with `RUN_FRAME_BY_FRAME.bat`  
**Controls:** SPACEBAR=Pause/Resume, Q=Quit
