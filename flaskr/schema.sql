-- 1. Enter the venv 
-- 2. Enable any tables you drop below
-- 3. 'flask --app flaskr init-db' command

-- DROP TABLE IF EXISTS user;
-- DROP TABLE IF EXISTS post;
-- DROP TABLE IF EXISTS company_info;
DROP TABLE IF EXISTS favorites;


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

-- Extraneous stuff that might be useful
CREATE TABLE IF NOT EXISTS company_info (
  company_id INTEGER PRIMARY KEY AUTOINCREMENT,
  ticker TEXT NOT NULL,
  name TEXT NOT NULL,
  country TEXT,
  ipo_year INTEGER,
  sector TEXT,
  industry TEXT
);