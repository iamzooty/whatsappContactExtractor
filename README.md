# 📱 WhatsApp Contact Extractor (ZootyGrow)

A fast, lightweight, and privacy-focused Django web application to extract, clean, normalize, and export WhatsApp group contacts into clean CSV spreadsheets ready for bulk messaging, Google Contacts, and CRMs.

---

## 🎬 Video Demo

<p align="center">
  <video src="assets/demo.webm" width="100%" controls="controls" autoplay loop muted></video>
</p>

> 🎥 **Watch Demo**: If the player does not load automatically in your browser, [click here to view the screencast](assets/demo.webm).

---

## ✨ Key Features

- **⚡ Instant Contact Extraction**: Parses WhatsApp Web exported HTML files in milliseconds.
- **📞 Smart Phone Normalization**:
  - Automatically converts Nigerian local numbers (`080...`, `090...`, `070...`, `081...`, `091...`) to international standard (`234`).
  - Supports international country codes (`+1`, `+44`, `+233`, `+254`, etc.).
  - Strips WhatsApp's hidden Unicode directional characters (`\u200e`, `\u202a-\u202e`) and extra spacing.
- **🏷️ Customizable Contact Prefixes**: Personalize how contacts are labeled in the exported spreadsheet (e.g. `ZG1`, `Lead1`, `TechGroup1`).
- **🎯 Intelligent Deduplication**: Automatically drops duplicate numbers so you never message the same person twice.
- **📊 3-Column CSV Export**: Generates a standard 3-column CSV (`Phone Number`, `Name/Tag`, `Country Code`) compatible with:
  - Google Contacts (<kbd>contacts.google.com</kbd>)
  - Excel / Google Sheets
  - Bulk WhatsApp Broadcast & SMS tools
- **🔒 100% Private & Local**: Your chats and contact numbers never leave your computer. All processing happens locally on your machine.
- **🎨 Modern, Sleek UI**:
  - WhatsApp-inspired Emerald/Teal modern design system.
  - Interactive drag-and-drop file upload target with live file name & file size detection.
  - Live preview table showing extracted contacts with a 1-click **"Copy Numbers"** clipboard button.
  - Direct file attachment downloads via Django `FileResponse`.

---

## 🛠️ How to Save the WhatsApp Web HTML File

WhatsApp Web is a Single Page Application (SPA) built with React. To ensure your saved file contains the live group members:

1. Open **[web.whatsapp.com](https://web.whatsapp.com)** in your browser (Chrome, Brave, Edge, or Firefox).
2. Click on the group chat you want to export.
3. Click the **Group Header / Name** at the top to open the Group Info drawer on the right.
4. Press <kbd>Ctrl + S</kbd> (or <kbd>Cmd + S</kbd> on Mac).
5. ⚠️ **IMPORTANT**: In the save dialog, select **"Webpage, Complete"** (not *"HTML Only"*). 
   - *"Webpage, Complete"* forces the browser to snapshot the live in-memory JavaScript DOM with all group members.
6. Upload the `.html` file into **ZootyGrow**, choose your contact prefix, and click **Extract Contacts**.

---

## 📂 Project Architecture

```text
whatsappContactExtractor/
├── ZootyGrow/                # Django project configuration
│   ├── settings.py           # Configured for static and media uploads
│   ├── urls.py               # Application routes & media routing
│   ├── wsgi.py
│   └── asgi.py
├── pages/                    # Core extractor app
│   ├── models.py             # Documents model with FileField
│   ├── forms.py              # UpFile form with prefix & country filters
│   ├── views.py              # Resilient extraction logic & download view
│   ├── tests.py              # Automated test suite
│   └── migrations/           # Database migrations
├── templates/                # Responsive HTML5 templates
│   ├── base.html             # Base layout with navbar & flash alerts
│   ├── home.html             # Landing page & feature overview
│   ├── extract.html          # Drag-and-drop upload interface
│   ├── successful.html       # Metrics summary & contact preview table
│   └── sender.html           # Campaign broadcast feature preview
├── static/                   # Static design assets
│   ├── bootstrap/            # Bootstrap 5 CSS & JS
│   ├── styles/sty1.css       # Custom modern design stylesheet
│   └── images/               # Site graphics
├── media/                    # Local user uploads & generated CSV exports
├── assets/                   # Repository media (demo video screencast)
│   └── demo.webm
├── requirements.txt          # Python dependencies
├── .gitignore                # Git ignore rules
└── manage.py
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10, 3.11, or 3.12
- Git

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/iamzooty/whatsappContactExtractor.git
   cd whatsappContactExtractor
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Apply database migrations:**
   ```bash
   python manage.py migrate
   ```

5. **Start the development server:**
   ```bash
   python manage.py runserver
   ```

6. Open your browser and navigate to **`http://127.0.0.1:8000/`**.

---

## 🧪 Running Automated Tests

To run the unit test suite verifying views, URL routing, phone number normalization, and CSV downloads:

```bash
python manage.py test
```

Expected output:
```text
Found 5 test(s).
Creating test database for alias 'default'...
System check identified no issues (0 silenced).
.....
Ran 5 tests in 0.058s - OK
Destroying test database for alias 'default'...
```

---

## 🗺️ Roadmap

- [ ] Direct WhatsApp Web Console script helper to bypass large group header caps (1,000+ members).
- [ ] Direct WhatsApp Campaign Bulk Sender feature (scheduled broadcast studio).
- [ ] Direct VCF (vCard) export format for direct phone import without CSV mapping.

---

## 📄 License

This project is licensed under the MIT License - feel free to use and adapt it for your personal or commercial projects.

---

## 👤 Author

Developed by **[iamzooty](https://github.com/iamzooty)**.
