import pandas as pd
import matplotlib.pyplot as plt
import sqlite3
import numpy as np
import seaborn as sns

# ==============================
# CONFIGURACION VISUAL
# ==============================
sns.set_theme(style='whitegrid')
plt.rcParams['figure.figsize'] = (8, 5)

# ==============================
# PREGUNTAS DE NEGOCIO
# ==============================
# 1. ¿Qué hace que una pelicula gane dinero?
# 2. ¿Qué géneros combinan alto ingreso promedio y buen rating?
# 3. ¿Los géneros que más producen son también los más rentables?
# 4. ¿Qué combinación de duración, rating y género aparece más en películas exitosas?
# 5. ¿Qué factores explican mejor la cantidad de votos?
# 6. ¿Qué actores o directores aparecen de forma consistente en películas exitosas (no solo una vez)?
# 7. ¿Cómo evolucionaron los ingresos, ratings y cantidad de películas a lo largo del tiempo?

# ==============================
# CARGA DE DATOS
# ==============================
df = pd.read_csv("imdb_top_1000.csv")

# ==============================
# COMPROBACIONES RAPIDAS
# ==============================
print(df.shape)
print(df.info())
print(df.describe())
print(df.isna().sum())
print(df.duplicated().sum())
print(df.dtypes)

# ==============================
# LIMPIEZA DE DATOS
# ==============================
clean_data = df.copy()
clean_data[['Series_Title', 'Certificate', 
    'Genre', 'Overview',
    'Director', 'Star1', 'Star2', 
    'Star3', 'Star4']] = clean_data[['Series_Title', 'Certificate', 'Genre', 'Overview', 
                            'Director', 'Star1', 'Star2', 'Star3', 'Star4']].astype(str)

clean_data["Released_Year"] = pd.to_numeric(clean_data["Released_Year"], errors="coerce")
# Eliminar todas las filas donde Released_Year es NaN
print("Columnas NAN", clean_data["Released_Year"].isna().sum())
clean_data = clean_data.dropna(subset=["Released_Year"])
clean_data["Released_Year"] = clean_data["Released_Year"].astype(int)

clean_data["Meta_score"] = pd.to_numeric(clean_data["Meta_score"], errors="coerce")
clean_data["Meta_score"] = clean_data["Meta_score"].fillna(clean_data["Meta_score"].median())
clean_data["Meta_score"] = clean_data["Meta_score"].astype(int)

clean_data["Runtime"] = clean_data["Runtime"].str.replace(' min','')
clean_data["Runtime"] = pd.to_numeric(clean_data["Runtime"], errors="coerce")

clean_data["Gross"] = clean_data["Gross"].str.replace(",", "")
clean_data["Gross"] = pd.to_numeric(clean_data["Gross"], errors="coerce")
clean_data["Gross"] = clean_data["Gross"].replace(0, np.nan)

clean_data["No_of_Votes"] = pd.to_numeric(clean_data["No_of_Votes"], errors="coerce")

clean_data["Rating_Bucket"] = pd.cut(
    clean_data["IMDB_Rating"],
    bins=[0,7,8,9,10],
    labels=["<7", "7-8", "8-9", "9-10"]
)

clean_data["Runtime_Bucket"] = pd.cut(
    clean_data["Runtime"],
    bins=[0, 90, 120, 150, 300],
    labels=["Short", "Medium", "Long", "Very Long"]
)

# ==============================
# NORMALIZACIÓN DE GENEROS
# ==============================
clean_data_genre = clean_data.copy()
clean_data_genre["Genre"] = clean_data_genre["Genre"].str.split(", ")
clean_data_genre = clean_data_genre.explode("Genre")

# ==============================
# GUARDAR EN BAASE DE DATOS (SQL)
# ==============================
conn = sqlite3.connect("IMDb.db")
clean_data.to_sql("imdb_top", conn, if_exists="replace", index=False)
clean_data_genre.to_sql("IMDb_genre_dashboard", conn, if_exists="replace", index=False)

# ==============================
# ANÁLISIS EXPLORATORIO
# ==============================
votes_movie  = pd.read_sql_query("""
    SELECT 
        CASE 
            WHEN No_of_votes < 100000 THEN 'Low'
            WHEN No_of_votes BETWEEN 100000 AND 500000 THEN 'Medium'
            ELSE 'High'
        END AS votes_level,
        AVG(Gross) AS avg_gross
    FROM imdb_top
    GROUP BY votes_level;                                                                 
""", conn) 

rating_movie  = pd.read_sql_query("""
    SELECT 
        CASE
            WHEN IMDB_Rating < 7 THEN '<7'
            WHEN IMDB_Rating >= 7 AND IMDB_Rating < 8 THEN '7-8'
            WHEN IMDB_Rating >= 8 AND IMDB_Rating < 9 THEN '8-9'
            ELSE '9-10'
        END AS rating_level,
        AVG(Gross) AS avg_gross
    FROM imdb_top 
    GROUP BY rating_level;                                                             
""", conn) 

