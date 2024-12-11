-- Create table for comments
CREATE TABLE comments (
    id SERIAL PRIMARY KEY,              
    stock VARCHAR(50) NOT NULL,          
    comment_time TIMESTAMP NOT NULL,    
    comments TEXT NOT NULL,         
    sentiment_tag VARCHAR(50),     
    influence INT
);

CREATE TABLE sentiment_score (
    id SERIAL PRIMARY KEY,              
    stock VARCHAR(50) NOT NULL,          
    comment_time TIMESTAMP NOT NULL,    
    comments TEXT NOT NULL,         
    sentiment_tag VARCHAR(50),     
    influence INT,                 
    sentiment VARCHAR(50) NOT NULL,
    score REAL NOT NULL   
);