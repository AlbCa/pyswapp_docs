# SWA
**swa** is an open-source Python library for processing surface wave seismic data.

---

## 📁 Folder and File Structure

- `swa.yml`  
  Conda environment file for setting up the required dependencies.

---

### **Library: `swa`**
Contains the core processing routines:
- **`_stream.py`**  
  Main class for reading, processing, visualizing, and transforming seismic shot gathers.
- **`_curve.py`**  
  Class for handling dispersion curves (read, process, visualize, save).
- **`_combineCurves.py`**  
  Combines multiple dispersion curves (e.g., from repeated shots) using binning for error estimation.
- **`utils.py`**  
  Utility functions, mainly for file handling.
- **`interactive_tools.py`**  
  Interactive tools for FK filtering, dispersion curve picking, velocity estimation, and linear muting.
- **`geometry.py`**  
  Functions for creating and reading geometry files.

---

### **Examples**
Scripts demonstrating various use cases:
- **`0a_create_geometry.py`**  
  Create and read a `geometry.csv` file.
- **`0b_manip_amps.py`**  
  Perform linear muting, LMO (Linear Moveout), and trace selection.
- **`1a_filter_fk.py`**  
  Create and/or apply FK filters.
- **`1b_pick_dc.py`**  
  Pick and plot dispersion curves.
- **`1c_windowing.py`**  
  Run the windowing procedure and plot the 2D pseudosection.
- **`1d_mopa.py`**  
  Windowing procedure with MOPA, including 2D pseudosection plotting.
- **`2a_combineDCs.py`**  
  Combine dispersion curves by midpoint and process them.
- **`3a_compute_phasediff.py`**  
  Filter data in the FK domain and compute phase differences.
- **`3b_run_tomo2d.py`**  
  Perform a tomography-like 2D analysis and visualize results.
- **`4a_MASW2D.py`**  
  Run the MASW pseudo-2D approach with dispersion curve combination.

---

### **Notebooks: `WR2024`**
Interactive Jupyter notebooks for XXI Workshop di Geofisica (Rovereto) workflows:
- **`wr2024_nb1.ipynb`**  
  Data handling, interactive plotting, picking, and combining dispersion curves.
- **`wr2024_nb2.ipynb`**  
  MASW pseudo-2D
- **`wr2024_nb3.ipynb`**  
  Tomography-like approach
- **`fk_filtering.ipynb`**  
  Interactive f-k filtering test

---

### **Data: `data`**
Directory for raw and processed data:
- **`syn_data/`**  
  Synthetic data set.
  - **`plots/`**  
    Output plots.
  - **`proc/`**  
    Processed data.
    - **`fk_filter/`**  
      Applied FK filters.
    - **`dc_pick/`**  
      Picked dispersion curves.
  - **`raw/`**  
    Original raw data.
  - **`geometry.csv`**  
    Manually created geometry file.
  - **`geometry_test.csv`**  
    Automatically created geometry file.

---

## 🚀 Getting Started

1. Clone the repository:
   ```bash
   git clone https://github.com/AlbCa/swa.git
