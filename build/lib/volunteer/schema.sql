DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS time_sheet;

CREATE TABLE user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    phonenumber char(10) unique NOT NULL,
    firstname TEXT NOT NULL,
    lastname TEXT NOT NULL,
    email TEXT,
    check_in_state BINARY,
    last_time_in DATETIME NOT NULL,
    last_time_out DATETIME,
    account_activated TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    account_updated TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE time_sheet (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    check_in_state BINARY NOT NULL,
    time_in DATETIME NOT NULL,
    time_out DATETIME,
    time_created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    time_modified TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user (id)
);
