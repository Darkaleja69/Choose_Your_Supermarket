# 🛒 Nueva Dimensión DimProductTypes para tu Modelo Existente

Este script crea una **nueva dimensión DimProductTypes** que se integra perfectamente con tu modelo actual, permitiendo agrupar productos similares para facilitar comparaciones en Power BI.

## 🎯 **¿Qué hace este script?**

- **Lee tu modelo existente**: DimProducts, DimCategories, DimSupermarkets
- **Crea nueva dimensión**: DimProductTypes con tipos de productos normalizados
- **Actualiza DimProducts**: Añade ProductTypeID para relacionar productos similares
- **Mantiene integridad**: No rompe tu modelo actual ni las relaciones existentes

## 📊 **Tu Modelo Actual vs. Nuevo**

### **Antes:**
```
DimProducts (ProductID, Name, Weight, Unit, ...)
DimCategories (CategoryID, CategoryName, ...)
DimSupermarkets (SupermarketID, SupermarketName, ...)
FactPrices (ProductID, CategoryID, SupermarketID, Price, Date, ...)
```

### **Después:**
```
DimProducts (ProductID, Name, Weight, Unit, ProductTypeID, ...) ← NUEVA COLUMNA
DimProductTypes (ProductTypeID, product_type_code, product_type_name, unit_type, description) ← NUEVA TABLA
DimCategories (CategoryID, CategoryName, ...)
DimSupermarkets (SupermarketID, SupermarketName, ...)
FactPrices (ProductID, CategoryID, SupermarketID, Price, Date, ...)
```

## 🚀 **Cómo Usar**

### **1. Ejecutar el Script**
```bash
python Create_Product_Types_Dimension.py
```

### **2. Seguir los Pasos SQL**
El script te proporcionará el SQL necesario para:
- Añadir la columna ProductTypeID a DimProducts
- Actualizar los ProductTypeID
- Crear la relación entre tablas

### **3. Usar en Power BI**
- Conectar a DimProductTypes
- Crear relación: DimProducts[ProductTypeID] → DimProductTypes[ProductTypeID]
- Usar para agrupar productos similares

## 📋 **Ejemplos de Agrupamiento**

### **Leches Enteras (sin considerar peso específico):**
```
"Leche Entera Hacendado 1L" (Weight=1.0, Unit=2) → ProductTypeID: 1
"Leche Entera Carrefour 1L" (Weight=1.0, Unit=2) → ProductTypeID: 1
"Leche Entera Alcampo 500ml" (Weight=0.5, Unit=2) → ProductTypeID: 1
```

### **Yogures Naturales:**
```
"Yogur Natural Danone 125g" (Weight=0.125, Unit=1) → ProductTypeID: 2
"Yogur Natural Hacendado 125g" (Weight=0.125, Unit=1) → ProductTypeID: 2
"Yogur Natural Carrefour 170g" (Weight=0.170, Unit=1) → ProductTypeID: 2
```

## 🏷️ **Tipos de Productos Reconocidos**

### **Lácteos**
- `LECHE_ENTERA` - Leche entera (L)
- `LECHE_SEMIDESNATADA` - Leche semidesnatada (L)
- `LECHE_DESNATADA` - Leche desnatada (L)
- `YOGUR_NATURAL` - Yogur natural (KG)
- `YOGUR_GRIEGO` - Yogur griego (KG)
- `YOGUR_FRUTAS` - Yogur de frutas (KG)

### **Aceites y Condimentos**
- `ACEITE_OLIVA` - Aceite de oliva (L)
- `ACEITE_GIRASOL` - Aceite de girasol (L)
- `ACEITE_VEGETAL` - Aceite vegetal (L)

### **Pan y Cereales**
- `PAN_INTEGRAL` - Pan integral (KG)
- `PAN_BLANCO` - Pan blanco (KG)
- `ARROZ_REDONDO` - Arroz redondo (KG)
- `ARROZ_LARGO` - Arroz largo (KG)

### **Pasta**
- `PASTA_ESPAGUETI` - Espagueti (KG)
- `PASTA_MACARRONES` - Macarrones (KG)

### **Bebidas**
- `AGUA_MINERAL` - Agua mineral (L)
- `COCA_COLA` - Coca Cola (L)
- `CERVEZA` - Cerveza (L)
- `VINO_TINTO` - Vino tinto (L)
- `VINO_BLANCO` - Vino blanco (L)

### **Y muchos más...**
El script reconoce más de 50 tipos de productos diferentes.

## 💡 **Uso en Power BI**

### **Comparar Precios por Tipo**
```dax
-- Precio promedio de leche entera por supermercado
Precio Leche Entera = 
CALCULATE(
    AVERAGE(FactPrices[Price]),
    DimProductTypes[product_type_name] = "LECHE_ENTERA"
)
```

