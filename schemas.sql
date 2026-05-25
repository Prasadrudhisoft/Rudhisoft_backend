CREATE TABLE admins (
    id INT NOT NULL AUTO_INCREMENT,
    username VARCHAR(100),
    email VARCHAR(100),
    password VARCHAR(255),
    reset_token VARCHAR(255),
    reset_token_expiry DATETIME,

    PRIMARY KEY (id)
);

CREATE TABLE applications (
    id INT NOT NULL AUTO_INCREMENT,
    career_id INT NOT NULL,
    applicant_name VARCHAR(100) NOT NULL,
    applicant_email VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    resume VARCHAR(255) NOT NULL,
    cover_letter TEXT,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_read TINYINT(1) DEFAULT 0,
    read_at TIMESTAMP NULL DEFAULT NULL,

    PRIMARY KEY (id),

    FOREIGN KEY (career_id)
    REFERENCES careers(id)
    ON DELETE CASCADE
);

CREATE TABLE careers (
    id INT NOT NULL AUTO_INCREMENT,
    title VARCHAR(255),
    description TEXT,
    location VARCHAR(100),
    job_type VARCHAR(50),
    status VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id)
);

CREATE TABLE contacts (
    id INT NOT NULL AUTO_INCREMENT,
    name VARCHAR(100),
    email VARCHAR(100),
    message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_read TINYINT(1) DEFAULT 0,
    read_at TIMESTAMP NULL DEFAULT NULL,

    PRIMARY KEY (id)
);