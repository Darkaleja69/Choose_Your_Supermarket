import pandas as pd
import re
import pyodbc
from sqlalchemy import create_engine
import glob
import os

def read_csv_fix_cp1252(path, **kwargs):
    # 1) Lectura “lossless” con latin1
    df = pd.read_csv(path, encoding="latin1", dtype=str, keep_default_na=False, **kwargs)

    # 2) Mapa de controles latin1 -> glifos cp1252 (incluye €)
    cp1252_map = str.maketrans({
        '\x80':'€', '\x82':'‚', '\x83':'ƒ', '\x84':'„', '\x85':'…',
        '\x86':'†', '\x87':'‡', '\x88':'ˆ', '\x89':'‰', '\x8A':'Š',
        '\x8B':'‹', '\x8C':'Œ', '\x8E':'Ž',
        '\x91':'‘', '\x92':'’', '\x93':'“', '\x94':'”', '\x95':'•',
        '\x96':'–', '\x97':'—', '\x98':'˜', '\x99':'™', '\x9A':'š',
        '\x9B':'›', '\x9C':'œ', '\x9E':'ž', '\x9F':'Ÿ'
    })

    # aplica a todas las columnas string
    for col in df.columns:
        df[col] = df[col].str.translate(cp1252_map)

    return df


def concat_csv(carpeta_csv,patron):

    ruta_busqueda = os.path.join(carpeta_csv, patron)
    archivos = glob.glob(ruta_busqueda)
    if not archivos:
        raise FileNotFoundError(f"No se encontraron archivos con patrón {patron} en {carpeta_csv}")

    # Leer y concatenar todos los CSV
    dataframes = [pd.read_csv(archivo) for archivo in archivos]
    df_final = pd.concat(dataframes, ignore_index=True)

    return df_final
headers=["Product","Weight","Price","Unit_Price","Availability","Category","Extraction_Date"]
headers_mercadona=["Product","Weight","Price","Unit_Price","Category","Extraction_Date"]
headers_carrefour=["Product","Price","Unit_Price","Category","Offer","Availability","Extraction_Date"]
alcampo=pd.read_csv('/home/ale/Supermarket_Project/alcampo.csv')
mercadona=concat_csv('/home/ale/Supermarket_Project','mercadona*')
print(mercadona.shape)

carrefour = read_csv_fix_cp1252("/home/ale/Supermarket_Project/carrefour.csv", header=None)   # ajusta sep si hace falta
# ... tu limpieza ...
carrefour.to_csv("/home/ale/Supermarket_Project/carrefour_utf8.csv", index=False, encoding="utf-8")
carrefour=pd.read_csv('/home/ale/Supermarket_Project/carrefour_utf8.csv')
pd.set_option('display.max_columns', None)

server = 'localhost,1433'   # o la IP de tu contenedor si es externa
database = 'Supermarkets'
username = 'sa'
password = 'Aleja_23'

engine = create_engine(
    f"mssql+pyodbc://sa:{password}@localhost:1433/{database}?driver=ODBC+Driver+17+for+SQL+Server"
)

def extraer_peso_final(producto):
    producto=producto.replace('.','')
    # Busca todas las coincidencias con patrón tipo: número + unidad (como "500g", "1 kg", "2x400g", "1.5L")
    matches = re.findall(r'(\d[\d.,]*\s*(?:g|kg|cl|ml|cm|comprimidos|rollo|hojas|m|mg|metros|l|unidades|uds|ud|tabs|x\d+g|x\d+ml))', producto.lower())
    
    if matches:
        peso = matches[-1].strip()
        producto_limpio = re.sub(re.escape(peso), '', producto, flags=re.IGNORECASE).strip()
        return pd.Series([producto_limpio, peso])
    else:
        print(producto)
        return pd.Series([producto, None])
def es_float(valor):
    try:
        float(valor)
        return True
    except (ValueError, TypeError):
        return False

def limpiar_precio(p):
    print(p)
    p = p.replace('€', '').replace(',', '.').replace('Precio no disponible','nan')
    p = re.sub(r'[^\d\.\-]', '', p)  # Elimina todo excepto dígitos, punto y -
    return float(p) if p != '' else float('nan')

def limpiar_precio_unitario(p):
    print(p)
    return p.replace('€ por kilogramo', '€/kg').replace('€ por unidad', '€/ud').replace('€ por litro', '€/l').replace('€ Unidad', '€/ud').replace('€ por metro', '€/m').replace('€ por 100ml', '€/100ml').replace('€ por 100g', '€/100g').replace('€ por gramo', '€/g').replace('€ por ml', '€/ml').replace(',', '.')

