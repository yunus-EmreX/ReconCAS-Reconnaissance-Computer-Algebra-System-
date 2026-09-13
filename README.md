```markdown
# ReconCAS (OpticCAS-Terminal)
**Vision-Based Computer Algebra System**

ReconCAS is a locally hosted desktop application that captures raw image data from the screen buffer, routes it through an Optical Character Recognition (OCR) pipeline, and translates it into symbolic mathematical expressions for advanced analysis. Unlike standard calculators, it eliminates manual input by allowing users to select screen regions (bounding boxes) to extract and evaluate equations instantly.

With its latest architectural update (V9), the project has moved away from a monolithic structure. It is now highly modular, featuring enterprise-grade security protocols, robust memory management, and significant OCR optimizations.

## ⚙️ Architecture and Technical Capabilities

The application operates on 3 decoupled layers (Core, Vision, GUI):

### 1. Vision Engine (Image Processing & OCR)
*   **Image Enhancement:** Selected screen regions are captured via Pillow, upscaled using bicubic/bilinear interpolation, converted to grayscale, and processed through high-contrast multipliers.
*   **Smart Math Corrector:** Common Tesseract OCR errors (e.g., reading `l` as `1` or `O` as `0`) are rectified using specialized Regex patterns. This ensures that legitimate mathematical functions like `sin`, `cos`, and `log` remain uncorrupted during the correction phase.
*   **Frame Differencing:** During Live Scanning mode, the system hashes (MD5) consecutive frames. If the visual data remains unchanged, the OCR engine is bypassed. This optimization prevents CPU spiking and minimizes resource overhead.

### 2. Math Engine (Secure Symbolic Analysis)
*   **Lexical Validation (Whitelist Layer):** To prevent arbitrary code execution (eval vulnerabilities) from malicious or hallucinated OCR outputs, incoming text is subjected to strict lexical validation. Only whitelisted mathematical tokens `[0-9, x, y, +, -, *, /, sin, cos...]` are permitted.
*   **SymPy Integration:** Sanitized strings are passed to the SymPy engine, which autonomously resolves implicit multiplications (e.g., mapping `2x` to `2*x`) and parses the expression.

### 3. Core & Security
*   **Cryptography:** The application utilizes a local SQLite database (`recon_cas_secure.db`). User passwords and recovery hints are never stored in plaintext; they are securely salted and hashed using the `bcrypt` algorithm.
*   **Session Logging:** All successful authentications, blocked malicious inputs, and evaluated equations are logged into the database with corresponding user IDs and timestamps.

### 4. CAS Laboratory & Sandbox Studio
*   **CAS Laboratory:** Dedicated functions allow users to compute analytical derivatives, indefinite integrals, polynomial factorization, and root solutions with a single click. Single-variable (x) expressions are instantly plotted on a Matplotlib 2D axis.
*   **Sandbox (Universe Simulator):** Users can define a base function (e.g., `sin(x)*cos(y)`) and multiply it by a spatial modifier/warp function (e.g., `x^2`). The system computes the resulting $Z$ matrix and renders a 3D Surface plot. Infinities (NaN/Inf) are filtered out via `np.errstate`, allowing the system to accurately calculate and display the absolute minimum/maximum (resistance) peaks of the matrix.
*   **Memory Management:** To prevent standard Matplotlib memory leaks across consecutive renders, explicit garbage collection (`gc.collect()`) and `plt.close('all')` are aggressively invoked during graph updates and window terminations.

## 📂 Project Structure

```text
ReconCAS/
├── core/
│   ├── __init__.py
│   ├── auth_engine.py      # bcrypt, SQLite DB, and Logging
│   └── math_engine.py      # SymPy Parser and Whitelist Validator
├── vision/
│   ├── __init__.py
│   └── ocr_engine.py       # Tesseract, Pillow, Frame Differencing
├── gui/
│   ├── __init__.py
│   └── app_windows.py      # Tkinter UI (Login, Terminal, Lab, Sandbox)
└── main.py                 # Bootloader
🛠️ Installation Guide
Python 3.8+ and Tesseract-OCR must be installed on your system.

Step 1: Install Tesseract-OCR

For Windows, download and install the Tesseract installer.

Ensure the installation path matches the default: C:\Program Files\Tesseract-OCR\tesseract.exe (The code explicitly targets this path).

Step 2: Clone the Repository

Bash
git clone (https://github.com/yunus-EmreX/ReconCAS-Reconnaissance-Computer-Algebra-System-.git)
cd ReconCAS
Step 3: Install Dependencies
Install the required Python packages via pip:

Bash
pip install pytesseract pillow sympy numpy matplotlib bcrypt
Step 4: Boot the Application
Once the environment is ready, execute the main script:

Bash
python main.py
(Note: The SQLite database will be generated automatically upon the first launch. Use CREATE_ACCOUNT to register your first operator credential before logging in.)

📜 License
This project is licensed under the Apache License 2.0. See the LICENSE file for detail
