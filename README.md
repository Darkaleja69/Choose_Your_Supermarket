# 🛒 **Data Analytics en Retail: Comparativa de Precios entre Supermercados**  
**Proyecto de Análisis Competitivo con Python, SQL y Power BI**


## **Resumen ejecutivo**

En este proyecto aplico un enfoque completo de **Data Analytics end-to-end** para responder una pregunta clave del sector retail:  
> 💬 *¿Qué supermercado ofrece los precios más competitivos para una misma cesta de productos?*

Mediante la integración de **Python, SQL y Power BI**, desarrollé una solución que recopila, limpia, analiza y visualiza datos reales de tres supermercados, transformando información no estructurada en **insights accionables**.  

El resultado es un **dashboard interactivo** que permite comparar precios, analizar categorías y descubrir oportunidades de ahorro.  
Este proyecto demuestra cómo la analítica de datos puede impulsar **decisiones estratégicas de pricing** en el sector retail.

---

## **Tecnologías utilizadas**

| Etapa | Herramientas / Lenguajes |
|-------|---------------------------|
| **Extracción y limpieza** | Python (`pandas`, `requests`, `BeautifulSoup`) |
| **Modelado y análisis** | SQL (`consultas analíticas`, `joins`) |
| **Visualización** | Power BI (`dashboards interactivos`, `DAX`) |

---

## **Flujo de trabajo del proyecto**

### 1. Extracción y limpieza de datos (Python)
- Desarrollo de un **web scraper** para obtener precios, categorías y marcas desde las webs de tres supermercados.  
- Limpieza y normalización de datos: nombres de productos, unidades, precios por kilo/litro, duplicados y formatos inconsistentes.  
- Exportación de los datos limpios a formato CSV y carga en SQL.
<img width="400" height="300" alt="image" src="https://github.com/user-attachments/assets/8514bbd4-fab6-4a71-956e-b616405242b8" />


### 2. Modelado y análisis en SQL
- Construcción de **tablas relacionales** para el diseño de un modelo en Estrella. Se han necesitado de 7 dimensiones y una única Fact Table para construir un modelo de datos eficiente y coherente. 
<img width="400" height="300" alt="image" src="https://github.com/user-attachments/assets/82c26b83-593a-4886-8b3d-9add9b859c29" />


### 3. Visualización en Power BI
Dashboard dividido en **tres tipos de páginas interactivas**:

#### 1. Tabla de productos y precios  
Lista completa con los precios en los tres supermercados y el costo total del carrito.  
<img width="400" height="300" alt="image" src="https://github.com/user-attachments/assets/72cacfcf-5563-4ac8-a4f4-6ce04a95c11e" />


#### 2. Análisis individual por supermercado  
Distribución de precios, top productos caros/baratos y promedios por categoría.  
<img width="400" height="300" alt="image" src="https://github.com/user-attachments/assets/736e1655-807d-49c1-84c8-d4f0c7df71e9" />


#### 3. Comparativa entre supermercados  
Vista consolidada con:
- Diferencias de precios por categoría  
- Índice de ahorro potencial  
- Ranking de competitividad  
  
<img width="400" height="300" alt="image" src="https://github.com/user-attachments/assets/59ec8b6a-73fa-4825-b958-f524552e5791" />

#### 4. Detalle del producto
Historial de precios y descripción de características del producto:

<img width="400" height="350" alt="image" src="https://github.com/user-attachments/assets/544a2d94-4b89-4ba7-b50e-891b37185b0d" />




## **Conclusiones principales**

- Se identificaron diferencias de hasta **300%** entre supermercados en productos equivalentes.  
- Las categorías de **frescos y alimentación** presentan mayor variabilidad de productos.  
- Este análisis muestra cómo la analítica de datos puede **apoyar decisiones estratégicas en pricing y posicionamiento** dentro del retail.

---

## **Aprendizajes clave**

- Ejecución de un flujo completo **end-to-end** de analítica de datos.  
- Integración de **Python, SQL y Power BI** en un proyecto realista.  
- Desarrollo de habilidades en **data storytelling** y comunicación visual.  
- Automatización del proceso de extracción de datos web.  