def limpiar_peso(p):
    if p is not None:
        if '(' in p or ')' in p:
            x=p.index('(')
            y=p.index(')')
            p=p[x+1:y]
        if ' x ' in p:
            p=p[p.index('x')+1:]
        if p=='.':
            p='0'
        p=p.replace('Botella','').replace('Botellín','').replace('Lata','').replace('por envase','').replace('Garrafa','').replace('Spray','').replace('Bote','').replace('Paquete','').replace('Sobre','').replace('Tarro','').replace('Tarrina','').replace('Brick','').replace('escurrido','').replace('Caja','').replace('Bandeja','').replace('Vaso','').replace('Tableta','').replace('Tarrito','').replace('Tubo','').replace('Benjamín','').replace('Pieza','').replace('Bol','').replace('Frasco','').replace('Pastilla','').replace('pastillas','').replace('Malla','').replace('Saco','').replace('recambios','').replace('hojas','').replace('servicios','').replace('cajas','').replace('Manojo','').replace('monodosis','').replace('velas','').replace('tiras','').replace('rollos','').replace('bandas','').replace('sobres','').replace('aprox.','').replace('bolsas','').replace('rollo','').replace('Granel','').replace('ud.','').replace('1/2','').replace(',','.')
        if p.endswith(' '):
            p=p[:-1]
        p=p.strip()
        return p
    else:
        return None

def normalizar_precio_unitario(valor):
    """
    It converts prices to €/kg o €/l unit based.
    """
    try:
        if pd.isna(valor):
            return None

        valor = valor.replace(" ", "").lower()

        if "/100ml" in valor:
            precio = float(valor.replace("€/100ml", ""))
            return precio * 10

        elif "/ml" in valor:
            precio = float(valor.replace("€/ml", ""))
            return precio * 1000

        elif "/l" in valor:
            return float(valor.replace("€/l", ""))

        elif "/kg" in valor:
            return float(valor.replace("€/kg", ""))

        elif "/100g" in valor:
            precio = float(valor.replace("€/100g", ""))
            return precio * 10

        elif "/g" in valor:
            precio = float(valor.replace("€/g", ""))
            return precio * 1000

        elif "/m" in valor:
            return float(valor.replace("€/m", ""))
        
        elif "/ud" in valor:
            return float(valor.replace("€/ud", ""))

        elif es_float(valor):
            return valor
        else:
            return None  # Unknown unit

    except Exception as e:
        return None

def multiplicar_si_hay_x(peso_str):
    if not isinstance(peso_str, str):
        return None

    
    peso_str = peso_str.lower().replace(" ", "")

    # It searches for 3x80, 2x125, etc.
    match = re.match(r'(\d+(?:[\.,]?\d*)?)x(\d+(?:[\.,]?\d*)?)', peso_str)
    if match:
        a = float(match.group(1).replace(',', '.'))
        b = float(match.group(2).replace(',', '.'))
        return str(a * b)

    return peso_str

def normalizar_peso(valor):
    
    if valor is None:
        return None
    else:
        if valor.endswith('.'):
            valor=valor[:-1]
        valor=valor.lower()
        if valor.endswith('kg'):
            valor=valor.replace('kg','').strip()
            if len(valor.split(' '))>1:
                valor=valor.split(' ')
                valor=valor[2]
            return float(multiplicar_si_hay_x(valor))
        elif valor.endswith('uds'):
            return float(multiplicar_si_hay_x(valor).replace('uds',''))
        elif valor.endswith('ud'):
            return float(multiplicar_si_hay_x(valor).replace('ud',''))
        elif valor.endswith('unidades'):
            return float(multiplicar_si_hay_x(valor).replace('unidades',''))
        elif valor.endswith('comprimidos'):
            return float(multiplicar_si_hay_x(valor).replace('comprimidos',''))
        elif valor.endswith('g'):
            return float((multiplicar_si_hay_x(valor).replace('g','').replace(' ','')))/1000
        elif valor.endswith('L'):
            return float(multiplicar_si_hay_x(valor).replace('L',''))
        elif valor.endswith('ml'):
            return float((multiplicar_si_hay_x(valor).replace('ml','')))/1000
        elif valor.endswith('cl'):
            return float((multiplicar_si_hay_x(valor).replace('cl','')))/100
        elif valor.endswith('l'):
            return float(multiplicar_si_hay_x(valor).replace('l',''))
        elif valor.endswith('cm'):
            return float((multiplicar_si_hay_x(valor).replace('cm','')))/100
        elif valor.endswith('m'):
            return float(multiplicar_si_hay_x(valor).replace('m',''))
        elif '(' in valor or ')' in valor:
            return float(valor[valor.index('(')+1:valor.index(')')])
        else:
            try:
                return float(valor)
            except Exception as e:
                print(f"Error con el valor: {valor} - {e}")
                return '.'
