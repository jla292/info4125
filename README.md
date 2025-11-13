# Cornell Fact Checker – Chrome Extension + Flask Backend

This repository contains:

* A **Flask backend** that runs a fact-checking model using Cornell-specific data.
* A **Chrome extension** that sends highlighted text from web pages to the backend for verification.

---

## Repository Structure

```text
/
├── backend/
│   ├── appFAKERV3.py              # Flask backend for fact checking
│   ├── cornell_classes_2025.json
│   ├── cornell_mealplans_2025.json
│   └── financial_aid_facts.json
│
└── extension/
    ├── background.js
    ├── content.js
    ├── cornell_seal.png
    ├── manifest.json
    ├── popup.html
    ├── popup.js
    └── styles.css
```

---

## Prerequisites

* Python 3.x installed
* Google Chrome installed

---

## 1. Backend Setup (Flask Server)

### Step 1: Download or clone the repository

Download the repository as a ZIP and extract it, or clone it:

```bash
git clone <repo-url>
```

Then move into the backend folder:

```bash
cd <repo-folder>/backend
```

### Step 2: Create and activate a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate      # Mac / Linux
venv\Scripts\activate         # Windows
```

### Step 3: Install required libraries

Inside the virtual environment, run:

```bash
pip install flask flask-cors numpy pandas nltk sentence-transformers transformers torch
```

### Step 4: Run the backend

From the `backend` folder, run:

```bash
python appFAKERV3.py
```

This will start the Flask server (usually on `http://127.0.0.1:5000` or similar).
Keep this terminal window open while you use the extension.

---

## 2. Chrome Extension Setup

### Step 1: Open the Extensions page in Chrome

In the address bar, go to:

```text
chrome://extensions/
```

### Step 2: Enable Developer Mode

Turn on **Developer Mode** using the toggle in the top-right corner.

### Step 3: Load the unpacked extension

1. Click **"Load unpacked"**.
2. Select the `extension` folder from this repository (the folder that contains `manifest.json`, `background.js`, etc.).
3. The extension should now appear in your list of extensions and (optionally) in the Chrome toolbar.

---

## 3. Using the Extension

Once:

* The **backend** is running (from `appFAKERV3.py`), and
* The **Chrome extension** is loaded in `chrome://extensions/`,

you can use the fact checker as follows:

1. Navigate to any webpage in Chrome.
2. **Highlight** the text you want to fact check.
3. **Right-click** the highlighted text.
4. In the menu, **choose the Cornell Fact Checker extension**.
5. The extension will send the selected text to the backend.
6. The extension will then display the result indicating whether the claim appears true, false, or otherwise, based on the backend’s fact-checking logic along with a site for you to navigate to for further information

---

## Notes

* Make sure the backend server is running **before** using the extension; otherwise, the extension will not be able to get a response.
* If the backend runs on a different URL or port than expected, you may need to update the API endpoint in `background.js` accordingly.
