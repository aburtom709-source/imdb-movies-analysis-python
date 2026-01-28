import pandas as pd
import matplotlib.pyplot as plt

# Load data
data = pd.read_csv("imdb_top_1000.csv")

# --- Data exploration (used during development) ---
# data.info()
# data.describe()
# data.columns
# data.dtypes

# --- Basic cleaning and type fixes ---
data = data.dropna().drop_duplicates()

# --- Covert data types ---
cols_to_str = [
    'Series_Title', 'Certificate', 'Genre', 'Overview', 
    'Director', 'Star1', 'Star2', 'Star3', 'Star4'
]
data[cols_to_str] = data[cols_to_str].astype(str)

# Released year
data['Released_Year'] = pd.to_numeric(data['Released_Year'], errors='coerce')
data['Released_Year'] = data['Released_Year'].astype(int)

# Runtime (remove ' min')
data['Runtime'] = data['Runtime'].str.replace(' min', '').astype(int)

# Meta score
data['Meta_score'] = pd.to_numeric(data['Meta_score'], errors='coerce').astype(int)

# Gross (remove commas and convert to int)
data['Gross'] = data['Gross'].str.replace(",", "").astype(int)

# Analysis data

## Averages
average_runtime = data['Runtime'].mean()
average_rating = data['IMDB_Rating'].mean()

## Number of movies per year
movies_per_year = data.groupby('Released_Year')['Series_Title'].count()

## Top 10 highest rated movies
top_rated_movies = data.sort_values(by='IMDB_Rating', ascending=False)
rated_movies = data[['Series_Title', 'IMDB_Rating']].head(10)

## Top 10 highest grossing movies
top_gross_movies = data.sort_values(by='Gross', ascending=False)
gross_movies = data[['Series_Title', 'Gross']].head(10)

## Genre with highest average rating
best_rated_genre = data.groupby('Genre')['IMDB_Rating'].mean().idxmax()

## Genre with highest average gross
best_profitable_genre = data.groupby('Genre')['Gross'].mean().idxmax()

## Correlation between rating and gross
rating_gross_correlation = data['IMDB_Rating'].corr(data['Gross'])

## Reshape actors 
actors = data.melt(
    id_vars=['IMDB_Rating'],
    value_vars=['Star1', 'Star2', 'Star3', 'Star4'],
    value_name='Actor'
)

## Average rating per actor
top_actors_by_rating = actors.groupby('Actor')['IMDB_Rating'].mean().sort_values(ascending=False).head(10)

# Visualizations

## Average rating per genre (Top 5)
average_rated_genre = data.groupby('Genre')['IMDB_Rating'].mean().sort_values(ascending=False).head(5)

## X and Y
genres = average_rated_genre.index
ratings = average_rated_genre.values

## Bar chart
plt.bar(genres, ratings)
plt.xticks(rotation=45)
plt.ylabel("Average IMDb Rating")
plt.xlabel("Genre")
plt.title("Top 5 Genres by Average Rating")
plt.show()

## Average grossing per genre (Top 5)
average_gross_genre = data.groupby('Genre')['Gross'].mean().sort_values(ascending=False).head(5)

## X and Y
genres_per_gross = average_gross_genre.index
gross = average_gross_genre.values

## Bar chart
plt.bar(genres_per_gross, gross)
plt.ylabel("Average Gross Revenue")
plt.xlabel("Genre")
plt.title("Top 5 Genres by Average Gross Revenue")
plt.show()

## Relationship between rating and revenue
plt.scatter(data['IMDB_Rating'], data['Gross'])
plt.ylabel("IMDb Rating")
plt.xlabel("Gross Revenue")
plt.title("IMDb Rating vs Gross Revenue")
plt.show()

## Number of movies per year
movies_per_year = data.groupby('Released_Year')['Series_Title'].count()

## X and Y
year = movies_per_year.index
movies_title = movies_per_year.values

## Line
plt.plot(year, movies_title)
plt.ylabel("Number of Movies")
plt.xlabel("Year")
plt.title("Movies Released per Year")
plt.show()