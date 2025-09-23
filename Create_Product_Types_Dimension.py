import pandas as pd
import re
import numpy as np
from sqlalchemy import create_engine
import warnings
warnings.filterwarnings('ignore')

# Configuración de la base de datos
server = 'localhost,1433'
database = 'Supermarkets'
username = 'sa'
password = 'XXXX'

print("Conectando a la base de datos...")
engine = create_engine(
    f"mssql+pyodbc://sa:{password}@localhost:1433/{database}?driver=ODBC+Driver+17+for+SQL+Server"
)

def load_existing_data():
    """Cargar datos del modelo existente"""
    print("Cargando datos del modelo existente...")
    
    try:
        # Cargar DimProducts
        products_query = "SELECT ProductID, Name, Weight, Unit FROM DimProduct"
        df_products = pd.read_sql(products_query, engine)
        print(f"  - DimProducts: {len(df_products)} productos")
        
        # Cargar DimCategories para referencia
        categories_query = "SELECT CategoryID, CategoryName FROM DimCategory"
        df_categories = pd.read_sql(categories_query, engine)
        print(f"  - DimCategory: {len(df_categories)} categorías")
        
        # Cargar DimSupermarkets para referencia
        supermarkets_query = "SELECT SupermarketID,Name FROM DimSupermarket"
        df_supermarkets = pd.read_sql(supermarkets_query, engine)
        print(f"  - DimSupermarket: {len(df_supermarkets)} supermercados")
        
        return df_products, df_categories, df_supermarkets
        
    except Exception as e:
        print(f" Error cargando datos: {e}")
        return None, None, None

