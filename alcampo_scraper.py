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

# Reutilizamos las funciones auxiliares del scraper original
def wait_for_elements(driver, by, selector, timeout=20, multiple=False):
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

def alcampo_csv(datos, nombre_archivo="alcampo.csv"):
    """Guarda los datos en un archivo CSV."""
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
    """Calcula el precio por litro o por kilogramo basado en el formato del producto."""
    try:
        precio = float(precio)
        
        litros_pattern = r'(\d+(?:\.\d+)?)\s*(?:L|l|litro)'
        ml_pattern = r'(\d+(?:\.\d+)?)\s*(?:ml|ML|cc)'
        kg_pattern = r'(\d+(?:\.\d+)?)\s*(?:kg|KG|Kg)'
        g_pattern = r'(\d+(?:\.\d+)?)\s*(?:g|G|gr|GR)'
        unidades_pattern = r'(\d+)\s*(?:botella|lata|pack|unidad|ud)'
        
        litros = re.findall(litros_pattern, formato)
        ml = re.findall(ml_pattern, formato)
        kg = re.findall(kg_pattern, formato)
        g = re.findall(g_pattern, formato)
        unidades = re.findall(unidades_pattern, formato)
        
        cantidad_total = 0
        
        if litros:
            cantidad_total = sum(float(x) for x in litros)
            if unidades:
                cantidad_total *= float(unidades[0])
            return precio / cantidad_total
            
        elif ml:
            cantidad_total = sum(float(x) for x in ml) / 1000
            if unidades:
                cantidad_total *= float(unidades[0])
            return precio / cantidad_total
            
        elif kg:
            cantidad_total = sum(float(x) for x in kg)
            if unidades:
                cantidad_total *= float(unidades[0])
            return precio / cantidad_total
            
        elif g:
            cantidad_total = sum(float(x) for x in g) / 1000
            if unidades:
                cantidad_total *= float(unidades[0])
            return precio / cantidad_total
            
        return None
        
    except Exception as e:
        print(f"Error calculando precio unitario para formato '{formato}': {str(e)}")
        return None

def aceptar_cookies(driver):
    """Acepta las cookies si aparece el diálogo"""
    try:
        # Esperar a que aparezca el botón de cookies y hacer clic
        boton_cookies = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
        )
        boton_cookies.click()
        print("Cookies aceptadas")
        time.sleep(2)
    except Exception as e:
        print(f"No se encontró el diálogo de cookies o ya estaban aceptadas: {str(e)}")

def scroll_suave(driver, pixels):
    """Hace un scroll suave de la página."""
    for i in range(0, pixels, 100):  # Scroll de 100 en 100 píxeles
        driver.execute_script(f"window.scrollBy(0, 100);")
        time.sleep(0.5)  # Pequeña pausa entre cada scroll

def esperar_carga_productos(driver, contenedor_principal, max_intentos=5):
    """Espera a que se carguen nuevos productos después de hacer scroll."""
    altura_anterior = driver.execute_script("return document.documentElement.scrollHeight")
    productos_anteriores = len(contenedor_principal.find_elements(By.CSS_SELECTOR, 'div.product-card-container'))
    
    for intento in range(max_intentos):
        # Hacer scroll suave hacia abajo (300 píxeles cada vez)
        scroll_suave(driver, 300)
        time.sleep(2)
        
        # Verificar si la altura de la página cambió
        nueva_altura = driver.execute_script("return document.documentElement.scrollHeight")
        nuevos_productos = len(contenedor_principal.find_elements(By.CSS_SELECTOR, 'div.product-card-container'))
        
        print(f"Intento {intento + 1}: Productos anteriores: {productos_anteriores}, Nuevos productos: {nuevos_productos}")
        
        if nueva_altura > altura_anterior or nuevos_productos > productos_anteriores:
            print("Se detectaron nuevos productos, esperando a que carguen completamente...")
            time.sleep(3)  # Dar tiempo extra para la carga completa
            return True
            
        print(f"Esperando nuevos productos... Intento {intento + 1}/{max_intentos}")
        time.sleep(1)
    
    return False

