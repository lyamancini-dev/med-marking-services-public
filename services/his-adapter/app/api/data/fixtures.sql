-- Товары (6шт)
INSERT INTO SERVICES (ID, NAME, GTIN, IS_MARKED, REST, STORE_ID) VALUES
(1, 'Шприц 5 мл', NULL, 0, 100, 1),
(2, 'Шприц 5 мл', NULL, 0, 50, 2),
(3, 'Бинт стерильный', NULL, 0, 200, 1),
(4, 'Эндопротез тазобедренный', '04601234567890', 1, 5, 1),
(5, 'Катетер уретральный', '04601234567891', 1, 3, 2),
(6, 'Перчатки смотровые', NULL, 0, 500, 1);

-- Коды маркировки для маркированных товаров
INSERT INTO SGTIN_REGISTRY (ID, SERVICE_ID, SGTIN, STATUS) VALUES
(1, 4, '010460123456789021serial1\u001d93crypto', 'AVAILABLE'),
(2, 4, '010460123456789021serial2\u001d93crypto', 'AVAILABLE'),
(3, 4, '010460123456789021serial3\u001d93crypto', 'AVAILABLE'),
(4, 5, '010460123456789121serial1\u001d93crypto', 'AVAILABLE'),
(5, 5, '010460123456789121serial2\u001d93crypto', 'AVAILABLE');