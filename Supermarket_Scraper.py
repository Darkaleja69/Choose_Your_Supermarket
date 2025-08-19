import os 
import re
import csv
import time 
import random 
import sqlite3
import keyboard
import traceback
from datetime import datetime
from bs4 import BeautifulSoup
from seleniumbase import Driver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import ElementClickInterceptedException, StaleElementReferenceException
import signal
import sys

def wait_for_elements(driver, by, selector, timeout=10, multiple=False):
    """Espera a que uno o varios elementos estén presentes en la página."""
    wait = WebDriverWait(driver, timeout)
    if multiple:
        return wait.until(EC.presence_of_all_elements_located((by, selector)))
    else:
        return wait.until(EC.presence_of_element_located((by, selector)))

def click_element(driver, by, selector, timeout=10):
    """Espera y hace clic en un elemento."""
    try:
        WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((by, selector))).click()
    except Exception as e:
        print(f"No se pudo hacer clic en el elemento: {e}")

def mercadona_csv(datos, nombre_archivo="dia.csv"):
    """
    Guarda los datos en un archivo CSV.

    Parámetros:
    datos -- Lista de diccionarios con los datos a guardar.
    nombre_archivo -- Nombre del archivo CSV a crear.
    """
    if not datos:
        print("No hay datos para guardar.")
        return
    
    columnas = datos[0].keys()
    existe_archivo = os.path.isfile(nombre_archivo)

    with open(nombre_archivo, 'a+' if existe_archivo else 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=columnas)

        if not existe_archivo:
            writer.writeheader()

        writer.writerows(datos)

def iniciar_driver():
    """Inicia el driver de Selenium con las configuraciones necesarias."""
    driver = Driver(
        browser="chrome",
        uc=True,
        headless2=False,
        incognito=False,
        agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        do_not_track=True,
        undetectable=True
    )
    driver.maximize_window()
    return driver

def calcular_precio_unitario(formato, precio):
    """
    Calcula el precio por litro o por kilogramo basado en el formato del producto.
    
    Args:
        formato (str): El formato del producto (ej: "2 botellas x 2 L", "5 L", "400 g")
        precio (str): El precio del producto como string
    
    Returns:
        float: Precio por litro o por kg, o None si no se puede calcular
    """
    try:
        # Convertir precio a float
        precio = float(precio)
        
        # Patrones comunes
        litros_pattern = r'(\d+(?:\.\d+)?)\s*(?:L|l|litro)'
        ml_pattern = r'(\d+(?:\.\d+)?)\s*(?:ml|ML|cc)'
        kg_pattern = r'(\d+(?:\.\d+)?)\s*(?:kg|KG|Kg)'
        g_pattern = r'(\d+(?:\.\d+)?)\s*(?:g|G|gr|GR)'
        unidades_pattern = r'(\d+)\s*(?:botella|lata|pack|unidad|ud)'
        
        # Buscar patrones en el formato
        litros = re.findall(litros_pattern, formato)
        ml = re.findall(ml_pattern, formato)
        kg = re.findall(kg_pattern, formato)
        g = re.findall(g_pattern, formato)
        unidades = re.findall(unidades_pattern, formato)
        
        cantidad_total = 0
        
        # Calcular cantidad total
        if litros:
            cantidad_total = sum(float(x) for x in litros)
            if unidades:
                cantidad_total *= float(unidades[0])
            return precio / cantidad_total
            
        elif ml:
            cantidad_total = sum(float(x) for x in ml) / 1000  # convertir a litros
            if unidades:
                cantidad_total *= float(unidades[0])
            return precio / cantidad_total
            
        elif kg:
            cantidad_total = sum(float(x) for x in kg)
            if unidades:
                cantidad_total *= float(unidades[0])
            return precio / cantidad_total
            
        elif g:
            cantidad_total = sum(float(x) for x in g) / 1000  # convertir a kg
            if unidades:
                cantidad_total *= float(unidades[0])
            return precio / cantidad_total
            
        return None
        
    except Exception as e:
        print(f"Error calculando precio unitario para formato '{formato}': {str(e)}")
        return None

