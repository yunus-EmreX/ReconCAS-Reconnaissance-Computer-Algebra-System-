# 🌌 ReconCAS (OpticCAS-Terminal) // V0.1.4 BETA
**Vision-Based Computer Algebra System & Kinetic Sandbox**

ReconCAS is a locally hosted desktop application that captures raw image data from the screen buffer or document files (PDF/Görsel), routes it through an Optical Character Recognition (OCR) pipeline, and translates it into symbolic mathematical expressions for advanced analysis. Unlike standard calculators, it eliminates manual input by allowing users to select screen regions (bounding boxes) or upload documents to extract, evaluate, and visualize equations instantly.

With the **V0.1.4 BETA** release, ReconCAS introduces a massive **Root Superuser Mega Patch** featuring a modular sidebar architecture. The 14 new operational capabilities include a Live System Monitor, OCR Calibration Panel, Real-time Theme Engine, Database Backup & Restore, Professional PDF Report Generation (fpdf2), a Plugin System, LSB Steganography Module, User Session Tracking Heatmaps, a Global Kill Switch, and an interactive Cyberpunk World Map Network Visualization.

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
*   **Windows High-DPI Awareness:** Automatically enables process-level Per-Monitor DPI Awareness (`SetProcessDpiAwareness(2)`). Eliminates the 25% coordinate displacement on 125%/150% scaled displays, ensuring 1:1 pixel alignment between user mouse snips and the screen buffer.
*   **Topmost Occlusion Guard:** Hides snipping overlays and delays terminal deiconification until after `ImageGrab` captures the screen buffer, preventing the dark GUI window (`#050505`) from obstructing captured equations.
*   **Adaptive Scaling & Subpixel Contrast:** Evaluates high-contrast normalized grayscale and adaptive interpolation (optimal 96px height) without destructive binarization, preserving decimal points and small punctuation marks.
*   **Dark Mode Guard:** The engine calculates average pixel intensity. In dark environments (`np.mean < 127`), it inverts colors to read dark-mode editors and PDFs flawlessly.
*   **Vertical 4-Operation Arithmetic Engine:** Detects and merges multi-line column arithmetic (vertical addition, subtraction, multiplication, division) into single unified expressions (e.g., `27` over `+ 3` $\rightarrow$ `27 + 3`), while discarding standalone question indices (`2.`, `1)`).
*   **Multi-Criteria Scoring & PSM Selection:** Evaluates PSM modes (6, 11, 4) using OCR confidence, parse validity, structural balance, and math character density, penalizing non-math prose.
*   **Token Confusion Correction & Multi-Equation Segmentation:** Rectifies common OCR confusions (`ly -> y`, `lx -> x`, `Ix -> x`, `02H -> 0=2`) and splits multi-equation lines automatically.
*   **Live Scanning & Frame Differencing:** Continuously hashes (MD5) frames during live monitoring to bypass OCR when visual data is static, minimizing CPU load.

### 2. Math Engine (Zero-Trust Symbolic Analysis)
*   **Strict Lexical Parser (Whitelist):** Incoming text is normalized first, then validated against a canonical case-insensitive whitelist (`SAFE_WORDS`) and character set (`ALLOWED_TOKENS`), completely blocking code injection vulnerabilities (`__import__`, `eval`, arbitrary system commands).
*   **Syntax-Aware Normalization:** Automatically converts Unicode math characters (`π`, `∞`, `√`, `∫`, `×`, `÷`, `²`, `³`, `¹`), roots (`√x` -> `sqrt(...)`), integrals (`∫x dx` -> `integrate(x, x)`), absolute values (`|x|` -> `Abs(x)`), and normalizes trailing question syntax (`27 + 3 = ?` -> `27 + 3`, `7,41 =` -> `7.41`).
*   **Operation Dispatcher:** First-class dispatching for symbolic operations (`diff`, `integrate`, `limit`, `series`, `factor`, `simplify`, `Matrix`, `solve`). Safely routes pure arithmetic directly to `evaluate_basic()` without forcing algebraic CAS Lab modals.

### 3. Document Engine (High-Resolution Batch Processing)
*   Integrates PyMuPDF (`fitz`) and OpenCV to analyze images (`.png`, `.jpg`, `.jpeg`, `.bmp`, `.tiff`, `.tif`) and multi-page PDFs.
*   Preserves full 200 DPI resolution, detects text line regions, and outputs rich metadata including OCR confidence, raw text, normalized text, and SymPy validation status.

### 4. GUI Layer (Modular Tkinter & Matplotlib)
*   Cyberpunk terminal styling (`#050505` dark theme, `#00FF41` matrix green, `#00FFFF` cyan).
*   Decoupled modules: `theme.py`, `widgets.py`, `auth_window.py`, `terminal_window.py`, `lab_window.py`, `sandbox_window.py`, `document_window.py`, `admin_window.py`, and `app_windows.py` (facade).

---

## 🛠️ Core Modules & Capabilities