def extract_product_type_from_name(name):
    """Extraer el tipo de producto del nombre con clasificación jerárquica mejorada"""
    if pd.isna(name):
        return 'OTROS'
    
    name_lower = name.lower()
    
    # Normalizar acentos
    replacements = {'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u', 'ü': 'u', 'ñ': 'n'}
    for old, new in replacements.items():
        name_lower = name_lower.replace(old, new)
    
    # Eliminar marcas comunes
    brands_to_remove = [
        'hacendado', 'carrefour', 'alcampo', 'mercadona', 'dia', 'eroski', 
        'condis', 'bonpreu', 'esclat', 'consum', 'caprabo', 'simply', 'ah',
        'danone', 'nestle', 'kelloggs', 'pescanova', 'campofrio', 'elpozo',
        'philadelphia', 'innocent', 'findus', 'casa tarradellas', 'arla',
        'krissia', 'fritifresh', 'florette', 'polasal', 'casa juncal'
    ]
    for brand in brands_to_remove:
        name_lower = re.sub(rf'\b{brand}\b', '', name_lower)
    
    # Limpiar espacios extra
    name_lower = re.sub(r'\s+', ' ', name_lower).strip()
    
    # Definir tipos de productos con palabras clave más específicas
    product_types = {
        # LÁCTEOS - LECHE
        'LECHE_ENTERA': ['leche entera', 'leche entera'],
        'LECHE_SEMIDESNATADA': ['leche semidesnatada', 'leche semidesnatada'],
        'LECHE_DESNATADA': ['leche desnatada', 'leche desnatada'],
        'LECHE_CONDENSADA': ['leche condensada'],
        'LECHE_EVAPORADA': ['leche evaporada'],
        'LECHE_SIN_LACTOSA': ['leche sin lactosa', 'leche sin lactosa'],
        
        # LÁCTEOS - YOGURES
        'YOGUR_NATURAL': ['yogur natural', 'yogurt natural'],
        'YOGUR_GRIEGO': ['yogur griego', 'yogurt griego'],
        'YOGUR_FRUTAS': ['yogur frutas', 'yogurt frutas', 'yogur de frutas'],
        'YOGUR_BEBIBLE': ['yogur bebible', 'yogurt bebible'],
        'YOGUR_DESNATADO': ['yogur desnatado', 'yogurt desnatado'],
        
        # LÁCTEOS - QUESOS
        'QUESO_MANCHEGO': ['queso manchego', 'manchego'],
        'QUESO_GOUDA': ['queso gouda', 'gouda'],
        'QUESO_MOZZARELLA': ['queso mozzarella', 'mozzarella'],
        'QUESO_EDAM': ['queso edam', 'edam'],
        'QUESO_HAVARTI': ['queso havarti', 'havarti'],
        'QUESO_RALLADO': ['queso rallado', 'rallado'],
        'QUESO_UNTAR': ['queso untar', 'queso de untar', 'crema queso'],
        'QUESO_FRESCO': ['queso fresco', 'queso blanco'],
        
        # LÁCTEOS - OTROS
        'MANTEQUILLA': ['mantequilla'],
        'NATA': ['nata', 'crema'],
        'HUEVOS': ['huevos', 'huevo'],
        
        # ACEITES
        'ACEITE_OLIVA_VIRGEN_EXTRA': ['aceite oliva virgen extra', 'aceite de oliva virgen extra'],
        'ACEITE_OLIVA_VIRGEN': ['aceite oliva virgen', 'aceite de oliva virgen'],
        'ACEITE_OLIVA_REFINADO': ['aceite oliva refinado', 'aceite de oliva refinado', 'aceite oliva 1º'],
        'ACEITE_GIRASOL': ['aceite girasol', 'aceite de girasol'],
        'ACEITE_COCO': ['aceite coco', 'aceite de coco'],
        'ACEITE_VEGETAL': ['aceite vegetal'],
        
        # PAN Y BOLLERÍA
        'PAN_INTEGRAL': ['pan integral', 'pan de molde integral'],
        'PAN_BLANCO': ['pan blanco', 'pan de molde blanco'],
        'PAN_RUSTICO': ['pan rustico', 'pan rústico', 'barra rustica'],
        'BAGUETTE': ['baguette', 'barra pan', 'barra de pan pistola'],
        'PANECILLO': ['panecillo', 'bollo'],
        'PAN_LECHE': ['pan leche', 'pan de leche'],
        'DONUTS': ['donuts', 'donut', 'berlina'],
        
        # ARROZ Y PASTA
        'ARROZ_REDONDO': ['arroz redondo', 'arroz de grano redondo'],
        'ARROZ_LARGO': ['arroz largo', 'arroz de grano largo'],
        'ARROZ_BASMATI': ['arroz basmati', 'basmati'],
        'ARROZ_INTEGRAL': ['arroz integral'],
        'PASTA_ESPAGUETI': ['espagueti', 'pasta espagueti'],
        'PASTA_MACARRONES': ['macarrones', 'pasta macarrones'],
        'PASTA_FIDEOS': ['fideos', 'pasta fideos'],
        'PASTA_LASAÑA': ['lasaña', 'lasagna'],
        
        # BEBIDAS - AGUA Y REFRESCOS
        'AGUA_MINERAL': ['agua mineral', 'agua'],
        'COCA_COLA': ['coca cola', 'coca-cola', 'coca'],
        'FANTA': ['fanta'],
        'SPRITE': ['sprite'],
        'ZUMO_NARANJA': ['zumo naranja', 'jugo naranja'],
        'ZUMO_MANZANA': ['zumo manzana', 'jugo manzana'],
        'SMOOTHIE': ['smoothie'],
        
        # BEBIDAS ALCOHÓLICAS
        'CERVEZA_MAHOU': ['cerveza mahou', 'mahou'],
        'CERVEZA_HEINEKEN': ['cerveza heineken', 'heineken'],
        'CERVEZA_CORONA': ['cerveza corona', 'corona'],
        'CERVEZA': ['cerveza'],
        'VINO_TINTO': ['vino tinto'],
        'VINO_BLANCO': ['vino blanco'],
        'VINO_ROSADO': ['vino rosado'],
        'WHISKY': ['whisky', 'whiskey'],
        'RON': ['ron'],
        'GINEBRA': ['ginebra'],
        'VODKA': ['vodka'],
        
        # PESCADO FRESCO - MUY ESPECÍFICO
        'SALMON_FRESCO': ['salmon fresco', 'salmón fresco', 'salmon entero', 'salmón entero'],
        'MERLUZA_FRESCA': ['merluza fresca', 'merluza entera'],
        'BACALAO_FRESCO': ['bacalao fresco', 'bacalao entero'],
        'DORADA_FRESCA': ['dorada fresca', 'dorada entera'],
        'LUBINA_FRESCA': ['lubina fresca', 'lubina entera'],
        'ATUN_FRESCO': ['atun fresco', 'atún fresco', 'atun entero', 'atún entero'],
        'BOQUERONES_FRESCOS': ['boquerones frescos', 'anchoas frescas'],
        'SARDINAS_FRESCAS': ['sardinas frescas', 'sardina fresca'],
        'PESCADO_FRESCO_GENERICO': ['pescado fresco', 'pescado entero'],
        
        # PESCADO EN LATA/CONSERVA
        'ATUN_LATA': ['atun lata', 'atún lata', 'atun en lata', 'atún en lata'],
        'SARDINAS_LATA': ['sardinas lata', 'sardinas en lata'],
        'ANCHOAS_LATA': ['anchoas lata', 'anchoas en lata'],
        'SALMON_LATA': ['salmon lata', 'salmón lata', 'salmon en lata', 'salmón en lata'],
        'MERLUZA_LATA': ['merluza lata', 'merluza en lata'],
        
        # CARNE FRESCA - MUY ESPECÍFICO
        'POLLO_ENTERO': ['pollo entero', 'pollo'],
        'MUSLO_POLLO': ['muslo pollo', 'muslos pollo'],
        'PECHUGA_POLLO': ['pechuga pollo', 'pechugas pollo'],
        'ALAS_POLLO': ['alas pollo', 'alitas pollo'],
        'LOMO_CERDO': ['lomo cerdo', 'lomo de cerdo'],
        'SOLOMILLO_CERDO': ['solomillo cerdo', 'solomillo de cerdo'],
        'CHULETAS_CERDO': ['chuletas cerdo', 'chuletas de cerdo'],
        'BACON_CERDO': ['bacon', 'bacon cerdo', 'bacon de cerdo'],
        'JAMON_CERDO': ['jamon cerdo', 'jamón cerdo', 'jamon de cerdo', 'jamón de cerdo'],
        'SOLOMILLO_TERNERA': ['solomillo ternera', 'solomillo de ternera'],
        'CHULETAS_TERNERA': ['chuletas ternera', 'chuletas de ternera'],
        'CORDERO_ENTERO': ['cordero entero', 'cordero'],
        'CHULETAS_CORDERO': ['chuletas cordero', 'chuletas de cordero'],
        'PAVO_ENTERO': ['pavo entero', 'pavo'],
        'PECHUGA_PAVO': ['pechuga pavo', 'pechugas pavo'],
        'CARNE_FRESCA_GENERICA': ['carne fresca', 'carne'],
        
        # FRUTAS FRESCAS - MUY ESPECÍFICO
        'MANZANA_GOLDEN': ['manzana golden', 'manzanas golden'],
        'MANZANA_FUJI': ['manzana fuji', 'manzanas fuji'],
        'MANZANA_GRANNY': ['manzana granny', 'manzanas granny'],
        'PLATANO_CANARIO': ['platano canario', 'plátano canario', 'platano canarias', 'plátano canarias'],
        'PLATANO_ECUADOR': ['platano ecuador', 'plátano ecuador'],
        'NARANJA_MESA': ['naranja mesa', 'naranjas mesa', 'naranja de mesa'],
        'NARANJA_ZUMO': ['naranja zumo', 'naranjas zumo', 'naranja para zumo'],
        'PERA_CONFERENCIA': ['pera conferencia', 'peras conferencia'],
        'PERA_BLANQUILLA': ['pera blanquilla', 'peras blanquilla'],
        'MELOCOTON_ROJO': ['melocoton rojo', 'melocotón rojo', 'melocotones rojos'],
        'NECTARINA_AMARILLA': ['nectarina amarilla', 'nectarinas amarillas', 'nectarina carne amarilla'],
        'ALBARICOQUE': ['albaricoque', 'albaricoques'],
        'CEREZAS': ['cerezas', 'cereza'],
        'FRESAS': ['fresas', 'fresa', 'fresones'],
        'FRAMBUESAS': ['frambuesas', 'frambuesa'],
        'ARANDANOS': ['arandanos', 'arándanos', 'arandano', 'arándano'],
        'UVA_BLANCA': ['uva blanca', 'uvas blancas'],
        'UVA_ROJA': ['uva roja', 'uvas rojas'],
        'SANDIA': ['sandia', 'sandía', 'sandia negra'],
        'MELON_CANTALOUP': ['melon cantaloup', 'melón cantaloup'],
        'MELON_PIEL_SAPO': ['melon piel sapo', 'melón piel sapo'],
        'MANGO': ['mango', 'mangos'],
        'AGUACATE': ['aguacate', 'aguacates'],
        'LIMON': ['limon', 'limón', 'limones'],
        'LIMA': ['lima', 'limas'],
        'PIÑA': ['piña', 'piña en rodajas', 'pina'],
        'FRUTA_FRESCA_GENERICA': ['fruta fresca', 'fruta'],
        
        # VERDURAS FRESCAS - MUY ESPECÍFICO
        'TOMATE_PERITA': ['tomate perita', 'tomate pera', 'tomates perita', 'tomates pera'],
        'TOMATE_CHERRY': ['tomate cherry', 'tomates cherry'],
        'TOMATE_RAMA': ['tomate rama', 'tomates rama'],
        'TOMATE_ENSALADA': ['tomate ensalada', 'tomates ensalada'],
        'TOMATE_ROSA': ['tomate rosa', 'tomates rosa'],
        'TOMATE_NEGRO': ['tomate negro', 'tomates negro'],
        'LECHUGA_ICEBERG': ['lechuga iceberg', 'lechugas iceberg'],
        'LECHUGA_COGOLLO': ['lechuga cogollo', 'lechugas cogollo', 'cogollos'],
        'LECHUGA_ROMANA': ['lechuga romana', 'lechugas romana'],
        'PIMIENTO_ROJO': ['pimiento rojo', 'pimientos rojos'],
        'PIMIENTO_VERDE': ['pimiento verde', 'pimientos verdes'],
        'PIMIENTO_ITALIANO': ['pimiento italiano', 'pimientos italianos'],
        'CEBOLLA_DULCE': ['cebolla dulce', 'cebollas dulces'],
        'CEBOLLA_BLANCA': ['cebolla blanca', 'cebollas blancas', 'cebolla granel'],
        'ZANAHORIA': ['zanahoria', 'zanahorias'],
        'CALABACIN': ['calabacin', 'calabacín', 'calabacines'],
        'BERENJENA': ['berenjena', 'berenjenas'],
        'PEPINO': ['pepino', 'pepinos'],
        'PATATA_LAVADA': ['patata lavada', 'patatas lavadas'],
        'PATATA_NORMAL': ['patata normal', 'patatas normales'],
        'ALCACHOFA': ['alcachofa', 'alcachofas'],
        'ESPINACAS': ['espinacas', 'espinaca'],
        'VERDURA_FRESCA_GENERICA': ['verdura fresca', 'verdura'],
        
        # PRODUCTOS DE LIMPIEZA
        'DETERGENTE_LAVADORA': ['detergente lavadora', 'detergente'],
        'SUAVIZANTE': ['suavizante'],
        'DETERGENTE_LAVAJILLAS': ['detergente lavavajillas', 'detergente lavajillas'],
        'LIMPIEZA_SUELOS': ['limpiador suelos', 'limpiador de suelos'],
        'LIMPIEZA_BAÑO': ['limpiador baño', 'limpiador de baño'],
        'LIMPIEZA_COCINA': ['limpiador cocina', 'limpiador de cocina'],
        'LEJIA': ['lejia', 'lejía'],
        'AMONIACO': ['amoniaco'],
        'BAYETAS': ['bayetas', 'bayeta'],
        'ESTROPAJOS': ['estropajos', 'estropajo'],
        
        # PAPEL Y HOGAR
        'PAPEL_HIGIENICO': ['papel higienico', 'papel higiénico'],
        'BOLSAS_BASURA': ['bolsas basura', 'bolsas de basura'],
        'PAPEL_COCINA': ['papel cocina', 'papel de cocina'],
        'FILM_TRANSPARENTE': ['film transparente', 'papel film'],
        'ALUMINIO': ['aluminio', 'papel aluminio'],
        
        # CONGELADOS
        'CONGELADOS_PESCADO': ['pescado congelado', 'congelados pescado'],
        'CONGELADOS_CARNE': ['carne congelada', 'congelados carne'],
        'CONGELADOS_VERDURAS': ['verduras congeladas', 'congelados verduras'],
        'CONGELADOS_FRUTAS': ['frutas congeladas', 'congelados frutas'],
        'CONGELADOS_PIZZA': ['pizza congelada', 'congelados pizza'],
        
        # CONSERVAS
        'CONSERVAS_PESCADO': ['conservas pescado', 'conservas de pescado'],
        'CONSERVAS_CARNE': ['conservas carne', 'conservas de carne'],
        'CONSERVAS_VERDURAS': ['conservas verduras', 'conservas de verduras'],
        'CONSERVAS_FRUTAS': ['conservas frutas', 'conservas de frutas'],
        
        # ESPECIAS Y CONDIMENTOS
        'SAL_FINA': ['sal fina', 'sal de mesa'],
        'SAL_GRUESA': ['sal gruesa'],
        'SAL_YODADA': ['sal yodada'],
        'SAL_HIMALAYA': ['sal himalaya', 'sal rosa himalaya', 'sal rosa del himalaya'],
        'PIMIENTA_NEGRA': ['pimenta negra', 'pimienta negra'],
        'OREGANO': ['oregano', 'orégano'],
        'PEREJIL': ['perejil'],
        'ALBAHACA': ['albahaca'],
        'ROMERO': ['romero'],
        'TOMILLO': ['tomillo'],
        'LAUREL': ['laurel', 'hoja laurel'],
        'PIMENTON_DULCE': ['pimenton dulce', 'pimentón dulce'],
        'AZAFRAN': ['azafran', 'azafrán'],
        
        # SALSAS Y CONDIMENTOS
        'SALSA_TOMATE': ['salsa tomate', 'salsa de tomate'],
        'MAYONESA': ['mayonesa'],
        'KETCHUP': ['ketchup'],
        'MOSTAZA': ['mostaza'],
        'VINAGRE_BALSAMICO': ['vinagre balsamico', 'vinagre balsámico'],
        'VINAGRE_VINO': ['vinagre vino', 'vinagre de vino'],
        'VINAGRE_MANZANA': ['vinagre manzana', 'vinagre de manzana'],
        
        # DULCES Y SNACKS
        'GALLETAS': ['galletas', 'galleta'],
        'CHOCOLATE_NEGRO': ['chocolate negro'],
        'CHOCOLATE_LECHE': ['chocolate leche', 'chocolate con leche'],
        'CHOCOLATE_BLANCO': ['chocolate blanco'],
        'CHUCHES': ['chuches', 'gominolas', 'caramelos'],
        
        # BEBIDAS CALIENTES
        'CAFE_MOLIDO': ['cafe molido', 'café molido'],
        'CAFE_CAPSULAS': ['cafe capsulas', 'café cápsulas'],
        'CAFE_INSTANTANEO': ['cafe instantaneo', 'café instantáneo'],
        'TE_NEGRO': ['te negro', 'té negro'],
        'TE_VERDE': ['te verde', 'té verde'],
        'TE_ROOIBOS': ['te rooibos', 'té rooibos'],
        'INFUSIONES': ['infusiones', 'infusión'],
        
        # INGREDIENTES BÁSICOS
        'AZUCAR': ['azucar', 'azúcar'],
        'HARINA_TRIGO': ['harina trigo', 'harina de trigo'],
        'HARINA_INTEGRAL': ['harina integral'],
        'LEVADURA': ['levadura'],
        'BICARBONATO': ['bicarbonato', 'bicarbonato sodio'],
        
        # PRODUCTOS ESPECIALES
        'GUACAMOLE': ['guacamole'],
        'HUMUS': ['hummus', 'humus'],
        'TZATZIKI': ['tzatziki'],
        'QUESO_FRESCO_GRECO': ['queso fresco griego', 'queso griego'],
        'YOGUR_GRIEGO_NATURAL': ['yogur griego natural', 'yogurt griego natural']
    }
    
    # Buscar coincidencias con prioridad jerárquica mejorada
    matches = []
    
    # Primera pasada: buscar coincidencias exactas y puntuarlas
    for type_name, keywords in product_types.items():
        for keyword in keywords:
            if keyword in name_lower:
                words_in_name = name_lower.split()
                words_in_keyword = keyword.split()
                
                # Calcular puntuación basada en especificidad
                score = 0
                
                # Puntuación base por coincidencia
                score += 1
                
                # Bonus por coincidencia exacta de todas las palabras
                if all(word in words_in_name for word in words_in_keyword):
                    score += 2
                
                # Bonus por longitud del keyword (más específico = más largo)
                score += len(words_in_keyword) * 0.5
                
                # Bonus por palabras específicas
                specific_words = ['fresco', 'fresca', 'entero', 'entera', 'virgen', 'extra', 'integral', 'natural']
                for word in words_in_keyword:
                    if word in specific_words:
                        score += 1
                
                matches.append((type_name, score, keyword))
    
    # Ordenar por puntuación (mayor puntuación = más específico)
    matches.sort(key=lambda x: x[1], reverse=True)
    
    # Devolver el tipo con mayor puntuación
    if matches:
        return matches[0][0]
    
    return 'OTROS'