def obtener_datos_productos(driver, categoria):
    """Obtiene los datos de los productos dentro de una categoría."""
    productos = []
    elemento_productos = wait_for_elements(driver, By.CSS_SELECTOR, 'div.product-cell[data-testid="product-cell"]', multiple=True)
    print(f"Total productos encontrados: {len(elemento_productos)}")

    for anuncio in elemento_productos: 
        html_content = anuncio.get_attribute('innerHTML')
        soup = BeautifulSoup(html_content, 'html.parser')

        # Obtener el título
        h4_element = soup.find('h4', class_="subhead1-r product-cell__description-name", attrs={"data-testid": "product-cell-name"})
        titulo = h4_element.text if h4_element else "Título no disponible"

        # Obtener la descripción detallada (cantidad/peso)
        formato_element = soup.find('div', class_="product-format product-format__size--cell")
        if formato_element:
            span_elements = formato_element.find_all('span', class_="footnote1-r")
            formato = " ".join(span.text.strip() for span in span_elements) if span_elements else "Formato no disponible"
        else:
            formato = "Formato no disponible"

        # Obtener el precio
        p_element = soup.find('p', class_="product-price__unit-price subhead1-b", attrs={"data-testid": "product-price"})
        if p_element is None:
            p_element = soup.find('p', class_="product-price__unit-price subhead1-b product-price__unit-price--discount", attrs={"data-testid": "product-price"})
        
        precio = p_element.text.replace(".", "").replace(",", ".").replace("€", "").strip() if p_element else "Precio no disponible"
        
        # Calcular precio unitario
        precio_unitario = None
        if precio != "Precio no disponible" and formato != "Formato no disponible":
            precio_unitario = calcular_precio_unitario(formato, precio)
        
        print(f"Producto: {titulo}\nFormato: {formato}\nPrecio: {precio}\nPrecio unitario: {precio_unitario:.2f}€/unidad" if precio_unitario else "Precio unitario: No disponible")
        
        productos.append({
            'titulo': titulo,
            'formato': formato,
            'precio': precio,
            'precio_unitario': f"{precio_unitario:.2f}" if precio_unitario is not None else "No disponible",
            'categoria': categoria,
            'fecha_extraccion': datetime.now().strftime('%Y-%m-%d')
        })
    return productos

def cerrar_modal_si_existe(driver):
    """Intenta cerrar el modal si está presente."""
    try:
        modal = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="mask"]'))
        )
        modal.click()
        time.sleep(1)
    except:
        pass

