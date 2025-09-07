# GrantThrive - Grant Mapping System Guide

## 1. Overview

This document provides a comprehensive guide to the GrantThrive Grant Mapping System, a powerful tool for scraping, processing, and visualizing historical grant data from the Australian Government's grants.gov.au website. This system provides councils with unprecedented insights into grant funding patterns, helping them identify opportunities, analyze trends, and make data-driven decisions.

**Key Components:**
1.  **Grant Scraper (`grant_scraper.py`):** A Python script to scrape historical grant data from grants.gov.au.
2.  **Data Processor (`grant_data_processor.py`):** A Python script to process, categorize, and enrich the scraped grant data.
3.  **Mapping Component (React):** An interactive web application for visualizing and exploring the grant data.

## 2. Deployed Mapping Component

The interactive grant mapping component has been deployed and is ready for use. You can access it at the following URL:

**[Link to Deployed Mapping Component]** (This will be provided upon final deployment)

## 3. System Components & Usage

### 3.1. Grant Scraper (`grant_scraper.py`)

**Purpose:** To scrape historical grant data from the grants.gov.au website.

**How to Run:**
1.  Ensure you have Python 3 and the required libraries (`requests`, `beautifulsoup4`) installed.
2.  Open a terminal and navigate to the directory containing the script.
3.  Run the script: `python3 grant_scraper.py`

**Customization:**
*   **Date Range:** Modify the `start_date` and `end_date` variables in the `main()` function to scrape data for a specific period.
*   **Max Pages:** Adjust the `max_pages` parameter to control the number of search result pages to scrape.

**Output:**
*   `grants_data.json`: Raw scraped grant data in JSON format.
*   `grants_data.csv`: Raw scraped grant data in CSV format.

### 3.2. Data Processor (`grant_data_processor.py`)

**Purpose:** To process the raw scraped data, categorize it, and prepare it for visualization.

**How to Run:**
1.  Ensure you have Python 3 and the `pandas` library installed.
2.  Place the `grants_data.json` or `grants_data.csv` file in the same directory.
3.  Run the script: `python3 grant_data_processor.py`

**Customization:**
*   **Categorization Logic:** Modify the `categories` dictionary in the `GrantDataProcessor` class to adjust the categorization keywords and themes.
*   **Postcode Coordinates:** Update the `postcode_coordinates` dictionary with a more comprehensive dataset for accurate mapping.

**Output:**
*   `processed_grants.json`: Enriched and categorized grant data.
*   `grant_mapping_data.json`: Data specifically formatted for the mapping component.

### 3.3. Mapping Component (React)

**Purpose:** To provide an interactive web interface for exploring the processed grant data.

**How to Integrate:**
1.  **Standalone:** Deploy the `grantthrive-mapping-component/dist` folder to any static web host.
2.  **Iframe:** Embed the deployed component in your existing website using an iframe.
3.  **React Integration:** Copy the components from `grantthrive-mapping-component/src` into your main GrantThrive application.

**Key Features:**
*   **Interactive Dashboard:** Real-time statistics on grant data.
*   **Map View:** (Placeholder) Visual representation of grant locations.
*   **List View:** Detailed list of all grants with sorting and filtering.
*   **Analytics View:** Visualizations of category and state distributions.
*   **Advanced Filtering:** Search, filter by category, state, and grant size.

## 4. Data-Driven Insights for Councils

This system empowers councils to:
*   **Identify Funding Opportunities:** Discover relevant grant programs and funding trends.
*   **Analyze Competitive Landscape:** See which organizations are receiving funding in their area.
*   **Visualize Grant Impact:** Understand the geographic distribution of grant funding.
*   **Make Data-Driven Decisions:** Use historical data to inform grant strategies.
*   **Enhance Community Engagement:** Share grant data with the community to promote transparency.

## 5. Future Enhancements

*   **Real-time Map Integration:** Replace the map placeholder with a live mapping library (e.g., Leaflet, Mapbox).
*   **Automated Scraping:** Set up a cron job to run the scraper and processor periodically.
*   **Advanced Analytics:** Add more sophisticated analytics and data visualizations.
*   **Council-Specific Dashboards:** Create personalized dashboards for individual councils.
*   **API Integration:** Develop an API to serve the processed grant data to other applications.


