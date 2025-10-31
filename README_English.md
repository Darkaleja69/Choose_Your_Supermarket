# 🛒 **Data Analytics in Retail: Price Comparison Across Supermarkets**  
**Competitive Analysis Project with Python, SQL, and Power BI**

---

## **Executive Summary**

In this project, I apply a complete **end-to-end Data Analytics approach** to answer a key question in the retail industry:  
> 💬 *Which supermarket offers the most competitive prices for the same shopping basket?*

By integrating **Python, SQL, and Power BI**, I developed a solution that collects, cleans, analyzes, and visualizes real supermarket data — transforming unstructured information into **actionable insights**.  

The result is an **interactive dashboard** that allows users to compare prices, analyze product categories, and uncover savings opportunities.  
This project demonstrates how data analytics can drive **strategic pricing decisions** in the retail sector.

---

## **Technologies Used**

| Stage | Tools / Languages |
|--------|-------------------|
| **Extraction & Cleaning** | Python (`pandas`, `requests`, `BeautifulSoup`) |
| **Modeling & Analysis** | SQL (`analytical queries`, `joins`) |
| **Visualization** | Power BI (`interactive dashboards`, `DAX`) |

---

## **Project Workflow**

### 1. Data Extraction and Cleaning (Python)
- Developed a **web scraper** to collect prices, categories, and brands from the websites of three supermarkets.  
- Performed data cleaning and normalization: product names, units, prices per kilo/liter, duplicates, and inconsistent formats.  
- Exported the cleaned data to CSV and loaded it into SQL.  

<img width="400" height="300" alt="image" src="https://github.com/user-attachments/assets/8514bbd4-fab6-4a71-956e-b616405242b8" />

---

### 2. Data Modeling and Analysis (SQL)
- Built **relational tables** to design a Star Schema model.  
- The final data model includes **seven dimensions** and **one fact table**, ensuring efficient and consistent analysis.  

<img width="400" height="300" alt="image" src="https://github.com/user-attachments/assets/82c26b83-593a-4886-8b3d-9add9b859c29" />

---

### 3. Visualization in Power BI
The dashboard is organized into **four types of interactive pages**:

#### 1. Product and Price Table  
A complete list of product prices across the three supermarkets, including the total shopping basket cost.  
<img width="400" height="300" alt="image" src="https://github.com/user-attachments/assets/72cacfcf-5563-4ac8-a4f4-6ce04a95c11e" />

#### 2. Supermarket-Level Analysis  
Price distribution, top expensive/cheap products, and category averages.  
<img width="400" height="300" alt="image" src="https://github.com/user-attachments/assets/736e1655-807d-49c1-84c8-d4f0c7df71e9" />

#### 3. Supermarket Comparison  
A consolidated view showing:
- Price differences by category  
- Potential savings index  
- Competitiveness ranking  

<img width="400" height="300" alt="image" src="https://github.com/user-attachments/assets/59ec8b6a-73fa-4825-b958-f524552e5791" />

#### 4. Product Detail  
Price history and detailed product attributes:  

<img width="400" height="350" alt="image" src="https://github.com/user-attachments/assets/544a2d94-4b89-4ba7-b50e-891b37185b0d" />

---

## **Key Findings**

- Price differences of up to **300%** were identified between supermarkets for equivalent products.  
- **Fresh food and grocery categories** show the highest product variability.  
- This analysis highlights how data analytics can **support strategic pricing and positioning decisions** in retail.

---

## **Key Learnings**

- Execution of a complete **end-to-end data analytics workflow**.  
- Integration of **Python, SQL, and Power BI** in a realistic data project.  
- Development of **data storytelling** and visual communication skills.  
- Automation of web data extraction processes.  