def obtener_datos_producto(driver, producto):
    """Obtiene los datos de un producto individual con manejo de errores de stale element."""
    max_intentos = 3
    for intento in range(max_intentos):
        try:
            # Intentar obtener el título
            titulo_container = producto.find_element(By.CSS_SELECTOR, 'div.title-container')
            titulo_element = titulo_container.find_element(By.CSS_SELECTOR, 'h3')
            titulo = titulo_element.text.strip()

            # Intentar obtener el precio
            precio_container = producto.find_element(By.CSS_SELECTOR, 'div.price-pack-size-container')
            precio_element = precio_container.find_element(By.CSS_SELECTOR, 'span[data-test="fop-price"]')
            precio = precio_element.text.replace("€", "").strip()

            # Obtener el formato y precio por unidad
            formato_container = producto.find_element(By.CSS_SELECTOR, 'div[data-test="fop-size"]')
            formato_element = formato_container.find_element(By.CSS_SELECTOR, 'span._text_cn5lb_1')
            formato = formato_element.text.strip()
            
            precio_unidad_element = formato_container.find_element(By.CSS_SELECTOR, 'span[data-test="fop-price-per-unit"]')
            precio_unidad = precio_unidad_element.text.strip()

            # Verificar disponibilidad del producto
            disponibilidad = "disponible"
            try:
                # Buscar el botón de agotado
                producto.find_element(By.CSS_SELECTOR, 'button[data-test="fop-controls-no-alternatives-button"]')
                disponibilidad = "agotado"
            except:
                # Si no encuentra el botón de agotado, verificamos el botón de añadir
                try:
                    producto.find_element(By.CSS_SELECTOR, 'button[data-test="counter-button"]')
                    disponibilidad = "disponible"
                except:
                    # Si no encuentra ninguno de los dos botones, marcamos como estado desconocido
                    disponibilidad = "desconocido"

            return {
                'titulo': titulo,
                'formato': formato,
                'precio': precio,
                'precio_unidad': precio_unidad.replace('(', '').replace(')', ''),
                'disponibilidad': disponibilidad
            }

        except Exception as e:
            if intento == max_intentos - 1:
                print(f"Error después de {max_intentos} intentos: {str(e)}")
                return None
            print(f"Intento {intento + 1} falló, reintentando...")
            time.sleep(1)
    return None

