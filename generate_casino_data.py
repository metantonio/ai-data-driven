import sqlite3
import random
import datetime
import os

DB_NAME = "example_casino.db"

def create_connection():
    """Create a database connection to the SQLite database specified by DB_NAME"""
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        print(f"Connected to {DB_NAME}")
    except sqlite3.Error as e:
        print(e)
    return conn

def create_tables(conn):
    """Create tables for casinos, games, players, and game_sessions"""
    cursor = conn.cursor()
    
    # 1. Casinos Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS casinos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        city TEXT NOT NULL,
        state TEXT NOT NULL,
        opened_date DATE
    );
    """)

    # 2. Games Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS games (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        casino_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        type TEXT NOT NULL,
        min_bet REAL,
        max_bet REAL,
        house_edge REAL,
        FOREIGN KEY (casino_id) REFERENCES casinos (id)
    );
    """)

    # 3. Players Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS players (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        age INTEGER,
        gender TEXT,
        signup_date DATE,
        loyalty_tier TEXT
    );
    """)

    # 4. Game Sessions (Play History)
    # Allows tracking wins/losses per session
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS game_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        player_id INTEGER NOT NULL,
        game_id INTEGER NOT NULL,
        session_date DATETIME NOT NULL,
        duration_minutes INTEGER,
        total_wagered REAL,
        net_outcome REAL, -- Positive for win, negative for loss
        FOREIGN KEY (player_id) REFERENCES players (id),
        FOREIGN KEY (game_id) REFERENCES games (id)
    );
    """)
    
    conn.commit()
    print("Tables created successfully.")

