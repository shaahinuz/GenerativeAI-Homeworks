"""
Generate sample films database with 500+ movie records
"""

import sqlite3
import random
from datetime import datetime, timedelta

# Sample data
MOVIE_TITLES = [
    "The Last Journey", "Midnight Dreams", "City Lights", "Ocean's Call",
    "Silent Echo", "Rising Storm", "Dark Waters", "Golden Hour",
    "Broken Wings", "Eternal Summer", "Lost Paradise", "Winter's End",
    "Secret Garden", "Forgotten Path", "Distant Stars", "Hidden Truth",
    "Wild Hearts", "Crimson Sky", "Silver Moon", "Diamond City",
    "Iron Will", "Velvet Night", "Crystal Dawn", "Shadow Dance",
    "Thunder Road", "Whisper Wind", "Frozen Fire", "Desert Rose",
    "Mountain Peak", "River Song", "Forest Deep", "Valley Low",
    "Sunrise Bay", "Sunset Hill", "Starlight Avenue", "Moonbeam Street",
    "Rainbow Bridge", "Cloud Nine", "Storm Warning", "Calm Waters"
]

DIRECTORS = [
    "Christopher Nolan", "Martin Scorsese", "Quentin Tarantino", "Steven Spielberg",
    "James Cameron", "Ridley Scott", "Peter Jackson", "Denis Villeneuve",
    "Greta Gerwig", "Wes Anderson", "Bong Joon-ho", "Guillermo del Toro",
    "Sofia Coppola", "Kathryn Bigelow", "Ava DuVernay", "Jordan Peele",
    "David Fincher", "Spike Lee", "Coen Brothers", "Paul Thomas Anderson"
]

ACTORS = [
    "Tom Hanks", "Meryl Streep", "Leonardo DiCaprio", "Cate Blanchett",
    "Denzel Washington", "Frances McDormand", "Robert De Niro", "Viola Davis",
    "Brad Pitt", "Emma Stone", "Morgan Freeman", "Natalie Portman",
    "Christian Bale", "Scarlett Johansson", "Daniel Day-Lewis", "Jennifer Lawrence",
    "Al Pacino", "Kate Winslet", "Anthony Hopkins", "Charlize Theron",
    "Will Smith", "Nicole Kidman", "Matt Damon", "Julia Roberts",
    "Johnny Depp", "Sandra Bullock", "Tom Cruise", "Angelina Jolie",
    "George Clooney", "Reese Witherspoon", "Ryan Gosling", "Amy Adams",
    "Chris Hemsworth", "Lupita Nyong'o", "Idris Elba", "Tilda Swinton",
    "Michael B. Jordan", "Saoirse Ronan", "Timothée Chalamet", "Zendaya",
    "Samuel L. Jackson", "Jessica Chastain", "Hugh Jackman", "Anne Hathaway",
    "Jake Gyllenhaal", "Emma Watson", "Benedict Cumberbatch", "Margot Robbie",
    "Ryan Reynolds", "Gal Gadot", "Chris Evans", "Brie Larson",
    "Mark Ruffalo", "Tessa Thompson", "Oscar Isaac", "Florence Pugh",
    "Adam Driver", "Mahershala Ali", "Rami Malek", "Olivia Colman",
    "Gary Oldman", "Helen Mirren", "Javier Bardem", "Penélope Cruz",
    "Colin Firth", "Rachel Weisz", "Eddie Redmayne", "Alicia Vikander",
    "Michael Fassbender", "Lupita Nyong'o", "Chiwetel Ejiofor", "Octavia Spencer",
    "Forest Whitaker", "Taraji P. Henson", "Kerry Washington", "Halle Berry",
    "Jamie Foxx", "Don Cheadle", "Chadwick Boseman", "Danai Gurira",
    "Daniel Kaluuya", "John Boyega", "Letitia Wright", "Winston Duke",
    "Angela Bassett", "Whoopi Goldberg", "Laurence Fishburne", "Wesley Snipes",
    "Harrison Ford", "Sigourney Weaver", "Jeff Bridges", "Julianne Moore"
]

