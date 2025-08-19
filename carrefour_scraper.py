import os 
import re
import csv
import time 
import random 
import argparse
from datetime import datetime
from bs4 import BeautifulSoup
from seleniumbase import Driver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
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

def carrefour_csv(datos, nombre_archivo="carrefour.csv"):
    """
    Guarda los datos en un archivo CSV.
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
    """
    try:
        # Asegurarse de que el precio sea un número
        if isinstance(precio, str):
            precio = precio.replace('€', '').replace(',', '.').strip()
        try:
            precio = float(precio)
        except ValueError as e:
            print(f"Error convirtiendo precio '{precio}' a float: {str(e)}")
            return None
        
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
            cantidad_total = sum(float(x.replace(',', '.')) for x in litros)
            if unidades:
                cantidad_total *= float(unidades[0])
            return precio / cantidad_total
            
        elif ml:
            cantidad_total = sum(float(x.replace(',', '.')) for x in ml) / 1000
            if unidades:
                cantidad_total *= float(unidades[0])
            return precio / cantidad_total
            
        elif kg:
            cantidad_total = sum(float(x.replace(',', '.')) for x in kg)
            if unidades:
                cantidad_total *= float(unidades[0])
            return precio / cantidad_total
            
        elif g:
            cantidad_total = sum(float(x.replace(',', '.')) for x in g) / 1000
            if unidades:
                cantidad_total *= float(unidades[0])
            return precio / cantidad_total
            
        return None
        
    except Exception as e:
        print(f"Error calculando precio unitario para formato '{formato}' y precio '{precio}': {str(e)}")
        return None

def obtener_categorias(driver):
    """Obtiene todas las categorías principales de Carrefour, excluyendo 'Mis Productos' y 'Ofertas'."""
    categorias = []
    categorias_excluidas = ['Mis productos', 'Ofertas']
    
    # Esperar a que el contenedor de categorías esté presente
    wait_for_elements(driver, By.CSS_SELECTOR, 'div.nav-first-level-categories')
    
    # Intentar hacer click en el botón "siguiente" hasta que no haya más categorías nuevas
    categorias_vistas = set()
    while True:
        # Obtener categorías visibles actuales
        elementos_categoria = wait_for_elements(driver, By.CSS_SELECTOR, 'div.nav-first-level-categories__slide', multiple=True)
        
        nuevas_categorias = False
        for elemento in elementos_categoria:
            try:
                titulo = elemento.get_attribute('title')
                if titulo not in categorias_vistas and titulo not in categorias_excluidas:
                    link = elemento.find_element(By.TAG_NAME, 'a')
                    url = link.get_attribute('href')
                    if url and 'supermercado' in url:
                        categorias.append({'titulo': titulo, 'url': url})
                        categorias_vistas.add(titulo)
                        nuevas_categorias = True
            except Exception as e:
                print(f"Error obteniendo categoría: {e}")
        
        # Si no hay categorías nuevas, terminar
        if not nuevas_categorias:
            break
            
        # Intentar hacer click en el botón siguiente
        try:
            boton_siguiente = driver.find_element(By.CSS_SELECTOR, 'button.nav-first-level-categories__next-button')
            if not boton_siguiente.is_displayed() or not boton_siguiente.is_enabled():
                break
            boton_siguiente.click()
            time.sleep(0.5)  # Pequeña espera para la animación
        except Exception as e:
            print("No se puede navegar a más categorías")
            break
    
    print(f"Categorías encontradas (excluyendo {', '.join(categorias_excluidas)}): {[cat['titulo'] for cat in categorias]}")
    return categorias

def reiniciar_driver(driver_actual=None):
    """Cierra el driver actual si existe y crea uno nuevo."""
    try:
        if driver_actual:
            driver_actual.quit()
    except:
        pass
    return iniciar_driver()

def verificar_sesion(driver):
    """Verifica si la sesión del driver es válida."""
    try:
        # Intenta acceder a una propiedad del driver para verificar la sesión
        driver.current_url
        return True
    except:
        return False

