DROP TABLE IF EXISTS accounts;

CREATE TABLE accounts
(
    user_id TEXT PRIMARY KEY,
    password TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'user',
    iban TEXT UNIQUE,
    bic TEXT UNIQUE,
    account_number INTEGER UNIQUE,
    balance REAL NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'active'
);

DROP TABLE IF EXISTS transactions;

CREATE TABLE transactions
(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    amount REAL NOT NULL,
    date TEXT NOT NULL,
    description TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES accounts(user_id)
);

DROP TABLE IF EXISTS notifications;

CREATE TABLE notifications
(
    notif_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    message TEXT NOT NULL,
    date TEXT NOT NULL,
    read INTEGER DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES accounts(user_id)
);