def colu_unidades(p):
    if p is None:
        return None
    if p.endswith('g'):
        return 1
    elif p.endswith('l'):
        return 2
    elif p.endswith('m'):
        return 3
    else:
        return 0

def disponibilidad(d):
    if d.lower()=='disponible':
        return 0
    else:
        return 1
###ALCAMPO
def extract_transform_alcampo(df):
    df.columns=headers
    print(df.count())
    df.dropna(inplace=True)
    df.drop_duplicates(subset=["Product","Weight","Price","Unit_Price","Availability","Category"],inplace=True)
    print(df.count())
    df['Price'] = df['Price'].apply(limpiar_precio)
    df['Unit_Price'] = df['Unit_Price'].apply(limpiar_precio_unitario)
    df['Unit_Price'] = df['Unit_Price'].apply(normalizar_precio_unitario)
    df['Parent_Category']=df['Category'].str.split('>').str[0]
    df['Category']=df['Category'].str.split('>').str[1]
    df['Unit']=df['Weight'].apply(colu_unidades)
    print(df['Availability'].value_counts())
    df['Availability']=df['Availability'].apply(disponibilidad)
    df['Weight']=df['Weight'].apply(limpiar_peso)
    df['Weight']=df['Weight'].apply(normalizar_peso)
    df_restantes_str = df[df['Weight'].apply(lambda x: isinstance(x, str))]
    print(df_restantes_str)
    print(df.count())
    df=df.drop_duplicates(subset=['Product','Weight','Price','Unit_Price','Availability','Category','Parent_Category','Unit'])
    print(df.count())
    filtered_df = df[~df['Weight'].apply(lambda x: isinstance(x, str)) & df['Weight'].notna()]
    return filtered_df

###MERCADONA
def extract_transform_mercadona(df):
    df.columns=headers_mercadona
    print(df.count())
    df.dropna(inplace=True)
    df.drop_duplicates(inplace=True)
    print(df.count())
    print(df)
    df['Price'] = df['Price'].apply(limpiar_precio)
    df['Unit_Price'] = df['Unit_Price'].apply(limpiar_precio_unitario)
    
    df['Unit_Price'] = df['Unit_Price'].apply(normalizar_precio_unitario)
    
    df['Parent_Category']=df['Category'].str.split('-').str[0]
    df['Category']=df['Category'].str.split('-').str[1]
    df['Availability']=0
    df['Weight']=df['Weight'].apply(limpiar_peso)
    df['Unit']=df['Weight'].apply(colu_unidades)
    df['Weight']=df['Weight'].apply(normalizar_peso)
    print(df)
    return df

###CARREFOUR
def extract_transform_carrefour(df):
    df.columns=headers_carrefour
    df.dropna(inplace=True)
    df.drop_duplicates(inplace=True)
    df[['Product', 'Weight']] = df['Product'].apply(extraer_peso_final)
    df['Price'] = df['Price'].apply(limpiar_precio)
    df['Unit_Price'] = df['Unit_Price'].apply(limpiar_precio_unitario)
    
    df['Unit_Price'] = df['Unit_Price'].apply(normalizar_precio_unitario)
    df['Availability']=df['Availability'].apply(disponibilidad)
    df['Weight']=df['Weight'].apply(limpiar_peso)
    df['Unit']=df['Weight'].apply(colu_unidades)

    df['Weight']=df['Weight'].apply(normalizar_peso)
    print(df)
    return df

#df_alcampo=extract_transform_alcampo(alcampo)
#df_mercadona=extract_transform_mercadona(mercadona)
df_carrefour=extract_transform_carrefour(carrefour)

#df_alcampo.to_sql('stg_Alcampo', con=engine, if_exists='replace', index=False)
#df_mercadona.to_sql('stg_Mercadona', con=engine, if_exists='replace', index=False)
df_carrefour.to_sql('stg_Carrefour', con=engine, if_exists='replace', index=False)