def get_unit_description(unit):
    """Obtener descripción de la unidad"""
    unit_descriptions = {
        0: 'OTRAS',
        1: 'KG',
        2: 'L',
        3: 'M'
    }
    return unit_descriptions.get(unit, 'OTRAS')

def create_product_type_code(product_type, unit):
    """Crear código único para el tipo de producto"""
    unit_desc = get_unit_description(unit)
    return f"{product_type}_{unit_desc}"

def create_friendly_description(product_type, unit):
    """Crear descripción amigable para Power BI"""
    type_descriptions = {
        # LÁCTEOS - LECHE
        'LECHE_ENTERA': 'Leche Entera',
        'LECHE_SEMIDESNATADA': 'Leche Semidesnatada',
        'LECHE_DESNATADA': 'Leche Desnatada',
        'LECHE_CONDENSADA': 'Leche Condensada',
        'LECHE_EVAPORADA': 'Leche Evaporada',
        'LECHE_SIN_LACTOSA': 'Leche Sin Lactosa',
        
        # LÁCTEOS - YOGURES
        'YOGUR_NATURAL': 'Yogur Natural',
        'YOGUR_GRIEGO': 'Yogur Griego',
        'YOGUR_FRUTAS': 'Yogur de Frutas',
        'YOGUR_BEBIBLE': 'Yogur Bebible',
        'YOGUR_DESNATADO': 'Yogur Desnatado',
        
        # LÁCTEOS - QUESOS
        'QUESO_MANCHEGO': 'Queso Manchego',
        'QUESO_GOUDA': 'Queso Gouda',
        'QUESO_MOZZARELLA': 'Queso Mozzarella',
        'QUESO_EDAM': 'Queso Edam',
        'QUESO_HAVARTI': 'Queso Havarti',
        'QUESO_RALLADO': 'Queso Rallado',
        'QUESO_UNTAR': 'Queso de Untar',
        'QUESO_FRESCO': 'Queso Fresco',
        
        # LÁCTEOS - OTROS
        'MANTEQUILLA': 'Mantequilla',
        'NATA': 'Nata',
        'HUEVOS': 'Huevos',
        
        # ACEITES
        'ACEITE_OLIVA_VIRGEN_EXTRA': 'Aceite Oliva Virgen Extra',
        'ACEITE_OLIVA_VIRGEN': 'Aceite Oliva Virgen',
        'ACEITE_OLIVA_REFINADO': 'Aceite Oliva Refinado',
        'ACEITE_GIRASOL': 'Aceite de Girasol',
        'ACEITE_COCO': 'Aceite de Coco',
        'ACEITE_VEGETAL': 'Aceite Vegetal',
        
        # PAN Y BOLLERÍA
        'PAN_INTEGRAL': 'Pan Integral',
        'PAN_BLANCO': 'Pan Blanco',
        'PAN_RUSTICO': 'Pan Rústico',
        'BAGUETTE': 'Baguette',
        'PANECILLO': 'Panecillo',
        'PAN_LECHE': 'Pan de Leche',
        'DONUTS': 'Donuts',
        
        # ARROZ Y PASTA
        'ARROZ_REDONDO': 'Arroz Redondo',
        'ARROZ_LARGO': 'Arroz Largo',
        'ARROZ_BASMATI': 'Arroz Basmati',
        'ARROZ_INTEGRAL': 'Arroz Integral',
        'PASTA_ESPAGUETI': 'Espagueti',
        'PASTA_MACARRONES': 'Macarrones',
        'PASTA_FIDEOS': 'Fideos',
        'PASTA_LASAÑA': 'Lasaña',
        
        # BEBIDAS - AGUA Y REFRESCOS
        'AGUA_MINERAL': 'Agua Mineral',
        'COCA_COLA': 'Coca Cola',
        'FANTA': 'Fanta',
        'SPRITE': 'Sprite',
        'ZUMO_NARANJA': 'Zumo de Naranja',
        'ZUMO_MANZANA': 'Zumo de Manzana',
        'SMOOTHIE': 'Smoothie',
        
        # BEBIDAS ALCOHÓLICAS
        'CERVEZA_MAHOU': 'Cerveza Mahou',
        'CERVEZA_HEINEKEN': 'Cerveza Heineken',
        'CERVEZA_CORONA': 'Cerveza Corona',
        'CERVEZA': 'Cerveza',
        'VINO_TINTO': 'Vino Tinto',
        'VINO_BLANCO': 'Vino Blanco',
        'VINO_ROSADO': 'Vino Rosado',
        'WHISKY': 'Whisky',
        'RON': 'Ron',
        'GINEBRA': 'Ginebra',
        'VODKA': 'Vodka',
        
        # PESCADO FRESCO - MUY ESPECÍFICO
        'SALMON_FRESCO': 'Salmón Fresco',
        'MERLUZA_FRESCA': 'Merluza Fresca',
        'BACALAO_FRESCO': 'Bacalao Fresco',
        'DORADA_FRESCA': 'Dorada Fresca',
        'LUBINA_FRESCA': 'Lubina Fresca',
        'ATUN_FRESCO': 'Atún Fresco',
        'BOQUERONES_FRESCOS': 'Boquerones Frescos',
        'SARDINAS_FRESCAS': 'Sardinas Frescas',
        'PESCADO_FRESCO_GENERICO': 'Pescado Fresco',
        
        # PESCADO EN LATA/CONSERVA
        'ATUN_LATA': 'Atún en Lata',
        'SARDINAS_LATA': 'Sardinas en Lata',
        'ANCHOAS_LATA': 'Anchoas en Lata',
        'SALMON_LATA': 'Salmón en Lata',
        'MERLUZA_LATA': 'Merluza en Lata',
        
        # CARNE FRESCA - MUY ESPECÍFICO
        'POLLO_ENTERO': 'Pollo Entero',
        'MUSLO_POLLO': 'Muslo de Pollo',
        'PECHUGA_POLLO': 'Pechuga de Pollo',
        'ALAS_POLLO': 'Alas de Pollo',
        'LOMO_CERDO': 'Lomo de Cerdo',
        'SOLOMILLO_CERDO': 'Solomillo de Cerdo',
        'CHULETAS_CERDO': 'Chuletas de Cerdo',
        'BACON_CERDO': 'Bacon',
        'JAMON_CERDO': 'Jamón de Cerdo',
        'SOLOMILLO_TERNERA': 'Solomillo de Ternera',
        'CHULETAS_TERNERA': 'Chuletas de Ternera',
        'CORDERO_ENTERO': 'Cordero Entero',
        'CHULETAS_CORDERO': 'Chuletas de Cordero',
        'PAVO_ENTERO': 'Pavo Entero',
        'PECHUGA_PAVO': 'Pechuga de Pavo',
        'CARNE_FRESCA_GENERICA': 'Carne Fresca',
        
        # FRUTAS FRESCAS - MUY ESPECÍFICO
        'MANZANA_GOLDEN': 'Manzana Golden',
        'MANZANA_FUJI': 'Manzana Fuji',
        'MANZANA_GRANNY': 'Manzana Granny',
        'PLATANO_CANARIO': 'Plátano Canario',
        'PLATANO_ECUADOR': 'Plátano Ecuador',
        'NARANJA_MESA': 'Naranja de Mesa',
        'NARANJA_ZUMO': 'Naranja para Zumo',
        'PERA_CONFERENCIA': 'Pera Conferencia',
        'PERA_BLANQUILLA': 'Pera Blanquilla',
        'MELOCOTON_ROJO': 'Melocotón Rojo',
        'NECTARINA_AMARILLA': 'Nectarina Amarilla',
        'ALBARICOQUE': 'Albaricoque',
        'CEREZAS': 'Cerezas',
        'FRESAS': 'Fresas',
        'FRAMBUESAS': 'Frambuesas',
        'ARANDANOS': 'Arándanos',
        'UVA_BLANCA': 'Uva Blanca',
        'UVA_ROJA': 'Uva Roja',
        'SANDIA': 'Sandía',
        'MELON_CANTALOUP': 'Melón Cantaloup',
        'MELON_PIEL_SAPO': 'Melón Piel de Sapo',
        'MANGO': 'Mango',
        'AGUACATE': 'Aguacate',
        'LIMON': 'Limón',
        'LIMA': 'Lima',
        'PIÑA': 'Piña',
        'FRUTA_FRESCA_GENERICA': 'Fruta Fresca',
        
        # VERDURAS FRESCAS - MUY ESPECÍFICO
        'TOMATE_PERITA': 'Tomate Perita',
        'TOMATE_CHERRY': 'Tomate Cherry',
        'TOMATE_RAMA': 'Tomate Rama',
        'TOMATE_ENSALADA': 'Tomate Ensalada',
        'TOMATE_ROSA': 'Tomate Rosa',
        'TOMATE_NEGRO': 'Tomate Negro',
        'LECHUGA_ICEBERG': 'Lechuga Iceberg',
        'LECHUGA_COGOLLO': 'Lechuga Cogollo',
        'LECHUGA_ROMANA': 'Lechuga Romana',
        'PIMIENTO_ROJO': 'Pimiento Rojo',
        'PIMIENTO_VERDE': 'Pimiento Verde',
        'PIMIENTO_ITALIANO': 'Pimiento Italiano',
        'CEBOLLA_DULCE': 'Cebolla Dulce',
        'CEBOLLA_BLANCA': 'Cebolla Blanca',
        'ZANAHORIA': 'Zanahoria',
        'CALABACIN': 'Calabacín',
        'BERENJENA': 'Berenjena',
        'PEPINO': 'Pepino',
        'PATATA_LAVADA': 'Patata Lavada',
        'PATATA_NORMAL': 'Patata Normal',
        'ALCACHOFA': 'Alcachofa',
        'ESPINACAS': 'Espinacas',
        'VERDURA_FRESCA_GENERICA': 'Verdura Fresca',
        
        # PRODUCTOS DE LIMPIEZA
        'DETERGENTE_LAVADORA': 'Detergente Lavadora',
        'SUAVIZANTE': 'Suavizante',
        'DETERGENTE_LAVAJILLAS': 'Detergente Lavavajillas',
        'LIMPIEZA_SUELOS': 'Limpiador Suelos',
        'LIMPIEZA_BAÑO': 'Limpiador Baño',
        'LIMPIEZA_COCINA': 'Limpiador Cocina',
        'LEJIA': 'Lejía',
        'AMONIACO': 'Amoniaco',
        'BAYETAS': 'Bayetas',
        'ESTROPAJOS': 'Estropajos',
        
        # PAPEL Y HOGAR
        'PAPEL_HIGIENICO': 'Papel Higiénico',
        'BOLSAS_BASURA': 'Bolsas Basura',
        'PAPEL_COCINA': 'Papel Cocina',
        'FILM_TRANSPARENTE': 'Film Transparente',
        'ALUMINIO': 'Aluminio',
        
        # CONGELADOS
        'CONGELADOS_PESCADO': 'Congelados Pescado',
        'CONGELADOS_CARNE': 'Congelados Carne',
        'CONGELADOS_VERDURAS': 'Congelados Verduras',
        'CONGELADOS_FRUTAS': 'Congelados Frutas',
        'CONGELADOS_PIZZA': 'Congelados Pizza',
        
        # CONSERVAS
        'CONSERVAS_PESCADO': 'Conservas Pescado',
        'CONSERVAS_CARNE': 'Conservas Carne',
        'CONSERVAS_VERDURAS': 'Conservas Verduras',
        'CONSERVAS_FRUTAS': 'Conservas Frutas',
        
        # ESPECIAS Y CONDIMENTOS
        'SAL_FINA': 'Sal Fina',
        'SAL_GRUESA': 'Sal Gruesa',
        'SAL_YODADA': 'Sal Yodada',
        'SAL_HIMALAYA': 'Sal Himalaya',
        'PIMIENTA_NEGRA': 'Pimienta Negra',
        'OREGANO': 'Orégano',
        'PEREJIL': 'Perejil',
        'ALBAHACA': 'Albahaca',
        'ROMERO': 'Romero',
        'TOMILLO': 'Tomillo',
        'LAUREL': 'Laurel',
        'PIMENTON_DULCE': 'Pimentón Dulce',
        'AZAFRAN': 'Azafrán',
        
        # SALSAS Y CONDIMENTOS
        'SALSA_TOMATE': 'Salsa de Tomate',
        'MAYONESA': 'Mayonesa',
        'KETCHUP': 'Ketchup',
        'MOSTAZA': 'Mostaza',
        'VINAGRE_BALSAMICO': 'Vinagre Balsámico',
        'VINAGRE_VINO': 'Vinagre de Vino',
        'VINAGRE_MANZANA': 'Vinagre de Manzana',
        
        # DULCES Y SNACKS
        'GALLETAS': 'Galletas',
        'CHOCOLATE_NEGRO': 'Chocolate Negro',
        'CHOCOLATE_LECHE': 'Chocolate con Leche',
        'CHOCOLATE_BLANCO': 'Chocolate Blanco',
        'CHUCHES': 'Chuches',
        
        # BEBIDAS CALIENTES
        'CAFE_MOLIDO': 'Café Molido',
        'CAFE_CAPSULAS': 'Café Cápsulas',
        'CAFE_INSTANTANEO': 'Café Instantáneo',
        'TE_NEGRO': 'Té Negro',
        'TE_VERDE': 'Té Verde',
        'TE_ROOIBOS': 'Té Rooibos',
        'INFUSIONES': 'Infusiones',
        
        # INGREDIENTES BÁSICOS
        'AZUCAR': 'Azúcar',
        'HARINA_TRIGO': 'Harina de Trigo',
        'HARINA_INTEGRAL': 'Harina Integral',
        'LEVADURA': 'Levadura',
        'BICARBONATO': 'Bicarbonato',
        
        # PRODUCTOS ESPECIALES
        'GUACAMOLE': 'Guacamole',
        'HUMUS': 'Hummus',
        'TZATZIKI': 'Tzatziki',
        'QUESO_FRESCO_GRECO': 'Queso Fresco Griego',
        'YOGUR_GRIEGO_NATURAL': 'Yogur Griego Natural'
    }
    
    type_desc = type_descriptions.get(product_type, product_type.replace('_', ' ').title())
    unit_desc = get_unit_description(unit)
    
    return f"{type_desc} ({unit_desc})"

