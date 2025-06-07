# 🎧 DIN Test Web App

This Django application hosts a **Digits-in-Noise (DIN) test** with an associated questionnaire for hearing screening and research. It supports dynamic audio test configuration, multiple languages, and structured results collection.

---

## 📂 Project Structure

```
dinweb/
├── db.sqlite3              # Default SQLite DB
├── din/                    # Main Django app
├── logs/                   # Logs directory
├── manage.py               # Django CLI entry point
├── media/                  # Audio test data: <test_name>/snr<snr_level>/file.wav
├── scripts/
│   ├── audio_mixer.py      # Mix audio files with noise at various SNRs
│   └── rescale_sound.py    # Rescale audio to target dB SNR
├── settings/               # Django settings module
├── static/                 # Static assets (CSS/JS/audio)
├── venv/                   # Virtual environment (not tracked in Git)
```

---

## 🚀 Features

* DIN test execution with stepwise SNR adjustment
* Questionnaire for participant metadata
* Admin panel for test and result management
* Audio processing scripts to prepare test data

---

## ⚙️ Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/jacobdenobel/dinweb.git
cd dinweb
```

### 2. Create and Activate Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run Migrations

```bash
python manage.py migrate
```

### 5. Create Admin User (Optional)

```bash
python manage.py createsuperuser
```

### 6. Start the Server

```bash
python manage.py runserver
```

Access the site at [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## 🧪 DIN Test Audio Preparation

### 🎛 `scripts/audio_mixer.py`

Use this script to **generate DIN audio stimuli** by mixing clean digits with a noise file at various SNR levels.

**Usage:**

```bash
python scripts/audio_mixer.py \
    --min_snr -20 \
    --max_snr 10 \
    --increment 2 \
    --silence 0.2 \
    --save
```

**Parameters:**

* `--min_snr`, `--max_snr`, `--increment`: SNR range
* `--silence`: seconds of silence before/after
* `--dont_rescale`: skip normalization
* `--save`: actually saves output to `media/<test_name>/snr<level>/`

### 📉 `scripts/rescale_sound.py`

Use this to **rescale individual WAV files** to a target loudness (e.g., -20 dB SNR).

**Example:**

```bash
python scripts/rescale_sound.py path/to/file.wav --loud --save_inplace
```

---

## 📥 Load Tests into the Database

Once audio is ready in the `media/` directory, use the management command:

```bash
python manage.py load_test <name> \
    --test_name din \
    --language nl \
    --n_questions 24 \
    --starting_level 0 \
    --increment 2 \
    --min_level -20 \
    --max_level 10 \
    --active
```

---

## 🌐 Website Routes

| URL Pattern                                | View Name         | Description                                |
| ------------------------------------------ | ----------------- | ------------------------------------------ |
| `/`                                        | `index`           | Homepage                                   |
| `/questionary`                             | `questionary`     | User questionnaire                         |
| `/setup/<qid>/`                            | `setup`           | Test setup screen                          |
| `/test_question/<qid>/`                    | `test_question`   | Begin DIN test                             |
| `/question/<qid>/<tid>/<question_number>/` | `question`        | Test question page                         |
| `/results/`                                | `result_overview` | All test results (admin view)              |
| `/results/<qid>/`                          | `results`         | Detailed result for specific questionnaire |
| `/test_complete`                           | `test_complete`   | Completion page                            |

Use Django admin to manage test configurations, languages, and results.

---

## ✅ Requirements

* Python 3.8+
* Django 3.2+
* FFmpeg (if working with audio mixing)
* WAV files for digits and a consistent noise file

---

## 🛡 Deployment Notes

When deploying in production:

* Set `DEBUG=False` in `settings/`
* Configure allowed hosts, media/static paths
* Use Gunicorn + Nginx for serving production
* Ensure all audio files are pre-scaled and accessible

---