### 👑 Cyberpunk Admin Puppet Matrix (Superuser God Mode)
Integrated orchestration console accessible exclusively to authenticated root operators:
*   **Simulated Distributed Puppet Nodes:** Real-time health monitors, ping latency diagnostics, and cache flushing for worker clusters (Vision GPU Cluster, Neural OCR Synth, Quantum CAS Relay).
*   **Future Modular Concept Toggles:** Dynamic operational prototype controls for continuous fluid dynamics, distributed P2P OCR mesh, quantum heuristic rewriting, and multi-spectral document scanning.
*   **Live Matrix Telemetry & Audit Stream:** Real-time terminal log viewer, Overclock Burst simulation, and zero-knowledge cryptographic integrity auditing.
*   **Database & Memory Maintenance:** Zero-latency SQLite VACUUM optimization, complete calculation history purging, and live Python Garbage Collection triggering.

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

*   **Zero-Plaintext Superuser (Root) Cryptography:** Root authentication is verified using salted SHA-256 one-way cryptographic signatures. Root credentials never appear in plaintext anywhere in the codebase or database, leaving zero hints or artifacts during code inspection.
*   **Bcrypt Hashed Authentication:** Standard passwords and password recovery hints are salted and hashed using `bcrypt.gensalt()`, stored securely in a local SQLite database (`recon_cas_secure.db`). Plaintext credentials are never persisted.
*   **Password Override (Reset):** A secure recovery protocol allows users to reset passwords by verifying their hashed secret hint.
*   **Audit Logging:** Successful logins, evaluated equations, and blocked unauthorized inputs are logged with timestamps and user IDs.
*   **Zero-Trust Whitelist:** Restricts mathematical inputs strictly to permitted characters and algebraic symbols.

---

## 📂 Project Directory Structure

```text
ReconCAS/
├── core/
│   ├── __init__.py
│   ├── auth_engine.py          # SQLite DB, Bcrypt Hashing, Zero-Plaintext Root Auth, Audit Logging
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
│   ├── terminal_window.py      # TerminalGUI (Command Center, Live Monitoring, Snipping, Root Hub)
│   ├── admin_window.py         # AdminPuppetWindow (Superuser Puppet Matrix & Maintenance)
│   ├── lab_window.py           # LabWindow (5X CAS Lab, 2D/3D Matplotlib)
│   ├── sandbox_window.py       # SandboxWindow (3D Kinetic Space Simulator)
│   ├── document_window.py      # DocumentWindow (Batch Scanner, Confidence & Warning UI)
│   └── app_windows.py          # Facade Re-exporting all GUI Classes (Backward Compatible)
├── tests/
│   ├── __init__.py
│   ├── test_auth.py            # DB Isolation, Bcrypt Hashing, Zero-Plaintext Root Auth, Admin Ops
│   ├── test_math.py            # Unicode Tokens, Case-Insensitivity, Roots/Integrals, Whitelist
│   ├── test_ocr.py             # False Positive Rejection, Confusion Correction, Segmentation
│   └── test_document.py        # PNG/JPG/PDF Batch Tests, 30-Page Limit, Error Handling
├── guncellemeler/
│   └── SURUM_V0.1_BETA_RAPORU.md # Detaylı Sürüm, Test ve Hata Çözüm Raporu (BUG-001..BUG-028)
├── logs/                       # Diagnostic OCR outputs (Generated dynamically in Debug Mode)
├── requirements.txt            # Dependencies
└── main.py                     # System Bootloader
```

---

## 🛡️ Quality Assurance & Test Suite

The `tests/` directory contains an automated test suite built upon Python's native `unittest` framework (**31 comprehensive tests, 100% passing**):

*   **test_math.py (11 tests)**: Arithmetic accuracy, 4-operation suffix formats (`27 + 3 = ?`, `45 - 18 =`), Turkish decimal comma (`7,41 =`), Unicode tokens (`π`, `∞`, `√`, `∫`, `×`, `÷`), case-insensitive whitelist (`Abs`, `Matrix`, `Eq`), syntax-aware roots/integrals, absolute value `|x|`, operation dispatching, and security injection blocking.
*   **test_auth.py (3 tests)**: Isolated temporary database tests verifying Bcrypt salting/hashing, zero-plaintext root authentication, password overrides, and superuser database maintenance routines.
*   **test_ocr.py (7 tests)**: Multi-PSM scoring, vertical arithmetic merging (`2.\n 27\n+ 3\n---` -> `27 + 3`), token confusion corrections (`ly -> y`, `lx -> x`, `Ix -> x`), false-positive natural language filtering (`crore/ serine iar` rejection), and multi-equation segmentation.
*   **test_document.py (10 tests)**: PNG, JPG, single/multi-page PDF analysis, `MAX_PDF_PAGES = 30` page limit enforcement, unsupported extension handling, and progress callbacks.

To execute the test suite, run:
```bash
python -m unittest discover -s tests
```

---

## 📦 Release Updates & Changelog

ReconCAS geliştirme sürecinde çözülen ve arşivlenen **tüm 35 hatanın (BUG-001 - BUG-028 ve BUG-PDF-001 - BUG-PDF-007)** kök neden analizleri, dikey 4 işlem birleştirme formülleri, High-DPI düzeltmeleri, sıfır açık metin root yetkilendirmesi ve 31 testlik doğrulama raporu için:

👉 **[Sürüm Güncelleme & Hata Çözüm Arşivi (V0.1.3 BETA)](guncellemeler/SURUM_V0.1_BETA_RAPORU.md)**


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

