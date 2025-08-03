\# 🤖 Gemini-Powered Job Scraper



\[!\[Python Version](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)

\[!\[License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

\[!\[Open Source](https://badges.frapsoft.com/os/v1/open-source.svg?v=103)](https://opensource.org/)



An intelligent job scraper that uses Google's Gemini Pro to parse unstructured job posting data into a clean, structured CSV format. The tool features a user-friendly web interface built with Streamlit and a powerful command-line script for batch processing.



\## ✨ Key Features



\-   \*\*AI-Powered Parsing\*\*: Leverages the Gemini API to intelligently extract and structure details from raw job descriptions.

\-   \*\*Dual Interface\*\*:

&nbsp;   -   \*\*Web App\*\*: An easy-to-use Streamlit interface for interactive scraping.

&nbsp;   -   \*\*CLI\*\*: A robust command-line script (`app.py`) for automated, large-scale scraping.

\-   \*\*Flexible Input\*\*: Accepts a single careers page URL (and auto-discovers job links) or a CSV file with a list of URLs.

\-   \*\*Dynamic \& Static Scraping\*\*: Handles both simple HTML pages (with `requests` and `BeautifulSoup`) and JavaScript-heavy dynamic sites (with `Playwright`).

\-   \*\*Data Validation\*\*: Includes post-processing logic to clean and normalize the AI-generated data for consistency.

\-   \*\*Concurrent Processing\*\*: Uses `ThreadPoolExecutor` to make parallel calls to the Gemini API, significantly speeding up large jobs.



\## 🚀 Demo (Streamlit App)



The web interface allows you to easily input a careers page or upload a CSV to start the scraping process.



!\[Streamlit App Demo](https://placehold.co/800x550/2d3748/ffffff?text=Streamlit%20UI%20Screenshot\\n\\n1.%20Enter%20a%20Careers%20Page%20URL\\n2.%20Or%20Upload%20a%20CSV%20of%20URLs\\n3.%20Click%20'Run%20Scraper'\\n4.%20View%20%26%20Download%20Results)



\## 🛠️ Technology Stack



\-   \*\*Backend\*\*: Python

\-   \*\*Web UI\*\*: Streamlit

\-   \*\*AI Model\*\*: Google Gemini Pro

\-   \*\*Web Scraping\*\*: Requests, BeautifulSoup4, Playwright

\-   \*\*Data Handling\*\*: Pandas



\## ⚙️ Installation \& Setup



Follow these steps to get the project running on your local machine.



\### 1. Clone the Repository



```bash

git clone \[https://github.com/avismic/job\_scraper.git](https://github.com/avismic/job\_scraper.git)

cd job\_scraper

```



\### 2. Create a Virtual Environment



It's highly recommended to use a virtual environment to manage dependencies.



```bash

\# For Windows

python -m venv venv

venv\\Scripts\\activate



\# For macOS/Linux

python3 -m venv venv

source venv/bin/activate

```



\### 3. Install Dependencies



Install all the required Python packages from `requirements.txt`.



```bash

pip install -r requirements.txt

```



\### 4. Install Playwright Browsers



Playwright requires browser binaries for dynamic scraping. This command will download them.



```bash

playwright install

```



\### 5. Set Up Environment Variables



The application needs a Google API key to use Gemini.



\-   Create a file named `.env` in the root directory of the project.

\-   Get your API key from \[Google AI Studio](https://aistudio.google.com/app/apikey).

\-   Add your key to the `.env` file:



```env

GOOGLE\_API\_KEY="YOUR\_API\_KEY\_HERE"

```



\## ▶️ How to Use



You can run the project using either the Streamlit web app or the command-line interface.



\### Option A: Run the Streamlit Web App



This is the easiest way to use the scraper. From your terminal, run:



```bash

streamlit run streamlit\_app.py

```



Your web browser will open with the application's UI.



1\.  \*\*Enter a URL\*\*: Paste the main URL of a company's careers page. The app will try to find all the individual job posting links.

2\.  \*\*Upload a CSV\*\*: Alternatively, upload a CSV file. The file must contain a header named `url` with the direct links to job postings listed below it.

3\.  Click \*\*Run Scraper\*\* and watch the magic happen!

4\.  Once finished, you can view the results on the page and download them as a CSV file.



\### Option B: Run the Command-Line Script



For batch processing or automation, use `app.py`.



The script takes an input CSV file and an output CSV file as arguments.



1\.  Prepare your `input.csv` file with a `url` column.

2\.  Run the script from your terminal:



```bash

python app.py input.csv output.csv

```



\-   `input.csv`: The path to your source file containing job URLs.

\-   `output.csv`: The path where the final structured data will be saved.



The script will print its progress to the console and create the `output.csv` file upon completion.



\## 📂 Project Structure



```

.

├── app.py              # Command-line interface script

├── streamlit\_app.py    # Streamlit web application

├── requirements.txt    # Project dependencies

├── .env                # For API keys (needs to be created)

├── input.csv           # Sample input for the CLI

├── scraper/            # Modules for scraping web pages

│   ├── static\_scraper.py

│   ├── dynamic\_scraper.py

│   └── link\_extractor.py

├── gemini/             # Module for parsing with Gemini AI

│   └── parser.py

└── utils/              # Helper modules

&nbsp;   └── validators.py   # For cleaning and normalizing data

```



\## 🤝 How to Contribute



Contributions are welcome! If you'd like to improve the project, please follow these steps:



1\.  \*\*Fork\*\* the repository.

2\.  Create a new \*\*branch\*\* (`git checkout -b feature/YourFeatureName`).

3\.  Make your changes and \*\*commit\*\* them (`git commit -m 'Add some feature'`).

4\.  \*\*Push\*\* to the branch (`git push origin feature/YourFeatureName`).

5\.  Open a \*\*Pull Request\*\*.



\## 📄 License



This project is licensed under the MIT License. See the \[LICENSE](LICENSE) file for details.