GENRES = ["Action", "Drama", "Comedy", "Thriller", "Sci-Fi", "Horror", "Romance", "Adventure"]

STUDIOS = ["Warner Bros", "Universal", "Paramount", "20th Century", "Columbia", "MGM", "Lionsgate", "A24"]


def create_database():
    """Create SQLite database with film tables and sample data"""

    conn = sqlite3.connect("films_data.db")
    cursor = conn.cursor()

    # Drop tables if exist
    cursor.execute("DROP TABLE IF EXISTS movies")
    cursor.execute("DROP TABLE IF EXISTS directors")
    cursor.execute("DROP TABLE IF EXISTS actors")

    # Create directors table
    cursor.execute("""
        CREATE TABLE directors (
            director_id INTEGER PRIMARY KEY AUTOINCREMENT,
            director_name TEXT NOT NULL,
            birth_year INTEGER,
            nationality TEXT
        )
    """)

    # Create actors table
    cursor.execute("""
        CREATE TABLE actors (
            actor_id INTEGER PRIMARY KEY AUTOINCREMENT,
            actor_name TEXT NOT NULL,
            birth_year INTEGER,
            nationality TEXT
        )
    """)

    # Create movies table
    cursor.execute("""
        CREATE TABLE movies (
            movie_id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            director_id INTEGER,
            lead_actor_id INTEGER,
            genre TEXT NOT NULL,
            release_year INTEGER NOT NULL,
            runtime_minutes INTEGER NOT NULL,
            rating REAL,
            box_office_millions REAL,
            studio TEXT,
            FOREIGN KEY (director_id) REFERENCES directors(director_id),
            FOREIGN KEY (lead_actor_id) REFERENCES actors(actor_id)
        )
    """)

    # Insert directors
    director_data = [
        (name, random.randint(1940, 1980), random.choice(["American", "British", "French", "Italian", "Korean", "Mexican"]))
        for name in DIRECTORS
    ]
    cursor.executemany(
        "INSERT INTO directors (director_name, birth_year, nationality) VALUES (?, ?, ?)",
        director_data
    )

    # Insert actors
    actor_data = [
        (name, random.randint(1950, 1990), random.choice(["American", "British", "Australian", "Canadian", "Irish"]))
        for name in ACTORS
    ]
    cursor.executemany(
        "INSERT INTO actors (actor_name, birth_year, nationality) VALUES (?, ?, ?)",
        actor_data
    )

    # Generate 600 movies
    movies_data = []
    for i in range(600):
        # Create unique titles by combining base titles with numbers/adjectives
        if i < len(MOVIE_TITLES):
            title = MOVIE_TITLES[i]
        else:
            base = random.choice(MOVIE_TITLES)
            num = (i // len(MOVIE_TITLES)) + 1
            title = f"{base} {num}"

        director_id = random.randint(1, len(DIRECTORS))
        lead_actor_id = random.randint(1, len(ACTORS))
        genre = random.choice(GENRES)
        release_year = random.randint(1990, 2024)
        runtime = random.randint(90, 180)
        rating = round(random.uniform(5.0, 9.5), 1)
        box_office = round(random.uniform(10, 800), 1)
        studio = random.choice(STUDIOS)

        movies_data.append((
            title,
            director_id,
            lead_actor_id,
            genre,
            release_year,
            runtime,
            rating,
            box_office,
            studio
        ))

    cursor.executemany(
        """INSERT INTO movies
           (title, director_id, lead_actor_id, genre, release_year, runtime_minutes, rating, box_office_millions, studio)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        movies_data
    )

    conn.commit()

    # Print summary
    cursor.execute("SELECT COUNT(*) FROM movies")
    movies_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM directors")
    directors_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM actors")
    actors_count = cursor.fetchone()[0]

    print(f"✅ Films database created successfully!")
    print(f"   - Movies: {movies_count}")
    print(f"   - Directors: {directors_count}")
    print(f"   - Actors: {actors_count}")

    conn.close()


if __name__ == "__main__":
    create_database()