def signal_handler(sig, frame):
    print('\nCerrando el navegador gracefully...')
    try:
        if 'driver' in globals():
            driver.quit()
    except:
        pass
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def explorar_categorias(driver):
    lista_productos = []
    url_base = driver.current_url
    max_reintentos_categoria = 3
    
    try:
        categorias = wait_for_elements(driver, By.CSS_SELECTOR, '.category-menu__header', multiple=True)
        total_categorias = len(categorias)
        
        for i in range(total_categorias):
            for intento in range(max_reintentos_categoria):
                try:
                    print(f"\n{'='*50}")
                    print(f"Procesando categoría {i+1} de {total_categorias} (intento {intento+1})")
                    
                    if driver.current_url != url_base:
                        driver.get(url_base)
                        time.sleep(3)
                    
                    # Obtener la lista actualizada de categorías
                    print("Actualizando lista de categorías...")
                    driver.execute_script("window.scrollTo(0, 0);")  # Scroll al inicio
                    time.sleep(2)
                    
                    # Intentar obtener y hacer clic en la categoría
                    max_intentos = 3
                    categoria_actual = None
                    
                    for intento_categoria in range(max_intentos):
                        try:
                            # Esperar a que no haya modal visible
                            try:
                                modal = driver.find_element(By.CSS_SELECTOR, '[data-testid="mask"]')
                                if modal.is_displayed():
                                    print("Modal detectado, intentando cerrar...")
                                    modal.click()
                                    time.sleep(1)
                            except:
                                pass
                            
                            categorias = wait_for_elements(driver, By.CSS_SELECTOR, '.category-menu__header', multiple=True)
                            categoria = categorias[i]
                            nombre_categoria = categoria.text.replace(",", "")
                            categoria_actual = nombre_categoria
                            print(f"Analizando categoría: {nombre_categoria}")
                            
                            # Hacer scroll y clic
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", categoria)
                            time.sleep(2)
                            driver.execute_script("arguments[0].click();", categoria)
                            break
                        except Exception as e:
                            if intento_categoria == max_intentos - 1:
                                raise
                            print(f"Error en intento {intento_categoria + 1}: {str(e)}")
                            time.sleep(2)
                            driver.refresh()
                            time.sleep(3)
                    
                    time.sleep(3)

                    # Esperar a que la categoría esté abierta y obtener las subcategorías
                    try:
                        print("Buscando subcategorías...")
                        # Esperar a que la categoría esté abierta
                        el_category = wait_for_elements(driver, By.CSS_SELECTOR, 'li.category-menu__item.open', multiple=False)
                        time.sleep(2)
                        
                        # Obtener todas las subcategorías directamente
                        subcategorias = wait_for_elements(driver, By.CSS_SELECTOR, 'li.category-menu__item.open li.category-item button.category-item__link', multiple=True)
                        
                        if not subcategorias:
                            print("No se encontraron subcategorías")
                            continue
                        
                        total_subcategorias = len(subcategorias)
                        print(f"Subcategorías encontradas: {total_subcategorias}")
                        
                        # Procesar cada subcategoría
                        for idx in range(total_subcategorias):
                            try:
                                # Esperar a que la categoría principal esté abierta
                                categoria_abierta = WebDriverWait(driver, 10).until(
                                    EC.presence_of_element_located((By.CSS_SELECTOR, 'li.category-menu__item.open'))
                                )
                                
                                # Obtener todas las subcategorías de la categoría abierta usando el selector correcto
                                subcategorias_links = categoria_abierta.find_elements(By.CSS_SELECTOR, 'button.category-item__link')
                                
                                if idx >= len(subcategorias_links):
                                    print(f"No se encontró el elemento para el índice {idx}")
                                    continue
                                    
                                sub_element = subcategorias_links[idx]
                                
                                # Obtener el nombre directamente del botón
                                try:
                                    nombre = sub_element.text.strip()
                                    print(f"Procesando subcategoría - Nombre: {nombre}")
                                    
                                    # Hacer scroll y clic en el botón
                                    driver.execute_script("arguments[0].scrollIntoView(true);", sub_element)
                                    time.sleep(2)
                                    driver.execute_script("arguments[0].click();", sub_element)
                                    
                                except Exception as e:
                                    print(f"Error al obtener nombre o navegar: {str(e)}")
                                    continue
                                
                                time.sleep(3)
                                
                                # Esperar a que los productos se carguen
                                try:
                                    wait_for_elements(driver, By.CSS_SELECTOR, 'div.product-cell[data-testid="product-cell"]', timeout=10, multiple=True)
                                except:
                                    print("No se detectaron productos, reintentando navegación...")
                                    driver.refresh()
                                    time.sleep(3)
                                    try:
                                        wait_for_elements(driver, By.CSS_SELECTOR, 'div.product-cell[data-testid="product-cell"]', timeout=10, multiple=True)
                                    except:
                                        print("No se pudieron cargar los productos, saltando subcategoría...")
                                        continue
                                
                                # Obtener los productos
                                print(f"Obteniendo productos de {nombre}...")
                                productos = obtener_datos_productos(driver, f"{categoria_actual} - {nombre}")
                                lista_productos.extend(productos)
                                
                                # Volver a la categoría principal
                                print("Volviendo a la categoría principal...")
                                driver.get(url_base)
                                time.sleep(3)
                                
                                # Reabrir la categoría principal
                                print("Reabriendo la categoría...")
                                categorias = wait_for_elements(driver, By.CSS_SELECTOR, '.category-menu__header', multiple=True)
                                for cat in categorias:
                                    if cat.text.replace(",", "") == categoria_actual:
                                        driver.execute_script("arguments[0].click();", cat)
                                        break
                                time.sleep(3)
                                
                            except Exception as e:
                                print(f"Error al obtener información de la subcategoría: {str(e)}")
                                print("Stacktrace:")
                                print(traceback.format_exc())
                                driver.get(url_base)
                                time.sleep(3)
                                continue

                    except Exception as e:
                        print(f"Error al procesar subcategorías de {nombre_categoria}: {str(e)}")
                        print("Stacktrace:")
                        print(traceback.format_exc())
                        driver.get(url_base)
                        time.sleep(3)
                        continue

                    # Después de procesar todas las subcategorías exitosamente
                    break  # <-- Añadir este break para salir del bucle de reintentos
                    
                except Exception as e:
                    print(f"Error al analizar la categoría {i}: {str(e)}")
                    print("Stacktrace:")
                    print(traceback.format_exc())
                    driver.get(url_base)
                    time.sleep(3)
                    if intento == max_reintentos_categoria - 1:
                        print(f"Se agotaron los reintentos para la categoría {i+1}")
                    continue
    
    except Exception as e:
        print(f"Error general en explorar_categorias: {str(e)}")
        print("Stacktrace:")
        print(traceback.format_exc())
    
    finally:
        return lista_productos

if __name__ == "__main__":
    driver = iniciar_driver()
    try:
        fecha = datetime.now().date()
        print(f"Iniciando escaneo a fecha: {datetime.now()}")

        driver.get("https://tienda.mercadona.es/")
        # Aceptar cookies
        click_element(driver, By.XPATH, "//button[normalize-space()='Aceptar']")
        time.sleep(3)
        
        # Navegar a la sección de categorías
        driver.get("https://tienda.mercadona.es/categories/112")
        
        # Extraer datos de las categorías y productos
        productos = explorar_categorias(driver)
        
        if productos:
            mercadona_csv(productos, f"mercadona_{fecha}.csv")
        else:
            print("No se encontraron productos.")

    except Exception as e:
        print(f"Error durante el proceso de scraping: {e}")
    
    finally:
        driver.quit()