def obtener_datos_productos_alcampo(driver, categoria):
    """Obtiene los datos de los productos dentro de una categoría de Alcampo."""
    productos = []
    productos_procesados = set()  # Para evitar duplicados por URL
    sin_productos_nuevos = 0
    max_intentos_sin_nuevos = 3
    ultima_posicion = 0
    driver.switch_to.default_content()

    # Buscar nuevamente el contenedor
    contenedores = driver.find_elements(By.CSS_SELECTOR, "div[data-retailer-anchor='product-list']")
    print(f"Contenedores encontrados después del scroll: {len(contenedores)}")
    try:
        # Esperar a que se cargue el contenedor principal de productos
        print("Esperando a que cargue el contenedor principal...")
        contenedor_principal = wait_for_elements(
            driver, 
            By.CSS_SELECTOR, 
            "div[data-retailer-anchor='product-list']", 
            multiple=False,
            timeout=15
        )
        
        print("\nVerificando estructura del contenedor principal:")
        print(f"Clases del contenedor: {contenedor_principal.get_attribute('class')}")
        
        print("\nEsperando 5 segundos para la carga inicial de productos...")
        time.sleep(5)

        while sin_productos_nuevos < max_intentos_sin_nuevos:
            try:
                # Refrescar el contenedor principal
                contenedor_principal = wait_for_elements(
                    driver, 
                    By.CSS_SELECTOR, 
                    "div[data-retailer-anchor='product-list']", 
                    multiple=False,
                    timeout=15
                )
                
                # Obtener productos visibles actuales
                elemento_productos = contenedor_principal.find_elements(By.CSS_SELECTOR, 'div.sc-kdIgRK')
                
                if not elemento_productos:
                    print("\nNo se encontraron productos, esperando más tiempo...")
                    time.sleep(2)
                    continue
                    
                print(f"\nProductos encontrados en esta iteración: {len(elemento_productos)}")
                
                # Procesar solo los productos que están completamente visibles
                productos_visibles = []
                for producto in elemento_productos:
                    try:
                        # Verificar si el producto está visible en la ventana
                        if driver.execute_script("""
                            var rect = arguments[0].getBoundingClientRect();
                            return (
                            rect.bottom > 0 && rect.top < window.innerHeight
                            );
                    """, producto):
                            productos_visibles.append(producto)
                    except:
                        continue


                


                print(f"Productos visibles en pantalla: {len(productos_visibles)}")
                
                # Procesar solo los productos visibles
                for producto in productos_visibles:
                    try:
                        # Verificar si el producto está aún cargando
                        if producto.find_elements(By.CSS_SELECTOR, 'div._skeleton_1ndyq_12'):
                            print("Producto aún cargando, esperando...")
                            time.sleep(2)
                            continue

                        # Obtener URL del producto para evitar duplicados
                        try:
                            url_producto = producto.find_element(By.CSS_SELECTOR, 'a[data-test="fop-product-link"]').get_attribute('href')
                            if url_producto in productos_procesados:
                                continue
                        except:
                            print("No se pudo obtener URL del producto")
                            url_producto = None

                        # Obtener datos del producto
                        datos_producto = obtener_datos_producto(driver, producto)
                        if datos_producto is None:
                            continue

                        print(f"\nProducto encontrado:")
                        print(f"Título: {datos_producto['titulo']}")
                        print(f"Formato: {datos_producto['formato']}")
                        print(f"Precio: {datos_producto['precio']}")
                        print(f"Precio por unidad: {datos_producto['precio_unidad']}")
                        # Añadir el estado de disponibilidad con un formato visual
                        estado = datos_producto['disponibilidad']
                        if estado == "disponible":
                            print(f"Estado: ✅ Disponible")
                        elif estado == "agotado":
                            print(f"Estado: ❌ Agotado")
                        else:
                            print(f"Estado: ❓ Desconocido")

                        datos_producto['categoria'] = categoria
                        datos_producto['fecha_scraping'] = datetime.now().strftime("%Y-%m-%d")
                        productos.append(datos_producto)

                        if url_producto:
                            productos_procesados.add(url_producto)

                    except Exception as e:
                        print(f"\nError procesando producto: {str(e)}")
                        continue

                # Hacer scroll y esperar nuevos productos
                if not esperar_carga_productos(driver, contenedor_principal):
                    sin_productos_nuevos += 1
                    print(f"\nNo se encontraron nuevos productos. Intento {sin_productos_nuevos}/{max_intentos_sin_nuevos}")
                else:
                    sin_productos_nuevos = 0
                    print(f"\nNuevos productos encontrados. Total actual: {len(productos)}")

            except Exception as e:
                print(f"Error en iteración de productos: {str(e)}")
                time.sleep(2)
                continue

    except Exception as e:
        print(f"Error obteniendo productos: {str(e)}")
        traceback.print_exc()

    print(f"\nTotal de productos recopilados: {len(productos)}")
    return productos

def navegar_a_catalogo(driver):
    """Navega al catálogo completo de Alcampo."""
    try:
        print("Accediendo a la web de Alcampo...")
        driver.get("https://www.compraonline.alcampo.es/")
        time.sleep(3)

        # Aceptar cookies si aparece el diálogo
        aceptar_cookies(driver)

        print("Haciendo clic en el botón de menú...")
        click_element(driver, By.ID, "nav-menu-button")
        time.sleep(2)

        print("Navegando al catálogo completo...")
        click_element(driver, By.XPATH, "//a[@data-test='Todo el catálogo']")
        time.sleep(3)

        return True

    except Exception as e:
        print(f"Error navegando al catálogo: {str(e)}")
        return False

def obtener_categorias(driver):
    """Obtiene todas las categorías disponibles en Alcampo."""
    categorias = []
    try:
        # Esperar a que se carguen las categorías
        elementos_categoria = wait_for_elements(
            driver,
            By.CSS_SELECTOR,
            'a[data-test="root-category-link"]',
            multiple=True
        )
        
        for elemento in elementos_categoria:
            nombre = elemento.text.strip()
            url = elemento.get_attribute('href')
            categorias.append({
                'nombre': nombre,
                'url': url
            })
            print(f"Categoría encontrada: {nombre}")
            
        return categorias
    except Exception as e:
        print(f"Error obteniendo categorías: {str(e)}")
        return []

