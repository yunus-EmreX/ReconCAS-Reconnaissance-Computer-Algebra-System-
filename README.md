# 🌌 ReconCAS (OpticCAS-Terminal) // V0.1 BETA
**Vision-Based Computer Algebra System & Kinetic Sandbox**

ReconCAS is a locally hosted, enterprise-grade desktop application that captures raw image data from the screen buffer, routes it through an Optical Character Recognition (OCR) pipeline, and translates it into symbolic mathematical expressions for advanced analysis. Unlike standard calculators, it eliminates manual input by allowing users to select screen regions (bounding boxes) to extract, evaluate, and visualize equations instantly.

With the **V0.1 BETA** release, ReconCAS transcends standard mathematical evaluation, introducing a dynamic OpenCV-powered vision pipeline, a time-manipulable 3D Sandbox Simulator, and an integrated diagnostic debug environment.

---

## 📑 Table of Contents
1. [System Architecture](#-system-architecture)
2. [Core Modules & Capabilities](#-core-modules--capabilities)
3. [Security & Cryptography](#-security--cryptography)
4. [Project Directory Structure](#-project-directory-structure)
5. [Quality Assurance & Test Suite](#-quality-assurance--test-suite)
6. [Installation & Setup](#-installation--setup)
7. [Future Roadmap (V0.1 Final)](#-future-roadmap)

---

## ⚙️ System Architecture

The application operates on three strictly decoupled layers (Core, Vision, GUI):

### 1. Advanced Vision Engine (OpenCV + Tesseract)
The OCR pipeline has been entirely rebuilt to handle arbitrary screen conditions, low-resolution drawings, and subpixel rendering noise.
*   **Dynamic Scaling & Padding:** The engine automatically detects the height of the captured region. Oversized inputs are scaled down, and micro-inputs are interpolated (using `cv2.INTER_CUBIC` or `INTER_AREA`) to an optimal 65px target height for the Tesseract LSTM model. A 30-pixel white padding is automatically applied to prevent edge-clipping.
*   **Dark Mode Guard:** The engine calculates the average pixel intensity of the captured frame. If a dark environment is detected (`np.mean < 127`), it automatically applies a negative bitwise inversion to ensure dark-mode terminals and PDFs are read flawlessly.
*   **Context-Aware Corrector:** Common Tesseract OCR errors (e.g., reading `l` as `1` or `O` as `0`) are rectified using specialized Regex patterns. These substitutions are context-aware, ensuring that legitimate mathematical functions like `sin`, `cos`, and `log` remain uncorrupted.
*   **Live Scanning & Frame Differencing:** During continuous Live Area Scanning, the system hashes (MD5) consecutive frames. If the visual data remains unchanged, the OCR engine is bypassed, drastically preventing CPU spiking and optimizing performance.

### 2. Math Engine (Secure Symbolic Analysis)
*   **Zero-Trust Lexical Parser (Whitelist):** To prevent arbitrary code execution vulnerabilities from malicious or hallucinated OCR outputs, incoming text is subjected to strict lexical validation. Only whitelisted mathematical tokens (e.g., `x`, `y`, `limit`, `Matrix`, `dsolve`, `integrate`) are permitted.
*   **Smart Implicit Multiplication:** The engine uses targeted Regex to safely map implied operations (like `5 x 3`) to exact syntax (`5 * 3`) strictly between numeric boundaries.
*   **SymPy Integration:** Sanitized strings are passed to the SymPy engine to compute analytical derivatives, indefinite integrals, polynomial factorization, limits, and root solutions[cite: 1].

---

## 🛠️ Core Modules & Capabilities

### 🧪 CAS Laboratory
The Advanced Analysis module acts as a localized alternative to MATLAB/Mathematica. 
* Evaluates complex calculus expressions (Derivatives, Integrals, Limits, Roots, Simplification).
* **Dynamic Rendering:** Automatically scales Matplotlib output based on variable counts, plotting standard 2D curves for single variables ($x$) and shifting to 3D surface rendering for dual variables ($x, y$)[cite: 1].

### 🌌 Sandbox Sim Studio (Kinetic Space)
A revolutionary 3D mathematical sandbox allowing users to warp and animate spatial planes in real-time.
*   **Time-Based Kinesis:** Integrates a time variable (`t`) utilizing `matplotlib.animation`. The 3D surface breathes and ripples continuously based on the temporal flow.
*   **Chrono-Control (Time Stop):** Users can freeze the simulation at any specific frame to analyze the wave structure, and resume the temporal flow at will.
*   **Spatial Warping & Reverse Engineering:** Features interactive UI sliders (`A` for amplitude/height, `B` for gravity/slope). As users warp the space, the console reverse-engineers the live geometry, printing the active mathematical rule ($Z$) and absolute maximum resistance peaks ($Z_{MAX}$) in real-time.

### 🕵️ Industrial Debug Mode
To eliminate "blind spots" in the vision engine, the main terminal features an animated Cyberpunk Toggle for Debug Mode. 
* When activated, every OCR capture generates a diagnostic log inside the `logs/` directory.
* It outputs the raw OpenCV-processed image (`.png`) and a text log (`.txt`) detailing the exact raw string read by Tesseract vs. the parsed output.

---

## 🔒 Security & Cryptography

*   **Bcrypt Encryption:** The application utilizes a local SQLite database (`recon_cas_secure.db`)[cite: 1]. User passwords and recovery hints are never stored in plaintext; they are securely salted (`gensalt`) and hashed using the `bcrypt` algorithm[cite: 1].
*   **Password Override (Reset):** A secure recovery protocol allows users to reset passwords by verifying their hashed secret hint.
*   **Session Audit Logging:** All successful authentications, blocked malicious inputs (via the Whitelist), and evaluated equations are logged into the database with corresponding user IDs and timestamps, creating a solid operational audit trail[cite: 1].

---

## 📂 Project Directory Structure

```text
ReconCAS/
├── core/
│   ├── __init__.py
│   ├── auth_engine.py      # SQLite DB, Bcrypt Cryptography, Audit Logging
│   └── math_engine.py      # SymPy Parser, Expanded Lexical Whitelist
├── vision/
│   ├── __init__.py
│   └── ocr_engine.py       # Tesseract, OpenCV Processing, Dark Mode Guard
├── gui/
│   ├── __init__.py
│   └── app_windows.py      # Tkinter UI, Kinetic Sandbox, Animated Debug Toggle
├── tests/                  
│   ├── __init__.py
│   ├── test_math.py        # Security & Validation tests
│   ├── test_auth.py        # DB & Cryptography tests
│   └── test_ocr.py         # Regex & Context-aware correction tests
├── logs/                   # Diagnostic OCR outputs (Generated dynamically in Debug Mode)
├── requirements.txt        # Dependencies
└── main.py                 # System Bootloader
🛡️ Quality Assurance & Test Suite
The tests/ directory contains an automated test suite built upon Python's native unittest framework, auditing critical system components through isolated scenarios[cite: 1].

test_math.py (Security & Math): Tests arithmetic accuracy and validates that malicious payloads (e.g., __import__('os').system('dir'), eval('1+1')) are successfully blocked by the UnsafeExpressionException before reaching the SymPy parser[cite: 1]. Ensures critical regressions like the exp(0) conflict are fixed[cite: 1].

test_auth.py (Cryptography): Creates an isolated temporary test database to verify Bcrypt salting/hashing, successful authentication cycles, and secure password overrides[cite: 1].

test_ocr.py (Vision Filters): Verifies context-aware regex corrections (protecting log and cos from character substitution) and ensures non-mathematical strings ("Hello World") are filtered out by is_actual_math[cite: 1].

To execute the test suite, run the following command from the project root:

Bash
python -m unittest discover -s tests
🚀 Installation & Setup
Prerequisites: Python 3.8+ and Tesseract-OCR must be installed on your system[cite: 1].

Step 1: Install Tesseract-OCR
For Windows, download and install the Tesseract installer[cite: 1]. Ensure the installation path matches the default (The engine explicitly targets this path)[cite: 1]:
C:\Program Files\Tesseract-OCR\tesseract.exe

Step 2: Clone the Repository

Bash
git clone [https://github.com/yunus-EmreX/ReconCAS-Reconnaissance-Computer-Algebra-System-.git](https://github.com/yunus-EmreX/ReconCAS-Reconnaissance-Computer-Algebra-System-.git)
cd ReconCAS
Step 3: Install Dependencies

Bash
pip install -r requirements.txt
Step 4: Boot the Application

Bash
python main.py
(Note: The SQLite database will be generated automatically upon the first launch. Use [ CREATE_ACCOUNT ] to register your first operator credential before logging in)[cite: 1].

🔮 Future Roadmap (V0.1 Final)
The current UI features a locked terminal command: [ PDF_DOKÜMAN_ANALİZİ ]. In the upcoming V0.1 Final release, ReconCAS will introduce a 4th layer (document_engine.py) designed for batch processing. Users will be able to inject massive (80+ page) engineering PDFs into the system, extracting, indexing, and stress-testing hundreds of equations simultaneously with full spatial metadata tracking.

License: This project is licensed under the Apache License 2.0. See the LICENSE file for details