def obtener_datos_productos(driver, categoria):
    """Obtiene los datos de los productos dentro de una categoría."""
    productos = []
    current_offset = 0
    pagina_actual = 1
    productos_por_pagina = 24
    current_page = 1
    total_pages = None
    last_url = None
    max_reintentos = 3
    reintento_actual = 0
    same_url_count = 0
    max_same_url = 2
    
    while reintento_actual < max_reintentos:
        try:
            # Verificar si la sesión es válida
            if not verificar_sesion(driver):
                print("Sesión inválida detectada - reiniciando driver")
                driver = reiniciar_driver(driver)
                driver.get(categoria['url'])
                time.sleep(3)  # Espera adicional después de reiniciar
                try:
                    aceptar_cookies(driver)
                except:
                    pass

            while True:  # Loop para manejar la paginación
                print(f"\n=== Procesando página {pagina_actual} (offset: {current_offset}) ===")
                
                # Verificar sesión antes de cada operación importante
                if not verificar_sesion(driver):
                    raise Exception("Sesión perdida durante el procesamiento")
                
                # Obtener la URL actual para detectar bucles
                current_url = driver.current_url
                if current_url == last_url:
                    same_url_count += 1
                    print(f"Detectada misma URL que la anterior iteración (ocurrencia {same_url_count})")
                    if same_url_count >= max_same_url:
                        print("Detectado bucle - terminando categoría")
                        break
                else:
                    same_url_count = 0
                last_url = current_url
                
                # Esperar a que el contenedor principal de productos se cargue
                wait = WebDriverWait(driver, 10)
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'ul.product-card-list__list')))
                time.sleep(2)
                
                # Obtener información de paginación
                is_last_page = False
                try:
                    # Primero intentar encontrar el div de paginación
                    pagination_div = driver.find_element(By.CSS_SELECTOR, 'div.pagination__row')
                    print("\nDebug - HTML del div de paginación:")
                    print(pagination_div.get_attribute('outerHTML'))
                    
                    # Obtener todos los elementos de texto dentro del div de paginación
                    pagination_elements = pagination_div.find_elements(By.CSS_SELECTOR, '*')
                    pagination_info = ' '.join([el.text for el in pagination_elements if el.text.strip()])
                    print(f"\nDebug - Texto completo de paginación encontrado: '{pagination_info}'")
                    
                    # Buscar el patrón "Página X de Y" con una expresión regular más flexible
                    page_match = re.search(r'[Pp]ágina\s*(\d+)\s*de\s*(\d+)', pagination_info, re.IGNORECASE)
                    if page_match:
                        current_page = int(page_match.group(1))
                        total_pages = int(page_match.group(2))
                        print(f"Debug - Números extraídos - current_page: {current_page}, total_pages: {total_pages}")
                        # Verificar si estamos en la última página
                        is_last_page = current_page >= total_pages
                        print(f"¿Es última página? {is_last_page} (Página {current_page} de {total_pages})")
                    else:
                        print("Debug - No se encontró el patrón 'Página X de Y' en el texto")
                        # Intentar buscar los números de otra manera
                        all_numbers = re.findall(r'\d+', pagination_info)
                        print(f"Debug - Todos los números encontrados en el texto: {all_numbers}")
                        if len(all_numbers) >= 2:
                            current_page = int(all_numbers[0])
                            total_pages = int(all_numbers[-1])
                            print(f"Debug - Usando números alternativos - current_page: {current_page}, total_pages: {total_pages}")
                            is_last_page = current_page >= total_pages
                            print(f"¿Es última página? {is_last_page} (Página {current_page} de {total_pages})")
                        else:
                            print("No se pudo determinar la información de paginación")
                            is_last_page = False  # Continuamos hasta que podamos determinar los números
                except Exception as e:
                    print(f"Error obteniendo información de paginación: {e}")
                    is_last_page = False  # Continuamos hasta que podamos determinar los números

                # Obtener todos los items de la lista de productos
                items_productos = wait.until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'li.product-card-list__item'))
                )
                
                # Filtrar los items que son banners ocultos
                items_productos = [item for item in items_productos if 'trade-banner' not in item.get_attribute('class')]
                print(f"Productos válidos en esta página: {len(items_productos)}")

                productos_pagina = []  # Lista temporal para productos de esta página
                for index, item in enumerate(items_productos, 1):
                    try:
                        # Asegurar que el elemento está en el viewport antes de procesarlo
                        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", item)
                        time.sleep(0.5)
                        
                        # Verificar si el item está en el viewport y es interactuable
                        try:
                            is_visible = driver.execute_script("""
                                var elem = arguments[0];
                                if (elem.classList.contains('trade-banner')) return false;
                                var style = window.getComputedStyle(elem);
                                if (style.display === 'none' || style.visibility === 'hidden') return false;
                                var rect = elem.getBoundingClientRect();
                                return (
                                    rect.top >= 0 &&
                                    rect.left >= 0 &&
                                    rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
                                    rect.right <= (window.innerWidth || document.documentElement.clientWidth)
                                );
                            """, item)
                            
                            if not is_visible:
                                # Hacer scroll hasta el elemento
                                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", item)
                                time.sleep(0.5)  # Pequeña espera para que termine el scroll
                        except Exception as e:
                            print(f"Error verificando visibilidad: {str(e)}")
                            continue

                        # Verificar si es un item válido antes de procesarlo
                        if driver.execute_script("""
                            return arguments[0].classList.contains('trade-banner') || 
                                   arguments[0].style.display === 'none' ||
                                   !arguments[0].querySelector('.product-card__parent, .product-card-list__lazy-card, .product-card');
                        """, item):
                            print("Item no válido o banner, saltando...")
                            continue

                        print("\n=== Procesando nuevo item ===")
                        print(f"Clases del item: {item.get_attribute('class')}")
                        print(f"Style del item: {item.get_attribute('style')}")

                        # Intentar las diferentes rutas para encontrar el product-card
                        product_card = None
                        parent = None
                        
                        # Primera ruta: product-card__parent directo
                        try:
                            print("\n=== RUTA 1: Búsqueda directa de product-card__parent ===")
                            print("Intentando encontrar product-card__parent directamente...")
                            
                            # Mostrar el HTML del item para debug
                            print(f"HTML del item completo:\n{item.get_attribute('outerHTML')}\n")
                            
                            # Usar JavaScript para verificar si el elemento existe
                            parent_exists = driver.execute_script("""
                                const el = arguments[0].querySelector('div.product-card__parent');
                                console.log('Elemento encontrado:', el);
                                return el !== null;
                            """, item)
                            
                            print(f"¿Existe product-card__parent?: {parent_exists}")
                            
                            if parent_exists:
                                parent = item.find_element(By.CSS_SELECTOR, 'div.product-card__parent')
                                print("product-card__parent encontrado")
                                print(f"HTML del parent:\n{parent.get_attribute('outerHTML')}\n")
                                
                                # Obtener los atributos del parent
                                try:
                                    app_price = parent.get_attribute('app_price')
                                    app_price_per_unit = parent.get_attribute('app_price_per_unit')
                                    print(f"Atributos del parent - precio: {app_price}, precio por unidad: {app_price_per_unit}")
                                except Exception as e:
                                    print(f"Error obteniendo atributos del parent: {str(e)}")
                                    app_price = None
                                    app_price_per_unit = None
                                
                                product_card = parent.find_element(By.CSS_SELECTOR, 'div.product-card')
                                print("product-card encontrado dentro de parent")
                                print(f"HTML del product-card:\n{product_card.get_attribute('outerHTML')}\n")
                            else:
                                print("product-card__parent no encontrado")
                                raise Exception("Elemento no encontrado")
                            
                        except Exception as e:
                            print(f"Error en la primera ruta: {str(e)}")
                            try:
                                # Segunda ruta: lazy-card
                                print("\n=== RUTA 2: Búsqueda a través de lazy-card ===")
                                print("Buscando dentro de lazy-card...")
                                
                                # Mostrar el HTML del item para debug
                                print(f"HTML del item completo:\n{item.get_attribute('outerHTML')}\n")
                                
                                lazy_exists = driver.execute_script("""
                                    const el = arguments[0].querySelector('div.product-card-list__lazy-card');
                                    console.log('Lazy-card encontrado:', el);
                                    return el !== null;
                                """, item)
                                
                                print(f"¿Existe lazy-card?: {lazy_exists}")
                                
                                if lazy_exists:
                                    lazy_card = item.find_element(By.CSS_SELECTOR, 'div.product-card-list__lazy-card')
                                    print(f"HTML del lazy-card:\n{lazy_card.get_attribute('outerHTML')}\n")
                                    
                                    parent = lazy_card.find_element(By.CSS_SELECTOR, 'div.product-card__parent')
                                    print("product-card__parent encontrado dentro de lazy-card")
                                    print(f"HTML del parent:\n{parent.get_attribute('outerHTML')}\n")
                                    
                                    try:
                                        app_price = parent.get_attribute('app_price')
                                        app_price_per_unit = parent.get_attribute('app_price_per_unit')
                                        print(f"Atributos del parent - precio: {app_price}, precio por unidad: {app_price_per_unit}")
                                    except Exception as e:
                                        print(f"Error obteniendo atributos del parent en lazy-card: {str(e)}")
                                        app_price = None
                                        app_price_per_unit = None
                                    
                                    product_card = parent.find_element(By.CSS_SELECTOR, 'div.product-card')
                                    print("product-card encontrado dentro de lazy-card parent")
                                    print(f"HTML del product-card:\n{product_card.get_attribute('outerHTML')}\n")
                                else:
                                    print("lazy-card no encontrado")
                                    raise Exception("Elemento no encontrado")
                                
                            except Exception as e:
                                print(f"Error en la segunda ruta: {str(e)}")
                                try:
                                    # Tercera ruta: product-card directo
                                    print("\n=== RUTA 3: Búsqueda directa de product-card ===")
                                    print("Buscando div.product-card directamente...")
                                    
                                    # Mostrar el HTML del item para debug
                                    print(f"HTML del item completo:\n{item.get_attribute('outerHTML')}\n")
                                    
                                    card_exists = driver.execute_script("""
                                        const el = arguments[0].querySelector('div.product-card');
                                        console.log('Product-card encontrado:', el);
                                        return el !== null;
                                    """, item)
                                    
                                    print(f"¿Existe product-card?: {card_exists}")
                                    
                                    if card_exists:
                                        product_card = item.find_element(By.CSS_SELECTOR, 'div.product-card')
                                        print("product-card encontrado directamente")
                                        print(f"HTML del product-card:\n{product_card.get_attribute('outerHTML')}\n")
                                        app_price = None
                                        app_price_per_unit = None
                                    else:
                                        print("product-card no encontrado")
                                        raise Exception("Elemento no encontrado")
                                    
                                except Exception as e:
                                    print(f"Error en la tercera ruta: {str(e)}")
                                    print("No se pudo encontrar la estructura del producto")
                                    continue

                        if not product_card:
                            print("No se encontró product-card por ninguna ruta")
                            continue

                        # Obtener información del producto
                        try:
                            # Navegar hasta el contenedor de información
                            try:
                                info_container = product_card.find_element(By.CSS_SELECTOR, 'div.product-card__info-container')
                                print("Contenedor de información encontrado")
                            except Exception as e:
                                print(f"Error encontrando contenedor de información: {str(e)}")
                                continue
                            
                            try:
                                detail_container = info_container.find_element(By.CSS_SELECTOR, 'div.product-card__detail')
                                print("Contenedor de detalles encontrado")
                            except Exception as e:
                                print(f"Error encontrando contenedor de detalles: {str(e)}")
                                continue

                            # Obtener el título
                            titulo = ""
                            try:
                                print("Buscando título...")
                                # Primero intentar obtener el título de la imagen
                                try:
                                    img_element = product_card.find_element(By.CSS_SELECTOR, 'img.product-card__image')
                                    titulo = img_element.get_attribute('alt')
                                    print(f"Título obtenido de la imagen: '{titulo}'")
                                except Exception as e:
                                    print(f"Error obteniendo título de la imagen: {str(e)}")
                                
                                # Si no hay título de la imagen, intentar del h2
                                if not titulo:
                                    print("Buscando título en h2...")
                                    try:
                                        titulo_h2 = product_card.find_element(By.CSS_SELECTOR, 'h2.product-card__title')
                                        print("h2 encontrado")
                                        titulo_element = titulo_h2.find_element(By.CSS_SELECTOR, 'a.product-card__title-link')
                                        print("Enlace de título encontrado")
                                        try:
                                            titulo = driver.execute_script(
                                                "return arguments[0].textContent.replace(/\\s+/g, ' ').trim()",
                                                titulo_element
                                            )
                                            print(f"Título obtenido del enlace: '{titulo}'")
                                        except Exception as e:
                                            print(f"Error ejecutando JavaScript para título: {str(e)}")
                                            titulo = titulo_element.text.strip()
                                            print(f"Título obtenido como texto plano: '{titulo}'")
                                    except Exception as e:
                                        print(f"Error obteniendo título del h2: {str(e)}")
                                
                                if not titulo:
                                    titulo = "Título no disponible"
                                
                            except Exception as e:
                                print(f"Error al obtener título: {str(e)}")
                                titulo = "Título no disponible"

                            # Obtener el precio
                            precio = app_price if app_price else "Precio no disponible"
                            if not precio or precio == "Precio no disponible":
                                try:
                                    print("Buscando precio en el DOM...")
                                    elementos_precio = product_card.find_elements(By.CSS_SELECTOR, 'span.product-card__price')
                                    print(f"Encontrados {len(elementos_precio)} elementos de precio")
                                    for precio_element in elementos_precio:
                                        try:
                                            print(f"HTML del elemento precio: {precio_element.get_attribute('outerHTML')}")
                                            try:
                                                precio_texto = driver.execute_script(
                                                    "return arguments[0].textContent.replace(/\\s+/g, ' ').trim()",
                                                    precio_element
                                                )
                                            except Exception as e:
                                                print(f"Error ejecutando JavaScript para precio: {str(e)}")
                                                precio_texto = precio_element.text.strip()
                                                
                                            print(f"Texto extraído del precio: '{precio_texto}'")
                                            if precio_texto:
                                                precio = precio_texto
                                                print(f"Precio encontrado en el DOM: {precio}")
                                                break
                                        except Exception as e:
                                            print(f"Error procesando elemento de precio: {str(e)}")
                                            continue
                                except Exception as e:
                                    print(f"Error obteniendo precio del DOM: {e}")

                            # Obtener precio por unidad
                            precio_unidad = app_price_per_unit if app_price_per_unit else None
                            if not precio_unidad:
                                try:
                                    print("Buscando precio por unidad en el DOM...")
                                    elementos_precio_unidad = product_card.find_elements(By.CSS_SELECTOR, 'span.product-card__price-per-unit')
                                    print(f"Encontrados {len(elementos_precio_unidad)} elementos de precio por unidad")
                                    for precio_unidad_element in elementos_precio_unidad:
                                        try:
                                            print(f"HTML del elemento precio por unidad: {precio_unidad_element.get_attribute('outerHTML')}")
                                            try:
                                                precio_unidad_texto = driver.execute_script(
                                                    "return arguments[0].textContent.replace(/\\s+/g, ' ').trim()",
                                                    precio_unidad_element
                                                )
                                            except Exception as e:
                                                print(f"Error ejecutando JavaScript para precio por unidad: {str(e)}")
                                                precio_unidad_texto = precio_unidad_element.text.strip()
                                                
                                            print(f"Texto extraído del precio por unidad: '{precio_unidad_texto}'")
                                            if precio_unidad_texto:
                                                precio_unidad = precio_unidad_texto
                                                print(f"Precio por unidad encontrado en el DOM: {precio_unidad}")
                                                break
                                        except Exception as e:
                                            print(f"Error procesando elemento de precio por unidad: {str(e)}")
                                            continue
                                except Exception as e:
                                    print(f"Error obteniendo precio por unidad del DOM: {e}")

                            # Procesar precio unitario
                            precio_unitario = None
                            unidad = None
                            if precio_unidad:
                                match = re.search(r'(\d+[.,]\d+)\s*€/(\w+)', precio_unidad)
                                if match:
                                    precio_unitario = match.group(1).replace(',', '.')
                                    unidad = match.group(2)

                            # Si no hay precio por unidad, intentar calcularlo del título
                            if not precio_unitario and precio != "Precio no disponible":
                                # Limpiar el precio antes de los cálculos
                                precio_limpio = precio.replace('€', '').replace(',', '.').strip()
                                try:
                                    precio_num = float(precio_limpio)
                                    formato_match = re.search(r'(\d+(?:[.,]\d+)?)\s*(kg|g|l|ml|cl|ud|unidad(?:es)?|botella(?:s)?|lata(?:s)?|pack(?:s)?)', titulo, re.IGNORECASE)
                                    if formato_match:
                                        cantidad = float(formato_match.group(1).replace(',', '.'))
                                        unidad_medida = formato_match.group(2).lower()
                                        
                                        if unidad_medida in ['g']:
                                            cantidad = cantidad / 1000
                                            unidad = 'kg'
                                        elif unidad_medida in ['ml', 'cl']:
                                            cantidad = cantidad / 1000 if unidad_medida == 'ml' else cantidad / 100
                                            unidad = 'l'
                                        elif unidad_medida in ['kg', 'l']:
                                            unidad = unidad_medida
                                        else:
                                            unidad = 'ud'
                                        
                                        precio_unitario = str(round(precio_num / cantidad, 2))
                                except Exception as e:
                                    print(f"Error calculando precio unitario: {str(e)}")
                                    precio_unitario = None

                            # Obtener información de promoción
                            promocion = None
                            try:
                                badge_div = product_card.find_element(By.CSS_SELECTOR, 'div.product-card__badge')
                                promo_element = badge_div.find_element(By.CSS_SELECTOR, 'span.badge__name')
                                promocion = promo_element.get_attribute('title') or promo_element.text.strip()
                            except:
                                pass

                            # Verificar si el producto está agotado
                            estado_producto = "Disponible"
                            try:
                                footer = product_card.find_element(By.CSS_SELECTOR, 'div.product-card__footer')
                                boton_agotado = footer.find_elements(By.CSS_SELECTOR, 'button.add-to-cart-button__button--sold-out')
                                if boton_agotado:
                                    estado_producto = "Agotado temporalmente"
                            except Exception as e:
                                print(f"Error verificando disponibilidad del producto: {e}")

                            print(f"Producto: {titulo}")
                            print(f"Precio: {precio}")
                            print(f"Precio unitario: {precio_unitario}€/{unidad}" if precio_unitario and unidad else "Precio unitario no disponible")
                            if promocion:
                                print(f"Promoción: {promocion}")

                            producto_actual = {
                                'titulo': titulo,
                                'precio': precio,
                                'precio_unitario': f"{precio_unitario}€/{unidad}" if precio_unitario and unidad else "No disponible",
                                'categoria': categoria['titulo'],
                                'promocion': promocion if promocion else "No disponible",
                                'estado': estado_producto,
                                'fecha_extraccion': datetime.now().strftime('%Y-%m-%d')
                            }

                            # Añadir el producto procesado a la lista temporal
                            productos_pagina.append(producto_actual)

                        except Exception as e:
                            print(f"Error procesando detalles del producto: {str(e)}")
                            continue

                    except Exception as e:
                        print(f"Error procesando producto {index}: {str(e)}")
                        continue

                # Añadir productos de esta página a la lista principal
                productos.extend(productos_pagina)
                print(f"Productos procesados en página {pagina_actual}: {len(productos_pagina)}")
                print(f"Total productos recolectados hasta ahora en {categoria['titulo']}: {len(productos)}")

                # Manejar paginación
                try:
                    next_links = driver.find_elements(By.CSS_SELECTOR, 'div.pagination__row a[href]')
                    print(f"Enlaces de paginación encontrados: {len(next_links)}")
                    
                    # Verificar si estamos en la última página usando múltiples indicadores
                    is_last_page = False
                    
                    # 1. Verificar por el texto de paginación (método más confiable)
                    try:
                        pagination_div = driver.find_element(By.CSS_SELECTOR, 'div.pagination__row')
                        pagination_text = pagination_div.text
                        page_match = re.search(r'[Pp]ágina\s*(\d+)\s*de\s*(\d+)', pagination_text, re.IGNORECASE)
                        if page_match:
                            current_page = int(page_match.group(1))
                            total_pages = int(page_match.group(2))
                            print(f"Información de paginación: Página {current_page} de {total_pages}")
                            if current_page >= total_pages:
                                print(f"Última página confirmada ({current_page}/{total_pages})")
                                is_last_page = True
                    except Exception as e:
                        print(f"No se pudo verificar el texto de paginación: {e}")
                    
                    # 2. Verificar por la ausencia de enlace "siguiente" o enlace inválido
                    if not is_last_page and next_links:
                        last_link = next_links[-1]
                        last_link_url = last_link.get_attribute('href')
                        if not last_link_url or 'offset=' not in last_link_url:
                            print("Última página detectada por falta de enlace siguiente válido")
                            is_last_page = True
                        elif last_link_url == current_url:
                            print("Última página detectada por enlace siguiente igual a URL actual")
                            is_last_page = True
                    
                    # 3. Verificar por cantidad de productos en la página
                    items_productos = driver.find_elements(By.CSS_SELECTOR, 'li.product-card-list__item')
                    if len(items_productos) < productos_por_pagina and len(items_productos) > 0:
                        print(f"Posible última página detectada por cantidad de productos ({len(items_productos)} < {productos_por_pagina})")
                        is_last_page = True
                    
                    if is_last_page:
                        print("Confirmada última página - terminando categoría")
                        break
                    
                    # Si no es la última página, intentar navegar a la siguiente
                    if next_links:
                        next_link = next_links[-1]
                        next_url = next_link.get_attribute('href')
                        print(f"URL del siguiente enlace encontrado: {next_url}")
                        
                        if 'offset=' in next_url and next_url != current_url:
                            print(f"Avanzando a la página {pagina_actual + 1}")
                            
                            try:
                                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", next_link)
                                time.sleep(1)
                            except Exception as e:
                                print(f"Error haciendo scroll al enlace: {e}")
                            
                            try:
                                driver.execute_script("arguments[0].click();", next_link)
                            except Exception as js_error:
                                print(f"Error haciendo clic con JavaScript: {js_error}")
                                try:
                                    driver.get(next_url)
                                except Exception as nav_error:
                                    print(f"Error en navegación directa: {nav_error}")
                                    raise Exception("Error de navegación")
                            
                            current_offset += productos_por_pagina
                            pagina_actual += 1
                            
                            # Verificar que la navegación fue exitosa
                            wait = WebDriverWait(driver, 10)
                            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'ul.product-card-list__list')))
                            time.sleep(2)
                        else:
                            print("El enlace no es válido o es la misma página actual - terminando categoría")
                            break
                    else:
                        print("No se encontraron enlaces de paginación - terminando categoría")
                        break

                except Exception as e:
                    print(f"Error al procesar la paginación: {str(e)}")
                    raise  # Re-lanzar la excepción para el manejo de reintentos

            # Si llegamos aquí sin excepciones, salimos del bucle de reintentos
            break

        except Exception as e:
            print(f"Error durante el procesamiento (intento {reintento_actual + 1} de {max_reintentos}): {str(e)}")
            reintento_actual += 1
            
            if reintento_actual < max_reintentos:
                print("Reiniciando driver y reintentando...")
                driver = reiniciar_driver(driver)
                # Volver a la última URL exitosa o al inicio de la categoría
                try:
                    if last_url and 'offset=' in last_url:
                        driver.get(last_url)
                    else:
                        driver.get(categoria['url'])
                    time.sleep(3)
                    try:
                        aceptar_cookies(driver)
                    except:
                        pass
                except:
                    print("Error al navegar después de reiniciar - usando URL de categoría")
                    driver.get(categoria['url'])
            else:
                print("Se alcanzó el máximo número de reintentos - terminando categoría")

    print(f"\n=== Resumen de categoría: {categoria['titulo']} ===")
    print(f"Total páginas procesadas: {pagina_actual}")
    print(f"Total productos recolectados: {len(productos)}")
    return productos