def obtener_subcategorias(driver):
    """Obtiene las subcategorías de la categoría actual."""
    subcategorias = []
    try:
        # Esperar a que se carguen las subcategorías
        elementos_subcategoria = wait_for_elements(
            driver,
            By.CSS_SELECTOR,
            'li.sc-jOnpCo a[data-test="root-category-link"]', # Selector actualizado para subcategorías
            multiple=True,
            timeout=10
        )
        
        print("\nBuscando subcategorías...")
        print(f"Elementos encontrados: {len(elementos_subcategoria)}")
        
        for elemento in elementos_subcategoria:
            try:
                nombre = elemento.text.strip()
                url = elemento.get_attribute('href')
                clase = elemento.get_attribute('class')
                print(f"\nElemento encontrado:")
                print(f"Nombre: {nombre}")
                print(f"URL: {url}")
                print(f"Clase: {clase}")
                
                if nombre and url:  # Asegurarse de que sean válidos
                    subcategorias.append({
                        'nombre': nombre,
                        'url': url
                    })
                    print(f"Subcategoría añadida: {nombre}")
            except Exception as e:
                print(f"Error procesando elemento de subcategoría: {str(e)}")
                continue
            
        return subcategorias
    except Exception as e:
        print(f"Error obteniendo subcategorías: {str(e)}")
        traceback.print_exc()
        return []

def reiniciar_navegacion(driver):
    """Reinicia la navegación al catálogo principal."""
    try:
        print("Reiniciando navegación...")
        driver.get("https://www.compraonline.alcampo.es/")
        time.sleep(3)
        
        # Aceptar cookies si aparece el diálogo
        aceptar_cookies(driver)
        
        # Hacer clic en el botón de menú
        click_element(driver, By.ID, "nav-menu-button")
        time.sleep(2)
        
        # Navegar al catálogo completo
        click_element(driver, By.XPATH, "//a[@data-test='Todo el catálogo']")
        time.sleep(3)
        
        return True
    except Exception as e:
        print(f"Error reiniciando navegación: {str(e)}")
        return False

def es_error_sesion(error):
    """Determina si un error está relacionado con la sesión."""
    error_str = str(error).lower()
    errores_sesion = [
        "invalid session id",
        "session not found",
        "session has been terminated",
        "session timed out",
        "stale element reference",
        "element is not attached",
        "no such session",
        "element click intercepted",
        "element not interactable",
        "element not visible"
    ]
    return any(msg in error_str for msg in errores_sesion)

def reiniciar_sesion(driver=None, max_intentos=3):
    """Reinicia la sesión del driver y devuelve una nueva instancia."""
    for intento in range(max_intentos):
        try:
            if driver:
                try:
                    driver.quit()
                except Exception as e:
                    print(f"Error al cerrar el driver anterior: {str(e)}")
                finally:
                    driver = None
            
            print(f"\nReiniciando sesión (intento {intento + 1}/{max_intentos})...")
            time.sleep(5 * (intento + 1))  # Espera incremental entre intentos
            
            nuevo_driver = iniciar_driver()
            
            if not reiniciar_navegacion(nuevo_driver):
                print("Error al reiniciar navegación, intentando de nuevo...")
                try:
                    nuevo_driver.quit()
                except:
                    pass
                continue
                
            # Verificar que el driver está respondiendo
            try:
                nuevo_driver.current_url
                return nuevo_driver
            except:
                print("El nuevo driver no responde, intentando de nuevo...")
                try:
                    nuevo_driver.quit()
                except:
                    pass
                continue
                
        except Exception as e:
            print(f"Error reiniciando sesión (intento {intento + 1}): {str(e)}")
            if intento < max_intentos - 1:
                time.sleep(5 * (intento + 1))
                continue
            
    print("No se pudo reiniciar la sesión después de todos los intentos")
    return None

