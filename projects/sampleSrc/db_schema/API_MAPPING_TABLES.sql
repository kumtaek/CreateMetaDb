-- API 매핑 사례를 위한 데이터베이스 테이블 스키마

-- 1. 사용자 관리 관련 테이블
CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL,
    status VARCHAR(20) DEFAULT 'ACTIVE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    del_yn CHAR(1) DEFAULT 'N',
    INDEX idx_username (username),
    INDEX idx_email (email),
    INDEX idx_status (status)
);

CREATE TABLE IF NOT EXISTS user_info (
    user_info_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    phone VARCHAR(20),
    address TEXT,
    birth_date DATE,
    last_login_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    del_yn CHAR(1) DEFAULT 'N',
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    INDEX idx_user_id (user_id)
);

CREATE TABLE IF NOT EXISTS user_profiles (
    profile_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    profile_image VARCHAR(255),
    bio TEXT,
    preferences JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    del_yn CHAR(1) DEFAULT 'N',
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    INDEX idx_user_id (user_id)
);

-- 2. 버전별 API 테이블
CREATE TABLE IF NOT EXISTS users_v1 (
    user_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL,
    status VARCHAR(20) DEFAULT 'ACTIVE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    del_yn CHAR(1) DEFAULT 'N',
    INDEX idx_username (username),
    INDEX idx_email (email)
);

-- 3. 제품 관련 테이블
CREATE TABLE IF NOT EXISTS products (
    product_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    product_name VARCHAR(100) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    stock_quantity INT DEFAULT 0,
    category_id BIGINT,
    brand_id BIGINT,
    status VARCHAR(20) DEFAULT 'ACTIVE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    del_yn CHAR(1) DEFAULT 'N',
    INDEX idx_product_name (product_name),
    INDEX idx_category_id (category_id),
    INDEX idx_brand_id (brand_id),
    INDEX idx_status (status)
);

CREATE TABLE IF NOT EXISTS categories (
    category_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    category_name VARCHAR(50) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    del_yn CHAR(1) DEFAULT 'N',
    INDEX idx_category_name (category_name)
);

CREATE TABLE IF NOT EXISTS brands (
    brand_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    brand_name VARCHAR(50) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    del_yn CHAR(1) DEFAULT 'N',
    INDEX idx_brand_name (brand_name)
);

-- 4. 주문 관련 테이블
CREATE TABLE IF NOT EXISTS orders (
    order_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_amount DECIMAL(10,2) NOT NULL,
    status VARCHAR(20) DEFAULT 'PENDING',
    shipping_address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    del_yn CHAR(1) DEFAULT 'N',
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    INDEX idx_user_id (user_id),
    INDEX idx_order_date (order_date),
    INDEX idx_status (status)
);

CREATE TABLE IF NOT EXISTS order_items (
    order_item_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    order_id BIGINT NOT NULL,
    product_id BIGINT NOT NULL,
    quantity INT NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    subtotal DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    del_yn CHAR(1) DEFAULT 'N',
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    INDEX idx_order_id (order_id),
    INDEX idx_product_id (product_id)
);

-- 5. 결제 관련 테이블
CREATE TABLE IF NOT EXISTS payments (
    payment_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    order_id BIGINT NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    payment_method VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'PENDING',
    transaction_id VARCHAR(100),
    processed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    del_yn CHAR(1) DEFAULT 'N',
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    INDEX idx_order_id (order_id),
    INDEX idx_transaction_id (transaction_id),
    INDEX idx_status (status)
);

-- 6. 알림 관련 테이블
CREATE TABLE IF NOT EXISTS notifications (
    notification_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    title VARCHAR(100) NOT NULL,
    message TEXT NOT NULL,
    type VARCHAR(50) NOT NULL,
    is_read CHAR(1) DEFAULT 'N',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    del_yn CHAR(1) DEFAULT 'N',
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    INDEX idx_user_id (user_id),
    INDEX idx_type (type),
    INDEX idx_is_read (is_read)
);

-- 7. 추천 관련 테이블
CREATE TABLE IF NOT EXISTS recommendations (
    recommendation_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    product_id BIGINT NOT NULL,
    score DECIMAL(3,2) NOT NULL,
    status VARCHAR(20) DEFAULT 'ACTIVE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    del_yn CHAR(1) DEFAULT 'N',
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    INDEX idx_user_id (user_id),
    INDEX idx_product_id (product_id),
    INDEX idx_status (status)
);

-- 샘플 데이터 삽입
INSERT INTO users (username, email, status) VALUES
('john_doe', 'john@example.com', 'ACTIVE'),
('jane_smith', 'jane@example.com', 'ACTIVE'),
('bob_wilson', 'bob@example.com', 'INACTIVE');

INSERT INTO user_info (user_id, phone, address, birth_date) VALUES
(1, '010-1234-5678', '서울시 강남구', '1990-01-01'),
(2, '010-2345-6789', '서울시 서초구', '1985-05-15'),
(3, '010-3456-7890', '서울시 송파구', '1992-12-25');

INSERT INTO categories (category_name, description) VALUES
('전자제품', '스마트폰, 노트북 등 전자제품'),
('의류', '남성, 여성 의류'),
('도서', '소설, 기술서적 등');

INSERT INTO brands (brand_name, description) VALUES
('삼성', '삼성전자 제품'),
('애플', '애플 제품'),
('나이키', '나이키 스포츠웨어');

INSERT INTO products (product_name, description, price, stock_quantity, category_id, brand_id) VALUES
('갤럭시 S24', '삼성 스마트폰', 1200000, 50, 1, 1),
('아이폰 15', '애플 스마트폰', 1300000, 30, 1, 2),
('나이키 에어맥스', '운동화', 150000, 100, 2, 3);

INSERT INTO orders (user_id, total_amount, status) VALUES
(1, 1200000, 'COMPLETED'),
(2, 1300000, 'PENDING'),
(3, 150000, 'COMPLETED');

INSERT INTO order_items (order_id, product_id, quantity, price, subtotal) VALUES
(1, 1, 1, 1200000, 1200000),
(2, 2, 1, 1300000, 1300000),
(3, 3, 1, 150000, 150000);
