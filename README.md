# SlideTranslator

SlideTranslator is a Python tool that uses an LLM to translate the text in PowerPoint (`.pptx`) presentations while preserving the original formatting. It provides a simple web interface built with Streamlit for easy use.

## Features

-   **Preserves Formatting**: Translates text without altering the layout, fonts, colors, or images.
-   **Comprehensive Extraction**: Extracts text from text boxes, shapes, tables, and presenter notes.
-   **Batch Translation**: Sends all text to the translation API in a single request for efficiency.
-   **Secure**: Uses a `.env` file to manage the LLM API key securely.
-   **Web UI**: Simple and intuitive interface powered by Streamlit.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd SlideTranslator
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    # Windows
    python -m venv .venv
    .\.venv\Scripts\activate

    # macOS / Linux
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  **Install the required dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up your environment variables:**
    -   Create a file named `.env` in the root directory of the project.
    -   Add your OpenAI API key to the file like this:
        ```
        OPENAI_API_KEY="sk-YourSecretApiKey"
        ```

## How to Run

With your virtual environment activated, run the Streamlit application from the root directory:

```bash
streamlit run app.py
```

Your web browser should open with the application running locally at `http://localhost:8501`.

## How to Use

1.  Open the application in your browser.
2.  Use the "Upload your .pptx file" button to select a presentation.
3.  Choose the target language for the translation from the dropdown menu.
4.  Click the "Translate Presentation" button.
5.  Wait for the process to complete.
6.  Click the "Download" button to save your translated presentation.