def procesar_categoria(driver, categoria, productos_totales, max_reintentos_sesion=3):
    """Procesa una categoría y todas sus subcategorías."""
    for intento_sesion in range(max_reintentos_sesion):
        try:
            print("\n" + "="*50)
            print(f"INICIANDO PROCESAMIENTO DE CATEGORÍA: {categoria['nombre']}")
            print(f"Intento de sesión: {intento_sesion + 1}/{max_reintentos_sesion}")
            print("="*50)
            
            # Verificar estado del driver antes de continuar
            try:
                driver.current_url
            except Exception as e:
                print(f"Driver no responde antes de procesar categoría: {str(e)}")
                driver = reiniciar_sesion(driver)
                if not driver:
                    return False, None
                continue
            
            try:
                driver.get(categoria['url'])
                time.sleep(3)
            except Exception as e:
                if es_error_sesion(e):
                    print(f"Error de sesión al acceder a la categoría: {str(e)}")
                    driver = reiniciar_sesion(driver)
                    if not driver:
                        return False, None
                    continue
                raise
            
            # Obtener subcategorías con reintentos
            subcategorias = None
            for _ in range(3):
                try:
                    subcategorias = obtener_subcategorias(driver)
                    break
                except Exception as e:
                    if es_error_sesion(e):
                        print(f"Error de sesión al obtener subcategorías: {str(e)}")
                        driver = reiniciar_sesion(driver)
                        if not driver:
                            return False, None
                        try:
                            driver.get(categoria['url'])
                            time.sleep(3)
                        except:
                            continue
                    else:
                        print(f"Error no relacionado con la sesión al obtener subcategorías: {str(e)}")
                        break
            
            if subcategorias:
                print(f"\nSe encontraron {len(subcategorias)} subcategorías en {categoria['nombre']}")
                for subcategoria in subcategorias:
                    subcategoria_procesada = False
                    for intento_sub in range(max_reintentos_sesion):
                        try:
                            print("\n" + "-"*30)
                            print(f"PROCESANDO SUBCATEGORÍA: {subcategoria['nombre']}")
                            print(f"URL: {subcategoria['url']}")
                            print(f"Intento: {intento_sub + 1}/{max_reintentos_sesion}")
                            print("-"*30)
                            
                            # Verificar estado del driver
                            try:
                                driver.current_url
                            except:
                                driver = reiniciar_sesion(driver)
                                if not driver:
                                    return False, None
                                continue
                            
                            try:
                                driver.get(subcategoria['url'])
                                time.sleep(3)
                            except Exception as e:
                                if es_error_sesion(e):
                                    print(f"Error de sesión al acceder a la subcategoría: {str(e)}")
                                    driver = reiniciar_sesion(driver)
                                    if not driver:
                                        return False, None
                                    continue
                                raise
                            
                            productos_subcategoria = obtener_datos_productos_alcampo(driver, f"{categoria['nombre']} > {subcategoria['nombre']}")
                            if productos_subcategoria:
                                productos_totales.extend(productos_subcategoria)
                                alcampo_csv(productos_subcategoria)
                                print(f"\nGuardados {len(productos_subcategoria)} productos de la subcategoría {subcategoria['nombre']}")
                                subcategoria_procesada = True
                                break
                            else:
                                print(f"\nNo se encontraron productos en la subcategoría {subcategoria['nombre']}")
                                subcategoria_procesada = True
                                break
                                
                        except Exception as e:
                            if es_error_sesion(e):
                                print(f"\nError de sesión procesando subcategoría: {str(e)}")
                                if intento_sub < max_reintentos_sesion - 1:
                                    driver = reiniciar_sesion(driver)
                                    if not driver:
                                        return False, None
                                    time.sleep(5)
                                    continue
                            else:
                                print(f"\nError procesando subcategoría: {str(e)}")
                                break
                    
                    if not subcategoria_procesada:
                        print(f"\nNo se pudo procesar la subcategoría {subcategoria['nombre']} después de todos los intentos")
                        continue
                            
                    time.sleep(random.uniform(2, 4))
            else:
                print(f"\nNo se encontraron subcategorías en {categoria['nombre']}, procesando como categoría principal")
                productos_categoria = None
                for _ in range(3):
                    try:
                        productos_categoria = obtener_datos_productos_alcampo(driver, categoria['nombre'])
                        break
                    except Exception as e:
                        if es_error_sesion(e):
                            print(f"Error de sesión al obtener productos de categoría principal: {str(e)}")
                            driver = reiniciar_sesion(driver)
                            if not driver:
                                return False, None
                            try:
                                driver.get(categoria['url'])
                                time.sleep(3)
                            except:
                                continue
                        else:
                            print(f"Error no relacionado con la sesión al obtener productos: {str(e)}")
                            break
                
                if productos_categoria:
                    productos_totales.extend(productos_categoria)
                    alcampo_csv(productos_categoria)
                    print(f"\nGuardados {len(productos_categoria)} productos de la categoría {categoria['nombre']}")
                else:
                    print(f"\nNo se encontraron productos en la categoría {categoria['nombre']}")
            
            print("\n" + "="*50)
            print(f"FINALIZADO PROCESAMIENTO DE CATEGORÍA: {categoria['nombre']}")
            print("="*50)
            return True, driver
            
        except Exception as e:
            if es_error_sesion(e):
                print(f"\nError de sesión en categoría principal: {str(e)}")
                if intento_sesion < max_reintentos_sesion - 1:
                    print("Reiniciando sesión para categoría principal...")
                    driver = reiniciar_sesion(driver)
                    if not driver:
                        return False, None
                    time.sleep(5)
                    continue
            else:
                print(f"\nERROR procesando categoría {categoria['nombre']}: {str(e)}")
                traceback.print_exc()
                return False, driver
    
    return False, driver

