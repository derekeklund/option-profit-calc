-- 1. Enter the venv 
-- 2. Enable any tables you drop below
-- 3. 'flask --app flaskr init-db' command
-- 4. Update the utils.py file if necessary
-- 5. Go to the /update-db route to update the database

-- DROP TABLE IF EXISTS user;
-- DROP TABLE IF EXISTS post;
-- DROP TABLE IF EXISTS favorites;
-- DROP TABLE IF EXISTS company_info;
-- DROP TABLE IF EXISTS nasdaq_100;
-- DROP TABLE IF EXISTS s_and_p_500;
-- DROP TABLE IF EXISTS russell_2000;

-- DELETE FROM favorites WHERE ticker = 'aapl';
-- DELETE FROM favorites WHERE id = 31;

-- ALTER TABLE company_info 
-- ADD COLUMN market_index TEXT;


CREATE TABLE IF NOT EXISTS company_info (
  company_id INTEGER PRIMARY KEY AUTOINCREMENT,
  ticker TEXT NOT NULL,
  name TEXT NOT NULL,
  country TEXT,
  ipo_year INTEGER,
  sector TEXT,
  industry TEXT,
  UNIQUE (ticker)
);

CREATE TABLE IF NOT EXISTS nasdaq_100 (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  company_id INTEGER NOT NULL,
  ticker TEXT NOT NULL,
  FOREIGN KEY (company_id) REFERENCES company_info (company_id)
  UNIQUE (company_id, ticker)
);

CREATE TABLE IF NOT EXISTS s_and_p_500 (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  company_id INTEGER NOT NULL,
  ticker TEXT NOT NULL,
  FOREIGN KEY (company_id) REFERENCES company_info (company_id)
  UNIQUE (company_id, ticker)
);

CREATE TABLE IF NOT EXISTS russell_2000 (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  company_id INTEGER NOT NULL,
  ticker TEXT NOT NULL,
  FOREIGN KEY (company_id) REFERENCES company_info (company_id)
  UNIQUE (company_id, ticker)
);



CREATE TABLE IF NOT EXISTS user (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS favorites (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  ticker TEXT NOT NULL,
  FOREIGN KEY (user_id) REFERENCES user (id),
  UNIQUE (user_id, ticker)
);

-- Blog stuff
CREATE TABLE IF NOT EXISTS post (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  author_id INTEGER NOT NULL,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  title TEXT NOT NULL,
  body TEXT NOT NULL,
  FOREIGN KEY (author_id) REFERENCES user (id)
);