def aceptar_cookies(driver):
    """Acepta las cookies si aparece el diálogo."""
    try:
        # Esperar a que el botón de cookies esté presente y sea clickeable
        boton_cookies = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
        )
        # Intentar hacer click con JavaScript si el click normal falla
        try:
            boton_cookies.click()
        except ElementClickInterceptedException:
            driver.execute_script("arguments[0].click();", boton_cookies)
        
        # Esperar a que el diálogo desaparezca
        WebDriverWait(driver, 5).until(
            EC.invisibility_of_element_located((By.ID, "onetrust-banner-sdk"))
        )
        time.sleep(0.5)  # Pequeña espera adicional para asegurar que el diálogo se ha cerrado
    except Exception as e:
        print("No se encontró el diálogo de cookies o ya fue aceptado")
        # No lanzamos la excepción ya que es normal que no aparezca el diálogo en algunas ocasiones

def signal_handler(sig, frame):
    print('\nCerrando el navegador gracefully...')
    try:
        if 'driver' in globals():
            driver.quit()
    except:
        pass
    sys.exit(0)

def main():
    # Configurar el parser de argumentos
    parser = argparse.ArgumentParser(description='Scraper de Carrefour con opciones de testing')
    parser.add_argument('--categoria', type=str, help='Nombre de la categoría para empezar (para testing)')
    parser.add_argument('--pagina', type=int, help='Número de página para empezar dentro de la categoría (para testing)')
    parser.add_argument('--offset', type=int, help='Offset específico para empezar (para testing)')
    args = parser.parse_args()

    signal.signal(signal.SIGINT, signal_handler)
    driver = iniciar_driver()
    
    try:
        # Navegar a la página principal de Carrefour
        driver.get("https://www.carrefour.es/supermercado/")
        print("\nNavegando a la página principal...")
        
        # Aceptar cookies si aparece el diálogo
        aceptar_cookies(driver)
        
        # Obtener categorías
        categorias = obtener_categorias(driver)
        print(f"\nSe encontraron {len(categorias)} categorías en total")
        
        # Si se especificó una categoría para testing, encontrarla en la lista
        categoria_inicio = 0
        if args.categoria:
            for i, cat in enumerate(categorias):
                if args.categoria.lower() in cat['titulo'].lower():
                    categoria_inicio = i
                    print(f"\n=== Iniciando desde la categoría: {cat['titulo']} ===")
                    break
            else:
                print(f"Advertencia: No se encontró la categoría '{args.categoria}'. Iniciando desde el principio.")
        
        todos_productos = []
        
        # Iterar sobre cada categoría, empezando desde la especificada
        for num_categoria, categoria in enumerate(categorias[categoria_inicio:], categoria_inicio + 1):
            print(f"\n=== Procesando categoría {num_categoria}/{len(categorias)}: {categoria['titulo']} ===")
            print(f"URL: {categoria['url']}")
            
            try:
                # Si se especificó una página de inicio y estamos en la categoría correcta
                if args.pagina and num_categoria == categoria_inicio + 1:
                    offset = (args.pagina - 1) * 24  # 24 productos por página
                    url_con_offset = f"{categoria['url']}?offset={offset}"
                    print(f"Iniciando desde la página {args.pagina} (offset: {offset})")
                    driver.get(url_con_offset)
                elif args.offset and num_categoria == categoria_inicio + 1:
                    url_con_offset = f"{categoria['url']}?offset={args.offset}"
                    print(f"Iniciando desde offset específico: {args.offset}")
                    driver.get(url_con_offset)
                else:
                    driver.get(categoria['url'])
                
                time.sleep(3)
                
                try:
                    aceptar_cookies(driver)
                except Exception as e:
                    print(f"No se pudo aceptar cookies en categoría {categoria['titulo']}: {e}")
                
                # Verificar sesión antes de procesar la categoría
                if not verificar_sesion(driver):
                    print("Sesión inválida detectada - reiniciando driver")
                    driver = reiniciar_driver(driver)
                    driver.get(categoria['url'])
                    time.sleep(3)
                    try:
                        aceptar_cookies(driver)
                    except:
                        pass
                
                print("\nIniciando procesamiento de productos...")
                productos = obtener_datos_productos(driver, categoria)
                todos_productos.extend(productos)
                
                # Guardar datos parcialmente
                if productos:
                    print(f"\nGuardando datos parciales de {categoria['titulo']}...")
                    carrefour_csv(productos)
                    print(f"Guardados {len(productos)} productos")
                
                print(f"\n=== Completada categoría {num_categoria}/{len(categorias)} ===")
                print(f"Productos en esta categoría: {len(productos)}")
                print(f"Total productos acumulados: {len(todos_productos)}")
                
            except Exception as e:
                print(f"\n❌ Error procesando categoría {categoria['titulo']}: {e}")
                # Reiniciar el driver si hay un error grave
                driver = reiniciar_driver(driver)
                continue
            
            time.sleep(2)
        
        print("\n=== RESUMEN FINAL ===")
        print(f"Total categorías procesadas: {len(categorias[categoria_inicio:])}")
        print(f"Total productos recolectados: {len(todos_productos)}")
        
    except Exception as e:
        print(f"\n❌ Error general: {e}")
    
    finally:
        print("\nCerrando el navegador...")
        try:
            driver.quit()
            print("Navegador cerrado exitosamente")
        except:
            print("Error al cerrar el navegador")
        print("\n=== PROCESO COMPLETADO ===")

if __name__ == "__main__":
    main()