def signal_handler(sig, frame):
    print('\nCerrando el navegador gracefully...')
    try:
        if 'driver' in globals():
            driver.quit()
    except:
        pass
    sys.exit(0)

def main():
    signal.signal(signal.SIGINT, signal_handler)
    
    max_reintentos = 3
    todos_los_productos = []
    categorias_procesadas = set()
    driver = None
    
    for intento in range(max_reintentos):
        try:
            if not driver:
                driver = iniciar_driver()
                if not driver:
                    print("No se pudo iniciar el driver, reintentando...")
                    time.sleep(5 * (intento + 1))
                    continue
            
            # Verificar estado del driver
            try:
                driver.current_url
            except:
                print("Driver no responde, reiniciando sesión...")
                driver = reiniciar_sesion(driver)
                if not driver:
                    continue
            
            if navegar_a_catalogo(driver):
                # Obtener todas las categorías con reintentos
                categorias = None
                for _ in range(3):
                    try:
                        categorias = obtener_categorias(driver)
                        if categorias:
                            break
                    except Exception as e:
                        if es_error_sesion(e):
                            print(f"Error de sesión al obtener categorías: {str(e)}")
                            driver = reiniciar_sesion(driver)
                            if not driver:
                                break
                            if not navegar_a_catalogo(driver):
                                break
                        else:
                            print(f"Error no relacionado con la sesión al obtener categorías: {str(e)}")
                            break
                
                if not categorias:
                    print("No se pudieron obtener las categorías, reintentando...")
                    if driver:
                        try:
                            driver.quit()
                        except:
                            pass
                        driver = None
                    continue
                
                print(f"\nTotal de categorías encontradas: {len(categorias)}")
                
                # Empezar desde la segunda categoría (índice 1)
                print("\nSaltando primera categoría (Folletos y promociones)")
                categorias_a_procesar = categorias[1:]
                print(f"Categorías a procesar: {len(categorias_a_procesar)}")
                
                # Procesar cada categoría
                for categoria in categorias_a_procesar:
                    if categoria['nombre'] in categorias_procesadas:
                        print(f"\nCategoría {categoria['nombre']} ya procesada, continuando...")
                        continue
                    
                    print(f"\nIniciando procesamiento de categoría {categoria['nombre']}")
                    print(f"URL: {categoria['url']}")
                    
                    exito, nuevo_driver = procesar_categoria(driver, categoria, todos_los_productos)
                    
                    if nuevo_driver is None:
                        print("\nSe perdió la sesión del driver, reiniciando...")
                        driver = reiniciar_sesion(driver)
                        if not driver:
                            break
                    else:
                        driver = nuevo_driver
                    
                    if exito:
                        categorias_procesadas.add(categoria['nombre'])
                        print(f"\nCategoría {categoria['nombre']} procesada exitosamente")
                        print(f"Progreso: {len(categorias_procesadas)}/{len(categorias_a_procesar)} categorías")
                    else:
                        print(f"\nError procesando categoría {categoria['nombre']}, reiniciando navegación...")
                        driver = reiniciar_sesion(driver)
                        if not driver:
                            print("No se pudo reiniciar la navegación, intentando de nuevo...")
                            break
                
                if len(categorias_procesadas) == len(categorias_a_procesar):
                    print("\n¡Todas las categorías procesadas exitosamente!")
                    break
            
            if driver:
                try:
                    driver.quit()
                except:
                    pass
                driver = None
            
        except Exception as e:
            print(f"\nError en la ejecución principal (intento {intento + 1}): {str(e)}")
            traceback.print_exc()
            if driver:
                try:
                    driver.quit()
                except:
                    pass
                driver = None
            
            if intento < max_reintentos - 1:
                print(f"\nReintentando en {5 * (intento + 1)} segundos...")
                time.sleep(5 * (intento + 1))
            else:
                print("\nSe alcanzó el máximo número de reintentos")
    
    print(f"\nTotal de productos recopilados: {len(todos_los_productos)}")
    print("Categorías procesadas:")
    for categoria in sorted(categorias_procesadas):
        print(f"- {categoria}")

if __name__ == "__main__":
    main()
