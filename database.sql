-- ONLINE VOTING SYSTEM DATABASE

DROP TABLE IF EXISTS votes;
DROP TABLE IF EXISTS candidates;
DROP TABLE IF EXISTS voters;

CREATE TABLE voters (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(100) NOT NULL,
    has_voted BOOLEAN DEFAULT FALSE
);

CREATE TABLE candidates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    party VARCHAR(100) NOT NULL
);

CREATE TABLE votes (
    id SERIAL PRIMARY KEY,
    voter_id INTEGER UNIQUE REFERENCES voters(id),
    candidate_id INTEGER REFERENCES candidates(id),
    voted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO candidates (name, party)
VALUES
('Rahul Sharma', 'Development Party'),
('Priya Patil', 'People Party'),
('Amit Kumar', 'Progress Party'),
('Sneha Joshi', 'National Party');

INSERT INTO voters (name, email, password)
VALUES
('Test Voter', 'test@gmail.com', '12345');