def create_product_types_dimension(df_products):
    """Crear la tabla de dimensiones DimProductTypes"""
    print("Creando tabla de dimensiones DimProductTypes...")
    
    # Extraer información para cada producto
    product_types_data = []
    
    for _, row in df_products.iterrows():
        product_type = extract_product_type_from_name(row['Name'])
        unit = row['Unit'] if pd.notna(row['Unit']) else 0
        
        product_type_code = create_product_type_code(product_type, unit)
        product_type_name = product_type
        unit_type = unit
        description = create_friendly_description(product_type, unit)
        
        product_types_data.append({
            'product_type_code': product_type_code,
            'product_type_name': product_type_name,
            'unit_type': unit_type,
            'description': description
        })
    
    # Crear DataFrame y eliminar duplicados
    df_product_types = pd.DataFrame(product_types_data)
    df_product_types = df_product_types.drop_duplicates().reset_index(drop=True)
    
    # Añadir ID secuencial
    df_product_types['ProductTypeID'] = range(1, len(df_product_types) + 1)
    
    # Reorganizar columnas
    df_product_types = df_product_types[['ProductTypeID', 'product_type_code', 'product_type_name', 'unit_type', 'description']]
    
    return df_product_types

def update_dim_products(df_products, df_product_types):
    """Actualizar DimProducts con el ProductTypeID"""
    print("Actualizando DimProducts con ProductTypeID...")
    
    # Crear mapeo de códigos a IDs
    code_to_id = dict(zip(df_product_types['product_type_code'], df_product_types['ProductTypeID']))
    
    # Añadir ProductTypeID a cada producto
    updated_products = []
    
    for _, row in df_products.iterrows():
        product_type = extract_product_type_from_name(row['Name'])
        unit = row['Unit'] if pd.notna(row['Unit']) else 0
        product_type_code = create_product_type_code(product_type, unit)
        
        product_type_id = code_to_id.get(product_type_code, None)
        
        updated_products.append({
            'ProductID': row['ProductID'],
            'Name': row['Name'],
            'Weight': row['Weight'],
            'Unit': row['Unit'],
            'ProductTypeID': product_type_id
        })
    
    return pd.DataFrame(updated_products)