def generate_data(conn):
    cursor = conn.cursor()

    # --- Data for Casinos ---
    casino_names = [
        ("The Golden Chip", "Las Vegas", "NV"),
        ("Ocean's Fortune", "Atlantic City", "NJ"),
        ("Royal Flush Resort", "Reno", "NV"),
        ("Mystic Lake Slots", "Prior Lake", "MN"),
        ("Desert Diamond", "Tucson", "AZ")
    ]
    
    cities = ["Las Vegas", "Atlantic City", "Reno", "Biloxi", "Detroit"]
    states = ["NV", "NJ", "NV", "MS", "MI"]

    print("Generating Casinos...")
    for name, city, state in casino_names:
        opened = datetime.date(random.randint(1990, 2020), random.randint(1, 12), random.randint(1, 28))
        cursor.execute("INSERT INTO casinos (name, city, state, opened_date) VALUES (?, ?, ?, ?)", 
                       (name, city, state, opened))
    
    # Get casino IDs
    cursor.execute("SELECT id FROM casinos")
    casino_ids = [row[0] for row in cursor.fetchall()]

    # --- Data for Games ---
    game_types = ["Slot Machine", "Blackjack", "Roulette", "Poker", "Baccarat", "Craps"]
    adjectives = ["Lucky", "Super", "Mega", "Golden", "Wild", "Royal", "Fortune"]
    nouns = ["777", "Wheel", "Cards", "Jackpot", "Reels", "Dice", "Table"]

    print("Generating Games...")
    for c_id in casino_ids:
        # Create ~20-50 games per casino
        num_games = random.randint(20, 50)
        for _ in range(num_games):
            g_type = random.choice(game_types)
            name = f"{random.choice(adjectives)} {random.choice(nouns)}"
            if g_type == "Slot Machine":
                name += " Slots"
                house_edge = random.uniform(0.02, 0.15) # 2% to 15% edge
                min_bet = 0.50
                max_bet = 100.0
            elif g_type == "Blackjack":
                house_edge = random.uniform(0.005, 0.02) # Skill dependent, but avg low
                min_bet = 10.0
                max_bet = 5000.0
            elif g_type == "Roulette":
                house_edge = 0.0526 # American Roulette standard
                min_bet = 5.0
                max_bet = 2000.0
            else:
                house_edge = random.uniform(0.01, 0.05)
                min_bet = 5.0
                max_bet = 1000.0
            
            cursor.execute("""
                INSERT INTO games (casino_id, name, type, min_bet, max_bet, house_edge) 
                VALUES (?, ?, ?, ?, ?, ?)
            """, (c_id, name, g_type, min_bet, max_bet, house_edge))

    # Get game IDs for sessions
    cursor.execute("SELECT id, type, house_edge, max_bet FROM games")
    games_data = cursor.fetchall() # List of (id, type, house_edge, max_bet)

    # --- Data for Players ---
    first_names = ["James", "Mary", "Robert", "Patricia", "John", "Jennifer", "Michael", "Linda", "David", "Elizabeth", "William", "Barbara", "Richard", "Susan", "Joseph", "Jessica"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson"]
    
    print("Generating Players...")
    num_players = 1000
    for _ in range(num_players):
        f_name = random.choice(first_names)
        l_name = random.choice(last_names)
        age = random.randint(21, 90)
        gender = random.choice(["M", "F"])
        signup = datetime.date(random.randint(2018, 2024), random.randint(1, 12), random.randint(1, 28))
        tier = random.choices(["Bronze", "Silver", "Gold", "Platinum"], weights=[0.6, 0.25, 0.1, 0.05])[0]
        
        cursor.execute("""
            INSERT INTO players (first_name, last_name, age, gender, signup_date, loyalty_tier) 
            VALUES (?, ?, ?, ?, ?, ?)
        """, (f_name, l_name, age, gender, signup, tier))

    # Get player IDs
    cursor.execute("SELECT id, signup_date FROM players")
    players_data = cursor.fetchall()

    # --- Data for Game Sessions ---
    print("Generating Game Sessions...")
    total_sessions = 10000
    
    # Insert in batches for speed
    batch_size = 500
    sessions_batch = []
    
    for _ in range(total_sessions):
        p_id, p_signup_str = random.choice(players_data)
        p_signup = datetime.datetime.strptime(p_signup_str, "%Y-%m-%d").date()
        
        g_id, g_type, house_edge, g_max = random.choice(games_data)
        
        # Session date must be after signup
        days_since_signup = (datetime.date.today() - p_signup).days
        if days_since_signup < 0: days_since_signup = 0
        session_delta = random.randint(0, days_since_signup)
        session_date = p_signup + datetime.timedelta(days=session_delta)
        # Add random time
        session_datetime = datetime.datetime.combine(session_date, datetime.time(random.randint(0, 23), random.randint(0, 59)))
        
        duration = random.randint(5, 300) # 5 mins to 5 hours
        
        # Determine wager and outcome
        # Approximate: total wavered = avg_bet * bets_per_min * duration
        bets_per_min = 10 if g_type == "Slot Machine" else 0.5 # Slots are fast
        avg_bet = random.uniform(1, g_max / 10)
        total_wagered = round(avg_bet * bets_per_min * duration, 2)
        
        # Simulate outcome based on house edge
        # Expected loss = total_wagered * house_edge
        # We add volatility (standard deviation)
        expected_loss = total_wagered * house_edge
        volatility = total_wagered * 2.0 # High variance
        
        # Random outcome normally distributed around expected loss
        # Net outcome is positive (win) or negative (loss)
        net_outcome = round(random.gauss(-expected_loss, volatility), 2)
        
        sessions_batch.append((p_id, g_id, session_datetime, duration, total_wagered, net_outcome))
        
        if len(sessions_batch) >= batch_size:
            cursor.executemany("""
                INSERT INTO game_sessions (player_id, game_id, session_date, duration_minutes, total_wagered, net_outcome)
                VALUES (?, ?, ?, ?, ?, ?)
            """, sessions_batch)
            sessions_batch = []
            
    if sessions_batch:
        cursor.executemany("""
            INSERT INTO game_sessions (player_id, game_id, session_date, duration_minutes, total_wagered, net_outcome)
            VALUES (?, ?, ?, ?, ?, ?)
        """, sessions_batch)

    conn.commit()
    print("Data generation complete.")

if __name__ == "__main__":
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME) # Clean start
        
    conn = create_connection()
    if conn:
        create_tables(conn)
        generate_data(conn)
        conn.close()
