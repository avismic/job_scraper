# 🤖 Gemini-Powered Job Scraper

[![Python Version](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An intelligent job scraper that uses Google's Gemini Pro to parse unstructured job posting data into a clean, structured CSV format. This tool features a user-friendly web interface built with Streamlit and a powerful command-line script for batch processing.

---

## ✨ Key Features

-   **AI-Powered Parsing**: Leverages the Gemini API to intelligently extract and structure details from raw job descriptions.
-   **Dual Interface**:
    -   **Web App**: An easy-to-use Streamlit interface for interactive scraping.
    -   **CLI**: A robust command-line script (`app.py`) for automated, large-scale scraping.
-   **Flexible Input**: Accepts a single careers page URL (and auto-discovers job links) or a CSV file with a list of URLs.
-   **Dynamic & Static Scraping**: Handles both simple HTML pages and JavaScript-heavy dynamic sites.
-   **Concurrent Processing**: Uses parallel processing to make multiple calls to the Gemini API at once, significantly speeding up large jobs.

---

## 🚀 Demo (Streamlit App)

The web interface allows you to easily input a careers page or upload a CSV to start the scraping process.

![Streamlit App Demo](https://drive.google.com/file/d/1kU9hsMVnioX3LRwZMuNmaJlxe1_qu3ZU/view?usp=sharing)

---

## ⚙️ Installation & Setup

Follow these steps to get the project running on your local machine.

### 1. Clone the Repository

```bash
git clone [https://github.com/avismic/job_scraper.git](https://github.com/avismic/job_scraper.git)
cd job_scraper
```

### 2. Create a Virtual Environment

It's highly recommended to use a virtual environment to manage dependencies.

**For Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**For macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

Install all the required Python packages.

```bash
pip install -r requirements.txt
```

### 4. Install Playwright Browsers

Playwright requires browser binaries for dynamic scraping. This command will download them.

```bash
playwright install
```

### 5. Set Up Environment Variables

The application needs a Google API key to use Gemini.

-   Create a file named `.env` in the root directory of the project.
-   Get your API key from **[Google AI Studio](https://aistudio.google.com/app/apikey)**.
-   Add your key to the `.env` file like this:

```env
GOOGLE_API_KEY="YOUR_API_KEY_HERE"
```

---

## ▶️ How to Use

You can run the project using either the Streamlit web app or the command-line interface.

### Option A: Run the Streamlit Web App (Recommended)

This is the easiest way to use the scraper. From your terminal, run:

```bash
streamlit run streamlit_app.py
```

Your web browser will open with the application's UI.

1.  **Enter a URL**: Paste the main URL of a company's careers page. The app will try to find all the individual job posting links.
2.  **Upload a CSV**: Alternatively, upload a CSV file. The file must contain a header named `url`.
3.  Click **Run Scraper** and wait for it to finish.
4.  Once complete, you can view the results on the page and download them as a CSV file.

### Option B: Run the Command-Line Script

For batch processing or automation, use `app.py`.

1.  Prepare your `input.csv` file with a `url` column.
2.  Run the script from your terminal:

```bash
python app.py input.csv output.csv
```

-   `input.csv`: The path to your source file containing job URLs.
-   `output.csv`: The path where the final structured data will be saved.

---

## 🤝 How to Contribute

Contributions are welcome! If you'd like to improve the project, please follow these steps:

1.  **Fork** the repository.
2.  Create a new **branch** (`git checkout -b feature/YourFeatureName`).
3.  Make your changes and **commit** them (`git commit -m 'Add some feature'`).
4.  **Push** to the branch (`git push origin feature/YourFeatureName`).
5.  Open a **Pull Request**.

---

## 📄 License

This project is licensed under the MIT License.
