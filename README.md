# pySWApp - an interactive, open-source python toolbox for processing seismic surface wave data

by
Nathalie Roser, Ilaria Barone, Alberto Carrera and Adrián Flores Orozco

---

## Abstract

We introduce the open-source python library pySWApp, which provides a flexible 
and semi-interactive framework for managing and processing 2D active seismic 
surface wave data for dispersion curve analysis. Among classical approaches for 
surface-wave analysis such as the Multichannel Analysis of Surface Waves (MASW), 
pySWApp encompasses advanced approaches for extracting dispersion curves under 
laterally challenging conditions: the Multi-Offset Phase Analysis (MOPA) and the 
Tomographic-Like Approach (Tomo2D).

---

## 📁 Folder and File Structure

The source code of the pySWApp library is in the `code` folder.
Synthetic data to reproduce the exemplary use cases presented in the 
manuscript are provided in the `data` folder. 
Exemplary scripts to showcase the libraries key functions are  provided in 
the `examples` folder. 
The pdf of the manuscript are in the `docs` folder.

---

### **Library: `pyswapp`**
Contains the core processing routines:
- **`manager.py`**  
  describe the new class...
- **`stream.py`**  
  Main class for reading, processing, visualizing, and transforming seismic shot gathers.
- **`curve.py`**  
  Class for handling dispersion curves (read, process, visualize, save).
- **`curves.py`**  
  Combines multiple dispersion curves (e.g., from repeated shots) using binning for error estimation.
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

## Dependencies

You'll need a working Python environment to run the code.
The recommended way to set up your environment is through the
[Anaconda Python distribution](https://www.anaconda.com/download/) which
provides the `conda` package manager.

The required dependencies are specified in the file `environment.yml`.

Open a terminal (Linux & Mac) or the Anaconda Prompt (Windows) and run the 
following command in the repository folder (where `environment.yml`
is located) to create a new environment and install the required
dependencies:

    conda env create

---

## 🚀 Getting Started

1. Clone the repository:
   ```bash
   git clone https://github.com/AlbCa/swa.git
   

2. Installing the library

To use the pySWApp library we suggest to install it in an conda 
environment. Run the following lines to activate the corresponding environment 
and start the setup process.

    conda activate <env_name>
    cd code
    pip install .

## License

All source code is made available under the MIT License. See LICENSE.md for 
the full license text.
