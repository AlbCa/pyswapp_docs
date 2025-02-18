# SWA
**swa** is an open-source Python library for processing surface wave seismic data.

---

## 📁 Folder and File Structure

- `swa.yml`  
  Conda environment file for setting up the required dependencies.

---

### **Library: `swa`**
Contains the core processing routines:
- **`stream.py`**  
  Main class for reading, processing, visualizing, and transforming seismic shot gathers.
- **`curve.py`**  
  Class for handling dispersion curves (read, process, visualize, save).
- **`curves.py`**  
  Combines multiple dispersion curves (e.g., from repeated shots) using binning for error estimation.
- **`manager.py`**  
  describe the new class...
- **`_init_.py`**  
  describe the new class...
- **`utils`**  
  describe the new folder...

---

### **Examples**
Scripts demonstrating various use cases:
- **`0a_create_geometry.py`**  
  Create and read a `geometry.csv` file.
- **`0b_manager_basics.py`**  
  An overview of the new manager.
- **`3a_run_tomo2d.py`**  
  Perform a tomography-like 2D analysis and visualize results.
- **`4a_run_MASW2D.py`**  
  Run the MASW pseudo-2D approach with dispersion curve combination.
- **`4b_run_MASW2D_mopa.py`**  
  Run the MASW pseudo-2D approach with mopa approach.
- **`4c_run_MASW2D_windowing.py`**  
  Run the MASW pseudo-2D approach with windowing approach.
- **`5a_combine_curves.py`**  
  Dispersion curve combination.

---

### **Notebooks**
Interactive Jupyter notebooks to be created...

---

### **Data: `data`**
Directory for raw and processed data:
- **`syn_data/`**  
  Synthetic data set.
  - **`proc/`**  
    Processed data.
    - **`swa_v2/`**  
      Applied FK filters.
      - **`3a_tomo2D/`**  
        describe the new folder...
      - **`3b_MASW2D/`**  
        describe the new folder...
  - **`raw/`**  
    Original raw data.
  - **`geometry_v2.csv`**  
    Manually created geometry file.
  - **`geometry_test.csv`**  
    Automatically created geometry file.
- **`real_data/`**  
  Real data sets.
  - **`Moriago/`**  
    2D active dataset.

---

## 🚀 Getting Started

1. Clone the repository:
   ```bash
   git clone https://github.com/AlbCa/swa.git