genre_movie  = pd.read_sql_query("""
    SELECT Genre, COUNT(DISTINCT Series_Title) AS quantity, 
        AVG(Gross) AS avg_gross
    FROM IMDb_genre_dashboard 
    WHERE Gross IS NOT NULL
    GROUP BY Genre
    HAVING quantity >= 30
    ORDER BY avg_gross DESC;	                                                            
""", conn) 

gross_high_and_rating_high  = pd.read_sql_query("""
    SELECT Genre, COUNT(DISTINCT Series_Title) AS quantity, 
        AVG(Gross) AS avg_gross, AVG(IMDB_Rating) AS avg_rating 
    FROM IMDb_genre_dashboard 
    GROUP BY Genre
    HAVING quantity >= 30
    ORDER BY avg_gross DESC, avg_rating  DESC;                                                            
""", conn) 

genre_gross  = pd.read_sql_query("""
    SELECT Genre, COUNT(DISTINCT Series_Title) AS quantity_per_genre, 
        AVG(Gross) AS avg_gross
    FROM IMDb_genre_dashboard
    GROUP BY Genre
    HAVING COUNT(DISTINCT Series_Title) >= 30
    ORDER BY quantity_per_genre DESC, avg_gross DESC                                                   
""", conn) 

runtime_rating_genre  = pd.read_sql_query("""
    SELECT 
        Genre,
        COUNT(DISTINCT Series_Title) AS quantity,
        AVG(Runtime) AS avg_runtime, 
        AVG(IMDB_Rating) AS avg_rating, 
        AVG(Gross) AS avg_gross
    FROM IMDb_genre_dashboard
    GROUP BY Genre
    HAVING COUNT(DISTINCT Series_Title) >= 30
    ORDER BY avg_gross DESC;                                                     
""", conn) 

rating_votes  = pd.read_sql_query("""
    SELECT 
	CASE 
		WHEN IMDB_Rating < 7 THEN "<7"
		WHEN IMDB_Rating BETWEEN 7 AND 8 THEN "7-8"
		WHEN IMDB_Rating BETWEEN 8 AND 9 THEN "8-9"
		ELSE "9-10"
	END AS rating_level,
	AVG(No_of_Votes) AS avg_votes
    FROM imdb_top 
    GROUP BY rating_level 
    ORDER BY avg_votes  DESC                                                   
""", conn) 

actores  = pd.read_sql_query("""
    SELECT Actor, COUNT(*) AS quantity, AVG(IMDB_Rating) AS avg_rating, AVG(Gross) AS avg_gross
    FROM (
        SELECT Star1 AS Actor, IMDB_Rating, Gross  
        FROM imdb_top
        UNION ALL
        SELECT Star2, IMDB_Rating, Gross 
        FROM imdb_top
        UNION ALL
        SELECT Star3, IMDB_Rating, Gross 
        FROM imdb_top 
        UNION ALL
        SELECT Star4, IMDB_Rating, Gross 
        FROM imdb_top
    )
    GROUP BY Actor
    HAVING COUNT(*) >= 10
    ORDER BY avg_gross DESC
    LIMIT 10                                               
""", conn) 

evolution  = pd.read_sql_query("""
    SELECT 
        Released_Year,
        COUNT(Series_Title) AS quantity,
        AVG(IMDB_Rating) AS avg_rating,
        AVG(Gross) AS avg_gross
    FROM imdb_top
    GROUP BY Released_Year
    ORDER BY Released_Year;                                            
""", conn) 

conn.close()

# ==============================
# VISUALIZACION
# ==============================
top_genres = genre_movie.sort_values(by='avg_gross', ascending=False).head(10)
plt.figure(figsize=(10, 6))
sns.barplot(
    data=top_genres,
    x='avg_gross',
    y='Genre',
    palette='viridis'
)
plt.title("Top 10 generos por ingresos promedio ($)")
plt.xlabel("Ingresos promedio")
plt.ylabel("Genero")
plt.savefig("images/Top_generos_por_ingresos.png")
plt.show()

plt.figure(figsize=(12, 6))
evolution = clean_data.groupby('Released_Year').agg({
    'Gross': 'mean'
}).reset_index()

sns.lineplot(
    data=evolution[evolution['Released_Year'] > 1950],
    x='Released_Year',
    y='Gross'
)
plt.title('Evolución de Ingresos Promedio (1950 - Presente)')
plt.xlabel('Año de Estreno')
plt.ylabel('Ingresos Promedio')
plt.savefig("images/Evolution.png")
plt.show()

plt.figure(figsize=(8, 6))

sns.heatmap(
    clean_data[['IMDB_Rating','Gross','No_of_Votes']].corr(),
    annot=True,
    cmap='coolwarm',
    fmt=".2f",
    linewidths=0.5
)
plt.title("Correlacion: Rating, Votos e Ingreso")
plt.tight_layout()
plt.savefig("images/Correlación.png")
plt.show()

# ==============================
# EXPORTACIÓN
# ==============================
clean_data.to_csv("IMDb_dashboard.csv", index=False)
clean_data_genre.to_csv("IMDb_genre_dashboard.csv", index=False)
