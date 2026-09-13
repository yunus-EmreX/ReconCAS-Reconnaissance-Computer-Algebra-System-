# 🌌 ReconCAS (OpticCAS-Terminal) // V0.1.1 BETA
**Vision-Based Computer Algebra System & Kinetic Sandbox**

ReconCAS is a locally hosted desktop application that captures raw image data from the screen buffer or document files (PDF/Görsel), routes it through an Optical Character Recognition (OCR) pipeline, and translates it into symbolic mathematical expressions for advanced analysis. Unlike standard calculators, it eliminates manual input by allowing users to select screen regions (bounding boxes) or upload documents to extract, evaluate, and visualize equations instantly.

With the **V0.1.1 BETA** release, ReconCAS transcends standard mathematical evaluation, introducing a dynamic OpenCV-powered vision pipeline, a high-resolution Document Engine, a time-manipulable 3D Sandbox Simulator, and an integrated diagnostic debug environment.

---

## 📑 Table of Contents
1. [System Architecture](#-system-architecture)
2. [Core Modules & Capabilities](#-core-modules--capabilities)
3. [Security & Cryptography](#-security--cryptography)
4. [Project Directory Structure](#-project-directory-structure)
5. [Quality Assurance & Test Suite](#-quality-assurance--test-suite)
6. [Release Updates & Changelog](#-release-updates--changelog)
7. [Installation & Setup](#-installation--setup)
8. [Future Roadmap](#-future-roadmap)

---

## ⚙️ System Architecture

The application operates on four decoupled layers (Core, Vision, Document Engine, GUI):

### 1. Advanced Vision Engine (OpenCV + Tesseract)
The OCR pipeline handles arbitrary screen conditions, low-resolution drawings, and subpixel rendering noise.
*   **Adaptive Scaling & Padding:** The engine automatically detects the height of the captured region. Micro-inputs are interpolated (using `cv2.INTER_CUBIC`) to an optimal 96px target height for the Tesseract LSTM model. A 30-pixel white padding is automatically applied to prevent edge-clipping. Full document pages are segmented into line regions to preserve character resolution.
*   **Dark Mode Guard:** The engine calculates the average pixel intensity of the captured frame. If a dark environment is detected (`np.mean < 127`), it automatically applies a negative bitwise inversion to ensure dark-mode terminals and PDFs are read flawlessly.
*   **Multi-Criteria Scoring & PSM Selection:** Evaluates PSM modes (6, 11, 4) using OCR confidence, expression parse success, parentheses balance, and math density, penalizing non-math prose.
*   **Token Confusion Correction & Multi-Equation Segmentation:** Rectifies common OCR confusions (`ly -> y`, `lx -> x`, `Ix -> x`, `02H -> 0=2`) and splits multi-equation lines automatically.
*   **Live Scanning & Frame Differencing:** During continuous Live Area Scanning, the system hashes (MD5) consecutive frames to bypass OCR when visual data is unchanged, drastically optimizing CPU usage.

### 2. Math Engine (Zero-Trust Symbolic Analysis)
*   **Strict Lexical Parser (Whitelist):** Incoming text is normalized first, then validated against a canonical case-insensitive whitelist (`SAFE_WORDS`) and character set (`ALLOWED_TOKENS`), completely blocking code injection vulnerabilities (`__import__`, `eval`, arbitrary system commands).
*   **Syntax-Aware Normalization:** Automatically converts Unicode math characters (`π`, `∞`, `√`, `∫`, `×`, `÷`, `²`, `³`, `¹`), roots (`√x`, `√(x+1)` -> `sqrt(...)`), integrals (`∫x dx` -> `integrate(x, x)`), and absolute values (`|x|` -> `Abs(x)`).
*   **Operation Dispatcher:** First-class dispatching for symbolic operations (`diff`, `integrate`, `limit`, `series`, `factor`, `simplify`, `Matrix`, `solve`).

### 3. Document Engine (High-Resolution Batch Processing)
*   Integrates PyMuPDF (`fitz`) and OpenCV to analyze images (`.png`, `.jpg`, `.jpeg`, `.bmp`, `.tiff`, `.tif`) and multi-page PDFs.
*   Preserves full 200 DPI resolution, detects text line regions, and outputs rich metadata including OCR confidence, raw text, normalized text, and SymPy validation status.

### 4. GUI Layer (Modular Tkinter & Matplotlib)
*   Cyberpunk terminal styling (`#050505` dark theme, `#00FF41` matrix green, `#00FFFF` cyan).
*   Decoupled modules: `theme.py`, `widgets.py`, `auth_window.py`, `terminal_window.py`, `lab_window.py`, `sandbox_window.py`, `document_window.py`, and `app_windows.py` (facade).

---

## 🛠️ Core Modules & Capabilities

### 🧪 CAS Laboratory
Acts as a localized alternative to MATLAB/Mathematica.
* Evaluates complex calculus expressions (Derivatives, Integrals, Limits, Roots, Simplification, Factoring).
* **Dynamic Rendering:** Automatically scales Matplotlib output based on variable counts, plotting standard 2D curves for single variables ($x$) and shifting to 3D surface rendering for dual variables ($x, y$).

### 🌌 Sandbox Sim Studio (Kinetic Space)
A 3D mathematical sandbox allowing users to warp and animate spatial planes in real-time.
*   **Time-Based Kinesis:** Integrates a time variable (`t`) utilizing `matplotlib.animation`. The 3D surface ripples continuously based on temporal flow.
*   **Chrono-Control (Time Stop):** Users can freeze the simulation at any specific frame to analyze wave structures, and resume temporal flow at will.
*   **Spatial Warping & Resistance Analysis:** Interactive UI sliders (`A` for amplitude/height, `B` for gravity/slope) compute live mathematical rules ($Z$) and absolute maximum resistance peaks ($Z_{MAX}$) in real-time.

### 📄 Document Analyzer (Batch Scanner)
*   Scans multi-page PDFs and images, displaying extracted equations along with OCR confidence scores and page numbers.
*   Directly routes any selected equation to the CAS Lab or 3D Kinetic Sandbox.

### 🕵️ Diagnostic Debug Mode
*   Animated Cyberpunk Toggle on the main terminal dumps OpenCV-processed images (`.png`) and diagnostic text logs (`.txt`) into `logs/` for every capture.

---

## 🔒 Security & Cryptography

*   **Bcrypt Hashed Authentication:** Passwords and password recovery hints are salted and hashed using `bcrypt.gensalt()`, stored securely in a local SQLite database (`recon_cas_secure.db`). Plaintext credentials are never persisted.
*   **Password Override (Reset):** A secure recovery protocol allows users to reset passwords by verifying their hashed secret hint.
*   **Audit Logging:** Successful logins, evaluated equations, and blocked unauthorized inputs are logged with timestamps and user IDs.
*   **Zero-Trust Whitelist:** Restricts mathematical inputs strictly to permitted characters and algebraic symbols.

---

## 📂 Project Directory Structure

```text
ReconCAS/
├── core/
│   ├── __init__.py
│   ├── auth_engine.py          # SQLite DB, Bcrypt Hashing, Audit Logging
│   ├── math_engine.py          # SymPy Parser, Syntax-Aware Normalization, Operation Dispatcher
│   └── document_engine.py      # PyMuPDF Document Batch Processor, Resolution Preservation
├── vision/
│   ├── __init__.py
│   └── ocr_engine.py           # Multi-PSM Scoring, Line Slicing, Token Confusion Correction
├── gui/
│   ├── __init__.py
│   ├── theme.py                # Cyberpunk Theme Definitions & Styling
│   ├── widgets.py              # AnimatedToggle Switch Widget
│   ├── auth_window.py          # AuthGUI (Login, Registration, Password Reset)
│   ├── terminal_window.py      # TerminalGUI (Command Center, Live Monitoring, Snipping)
│   ├── lab_window.py           # LabWindow (5X CAS Lab, 2D/3D Matplotlib)
│   ├── sandbox_window.py       # SandboxWindow (3D Kinetic Space Simulator)
│   ├── document_window.py      # DocumentWindow (Batch Scanner, Confidence & Warning UI)
│   └── app_windows.py          # Facade Re-exporting all GUI Classes (Backward Compatible)
├── tests/
│   ├── __init__.py
│   ├── test_auth.py            # DB Isolation, Bcrypt Hashing, Password Reset
│   ├── test_math.py            # Unicode Tokens, Case-Insensitivity, Roots/Integrals, Whitelist
│   ├── test_ocr.py             # False Positive Rejection, Confusion Correction, Segmentation
│   └── test_document.py        # PNG/JPG/PDF Batch Tests, 30-Page Limit, Error Handling
├── guncellemeler/
│   └── SURUM_V0.1_BETA_RAPORU.md # Detaylı Sürüm, Test ve Hata Çözüm Raporu (BUG-001..BUG-021)
├── logs/                       # Diagnostic OCR outputs (Generated dynamically in Debug Mode)
├── requirements.txt            # Dependencies
└── main.py                     # System Bootloader
```

---

## 🛡️ Quality Assurance & Test Suite

The `tests/` directory contains an automated test suite built upon Python's native `unittest` framework (27 comprehensive tests, 100% passing):

*   **test_math.py**: Arithmetic accuracy, Unicode tokens (`π`, `∞`, `√`, `∫`, `×`, `÷`), case-insensitive whitelist (`Abs`, `Matrix`, `Eq`), syntax-aware root/integral parsing, absolute value `|x|`, operation dispatching, and security injection blocking.
*   **test_auth.py**: Isolated temporary database tests verifying Bcrypt salting/hashing, authentication cycles, and password overrides.
*   **test_ocr.py**: Multi-PSM scoring, token confusion corrections (`ly -> y`, `lx -> x`, `Ix -> x`), false-positive natural language filtering (`crore/ serine iar` rejection), and multi-equation segmentation.
*   **test_document.py**: PNG, JPG, single/multi-page PDF analysis, `MAX_PDF_PAGES = 30` page limit enforcement, unsupported extension handling, and progress callbacks.

To execute the test suite, run:
```bash
python -m unittest discover -s tests
```

---

## 📦 Release Updates & Changelog

V0.1 BETA testleri (*Simple Algebra Practice Worksheet.pdf*) sırasında tespit edilen 28 hatanın (BUG-001 - BUG-021 ve BUG-PDF-001 - BUG-PDF-007) teknik kök nedenleri, uygulanan algoritmik çözümler, 4 katmanlı mimari refaktörü ve test dökümleri için:

👉 **[Sürüm V0.1.1 BETA Detaylı Hata Çözüm ve Test Raporu](guncellemeler/SURUM_V0.1_BETA_RAPORU.md)**

---

## 🚀 Installation & Setup

Prerequisites: Python 3.8+ and Tesseract-OCR must be installed on your system.

### Step 1: Install Tesseract-OCR
For Windows, download and install Tesseract. Ensure the installation path matches the default:
`C:\Program Files\Tesseract-OCR\tesseract.exe`

### Step 2: Clone the Repository
```bash
git clone https://github.com/yunus-EmreX/ReconCAS-Reconnaissance-Computer-Algebra-System-.git
cd ReconCAS
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Boot the Application
```bash
python main.py
```
*(Note: The SQLite database will be generated automatically upon first launch. Use `[ CREATE_ACCOUNT ]` to register your first operator credential before logging in.)*

---

## 🔮 Future Roadmap

*   **Current Specification:** The Document Engine processes documents up to 30 pages (`MAX_PDF_PAGES = 30`) to balance memory and OCR throughput, displaying a clear notice in the UI when larger documents are truncated.
*   **Future Target (V0.1 Final):** Full multi-threaded parallel page indexing allowing continuous batch processing of massive (80+ page) engineering documents with full spatial bounding box tracking.

---

License: This project is licensed under the Apache License 2.0. See the LICENSE file for details.

