# AI Web Scraper

An AI agent web scraper that uses Streamlit as a UI, custom scraping methods, and natural language parsing with Ollama to let users interactively scrape and parse website content.

## Overview

The project consists of three main components:

- **Scraping Module**:  
  Contains functions to scrape website content and process DOM data in [scrape.py](scrape.py) (e.g., [`scrape_website_combined`](scrape.py)).  

- **Parsing Module**:  
  Uses the Ollama API to parse scraped content, defined in [parse.py](parse.py) (e.g., [`parse_with_ollama`](parse.py)).  

- **Main Application**:  
  Provides the Streamlit UI available in [main.py](main.py) to drive the scraping and parsing workflows.

## Features

- **Interactive UI**:  
  Built with Streamlit for a responsive interface.

- **Multi-Method Scraping**:  
  Offers different scraping techniques (e.g., Brightdata integration) in [scrape.py](scrape.py) to get past even the most advanced captchas on websites.

- **Content Parsing with AI**:  
  Parses and extracts meaningful data based on user-provided descriptions in [parse.py](parse.py).

## Installation

## Clone the Repository

   ```sh
   git clone <https://github.com/Fabelouzz/AI-Agent-Webscraper>
   cd AI-Agent-Webcraper
```
   ## Setup the Virtual Environment

```bash
python -m venv scrapeenv
```

### Activate the virtual environment

**On Windows:**
```bash
scrapeenv\Scripts\activate.bat
```

**On macOS/Linux:**
```bash
source scrapeenv/bin/activate
```

---

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

# Usage

## 1. Run the Application

**Start the Streamlit app:**
```bash
streamlit run main.py
```

## 2. Using the App

Enter the website URL and click **"Scrape Website"**.  
This will display the DOM content once scraped.

## 3. Parse the Content

Once you have the content you want, then click **"Parse Content"**  
to see the parsed results.

---

# Project Structure

- **main.py**  
  Main Streamlit app (`main.py`)

- **scrape.py**  
  Scraping functions (`scrape.py`)

- **parse.py**  
  Parsing functions (`parse.py`)

- **requirements.txt**  
  Project dependencies

- **.gitignore**  
  Git ignore patterns

- **README.md**  
  Project documentation