def save_to_database(df_product_types, df_updated_products):
    """Guardar las tablas en la base de datos"""
    print("Guardando tablas en la base de datos...")
    
    try:
        # Guardar nueva tabla DimProductTypes
        df_product_types.to_sql('DimProductTypes', engine, if_exists='replace', index=False)
        print(" Tabla 'DimProductTypes' creada/actualizada")
        
        # Crear tabla temporal con los datos actualizados
        temp_table_name = 'DimProduct_Updated'
        df_updated_products.to_sql(temp_table_name, engine, if_exists='replace', index=False)
        print("Tabla temporal 'DimProduct_Updated' creada")
        
        return True
        
    except Exception as e:
        print(f"❌ Error al guardar en BD: {e}")
        
        # Guardar como CSV como respaldo
        df_product_types.to_csv('DimProductTypes.csv', index=False)
        df_updated_products.to_csv('DimProducts_Updated.csv', index=False)
        print("✅ Tablas guardadas como CSV")
        
        return False


def main():
    """Función principal"""

    
    # Cargar datos existentes
    df_products, df_categories, df_supermarkets = load_existing_data()
    
    if df_products is None:
        print("No se pudieron cargar los datos. Verifica la conexión a la base de datos.")
        return
    
    # Crear tabla de dimensiones
    df_product_types = create_product_types_dimension(df_products)
    
    # Actualizar DimProducts
    df_updated_products = update_dim_products(df_products, df_product_types)
    
    # Guardar en base de datos
    success = save_to_database(df_product_types, df_updated_products)
    

if __name__ == "__main__":
    main()
