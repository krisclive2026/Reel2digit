CREATE TABLE IF NOT EXISTS pricing_configs (
	id SERIAL NOT NULL, 
	unit_price FLOAT, 
	shipping_flat FLOAT, 
	max_cassettes INTEGER, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
);
CREATE INDEX IF NOT EXISTS ix_pricing_configs_id ON pricing_configs (id);

CREATE TABLE IF NOT EXISTS users (
	id SERIAL NOT NULL, 
	email VARCHAR NOT NULL, 
	hashed_password VARCHAR NOT NULL, 
	full_name VARCHAR NOT NULL, 
	phone VARCHAR, 
	street_address VARCHAR, 
	city VARCHAR, 
	state VARCHAR, 
	postal_code VARCHAR, 
	country VARCHAR, 
	role VARCHAR, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
);
CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email ON users (email);
CREATE INDEX IF NOT EXISTS ix_users_id ON users (id);

CREATE TABLE IF NOT EXISTS orders (
	id SERIAL NOT NULL, 
	order_number VARCHAR, 
	user_id INTEGER NOT NULL, 
	status VARCHAR, 
	cassette_count INTEGER NOT NULL, 
	format VARCHAR, 
	unit_price FLOAT NOT NULL, 
	shipping_fee FLOAT NOT NULL, 
	total_price FLOAT NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);
CREATE INDEX IF NOT EXISTS ix_orders_id ON orders (id);
CREATE UNIQUE INDEX IF NOT EXISTS ix_orders_order_number ON orders (order_number);

CREATE TABLE IF NOT EXISTS cassettes (
	id SERIAL NOT NULL, 
	order_id INTEGER NOT NULL, 
	tag_name VARCHAR NOT NULL, 
	sequence INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(order_id) REFERENCES orders (id)
);
CREATE INDEX IF NOT EXISTS ix_cassettes_id ON cassettes (id);

CREATE TABLE IF NOT EXISTS feedbacks (
	id SERIAL NOT NULL, 
	order_id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	rating INTEGER NOT NULL, 
	comment TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	UNIQUE (order_id), 
	FOREIGN KEY(order_id) REFERENCES orders (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);
CREATE INDEX IF NOT EXISTS ix_feedbacks_id ON feedbacks (id);

CREATE TABLE IF NOT EXISTS payments (
	id SERIAL NOT NULL, 
	order_id INTEGER NOT NULL, 
	amount FLOAT NOT NULL, 
	provider VARCHAR, 
	status VARCHAR, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(order_id) REFERENCES orders (id)
);
CREATE INDEX IF NOT EXISTS ix_payments_id ON payments (id);

CREATE TABLE IF NOT EXISTS shipping_labels (
	id SERIAL NOT NULL, 
	order_id INTEGER NOT NULL, 
	tracking_number VARCHAR NOT NULL, 
	carrier VARCHAR, 
	label_url VARCHAR NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	UNIQUE (order_id), 
	FOREIGN KEY(order_id) REFERENCES orders (id), 
	UNIQUE (tracking_number)
);
CREATE INDEX IF NOT EXISTS ix_shipping_labels_id ON shipping_labels (id);

CREATE TABLE IF NOT EXISTS media_assets (
	id SERIAL NOT NULL, 
	order_id INTEGER NOT NULL, 
	cassette_id INTEGER, 
	file_name VARCHAR NOT NULL, 
	file_url VARCHAR NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(order_id) REFERENCES orders (id), 
	FOREIGN KEY(cassette_id) REFERENCES cassettes (id)
);
CREATE INDEX IF NOT EXISTS ix_media_assets_id ON media_assets (id);