### **Análisis por Unidad**
```dax
-- Precio por litro de leche entera
Precio por Litro = 
DIVIDE(
    CALCULATE(SUM(FactPrices[Price]), DimProductTypes[product_type_name] = "LECHE_ENTERA"),
    CALCULATE(SUM(DimProducts[Weight]), DimProductTypes[product_type_name] = "LECHE_ENTERA")
)
```

### **Visualizaciones Recomendadas**
1. **Gráfico de barras**: Eje X = DimProductTypes[description], Eje Y = Precio promedio
2. **Tabla de comparación**: Filas = Tipo de producto, Columnas = Supermercado
3. **Segmentación**: Por tipo de producto para filtrar análisis

## 🔍 **Consultas SQL de Ejemplo**

### **Comparar Precios de Leche Entera**
```sql
SELECT 
    dpt.description,
    ds.SupermarketName,
    AVG(fp.Price) as precio_promedio
FROM DimProductTypes dpt
JOIN DimProducts dp ON dpt.ProductTypeID = dp.ProductTypeID
JOIN FactPrices fp ON dp.ProductID = fp.ProductID
JOIN DimSupermarkets ds ON fp.SupermarketID = ds.SupermarketID
WHERE dpt.product_type_name = 'LECHE_ENTERA'
GROUP BY dpt.description, ds.SupermarketName
ORDER BY dpt.description, precio_promedio
```

### **Top 10 Tipos Más Baratos**
```sql
SELECT TOP 10
    dpt.description,
    AVG(fp.Price) as precio_promedio
FROM DimProductTypes dpt
JOIN DimProducts dp ON dpt.ProductTypeID = dp.ProductTypeID
JOIN FactPrices fp ON dp.ProductID = fp.ProductID
GROUP BY dpt.description
ORDER BY precio_promedio ASC
```

## 📈 **Ventajas de esta Solución**

### **✅ Mantiene tu Modelo Actual**
- No rompe relaciones existentes
- No afecta FactPrices
- Compatible con tu estructura actual

### **✅ Agrupa Productos Similares**
- Independiente del peso específico
- Usa información estructurada (Weight + Unit)
- Normaliza nombres de productos

### **✅ Fácil de Usar en Power BI**
- Dimensiones optimizadas para BI
- Relaciones claras y simples
- Consultas eficientes

### **✅ Escalable**
- Fácil de mantener
- Fácil de actualizar
- Fácil de extender

## 🔧 **Configuración Avanzada**

### **Añadir Nuevos Tipos de Productos**
Edita la función `extract_product_type_from_name()` en el script:
```python
product_types = {
    'NUEVO_TIPO': ['palabra clave 1', 'palabra clave 2'],
    # ... más tipos
}
```

### **Personalizar Descripciones**
Edita la función `create_friendly_description()`:
```python
type_descriptions = {
    'NUEVO_TIPO': 'Descripción Amigable',
    # ... más descripciones
}
```

## 🚀 **Próximos Pasos**

### **1. Ejecutar el Script**
```bash
python Create_Product_Types_Dimension.py
```

### **2. Ejecutar SQL en tu Base de Datos**
```sql
-- Añadir columna
ALTER TABLE DimProducts ADD ProductTypeID INT;

-- Actualizar datos
UPDATE DimProducts 
SET ProductTypeID = temp.ProductTypeID
FROM DimProducts dp
INNER JOIN DimProducts_Updated temp ON dp.ProductID = temp.ProductID;

-- Crear relación
ALTER TABLE DimProducts 
ADD CONSTRAINT FK_DimProducts_DimProductTypes 
FOREIGN KEY (ProductTypeID) REFERENCES DimProductTypes(ProductTypeID);
```

### **3. Configurar Power BI**
1. Conectar a DimProductTypes
2. Crear relación con DimProducts
3. Crear visualizaciones usando la nueva dimensión

### **4. Crear Dashboard**
- Comparación de precios por tipo de producto
- Análisis por supermercado
- Identificación de productos más baratos

## 📞 **Soporte**

### **Problemas Comunes**
1. **Error de conexión**: Verificar credenciales de base de datos
2. **Productos no agrupados**: Revisar palabras clave en el script
3. **Relaciones no funcionan**: Verificar que ProductTypeID coincida

### **Optimización**
1. **Rendimiento**: Crear índices en ProductTypeID
2. **Memoria**: Usar columnas calculadas en Power BI
3. **Actualización**: Programar refrescos automáticos

---

**¡Con esta nueva dimensión podrás comparar precios de productos similares de manera eficiente en Power BI!** 📊
