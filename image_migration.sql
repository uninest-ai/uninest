-- Property Image Migration SQL
-- Generated automatically

-- Migrate API images to PropertyImage records
INSERT INTO property_images (property_id, image_url, is_primary, labels, created_at) 
VALUES (1, 'https://ar.rdcpix.com/5d251a9e12edc3508e326306f7d7c3d0c-f2209203381s.jpg', true, NULL, NOW());
INSERT INTO property_images (property_id, image_url, is_primary, labels, created_at) 
VALUES (1, 'https://ar.rdcpix.com/5d251a9e12edc3508e326306f7d7c3d0c-f716391261s.jpg', false, NULL, NOW());
UPDATE properties SET image_url = 'https://ar.rdcpix.com/5d251a9e12edc3508e326306f7d7c3d0c-f2209203381s.jpg' WHERE id = 1 AND image_url IS NULL;
INSERT INTO property_images (property_id, image_url, is_primary, labels, created_at) 
VALUES (2, 'https://ap.rdcpix.com/08eecc565e8dd9fbecc85b2287d9fe29l-m1913496513s.jpg', true, NULL, NOW());
INSERT INTO property_images (property_id, image_url, is_primary, labels, created_at) 
VALUES (2, 'https://ap.rdcpix.com/08eecc565e8dd9fbecc85b2287d9fe29l-m4203691149s.jpg', false, NULL, NOW());
UPDATE properties SET image_url = 'https://ap.rdcpix.com/08eecc565e8dd9fbecc85b2287d9fe29l-m1913496513s.jpg' WHERE id = 2 AND image_url IS NULL;
INSERT INTO property_images (property_id, image_url, is_primary, labels, created_at) 
VALUES (3, 'https://ap.rdcpix.com/f74e85a0c5883dd6b1268fb68297d169l-m818868505s.jpg', true, NULL, NOW());
INSERT INTO property_images (property_id, image_url, is_primary, labels, created_at) 
VALUES (3, 'https://ap.rdcpix.com/f74e85a0c5883dd6b1268fb68297d169l-m1689551708s.jpg', false, NULL, NOW());
UPDATE properties SET image_url = 'https://ap.rdcpix.com/f74e85a0c5883dd6b1268fb68297d169l-m818868505s.jpg' WHERE id = 3 AND image_url IS NULL;
INSERT INTO property_images (property_id, image_url, is_primary, labels, created_at) 
VALUES (4, 'https://ap.rdcpix.com/acdf405b3d2f911f4bac507f8c5cb176l-b898573106s.jpg', true, NULL, NOW());
INSERT INTO property_images (property_id, image_url, is_primary, labels, created_at) 
VALUES (4, 'https://ap.rdcpix.com/acdf405b3d2f911f4bac507f8c5cb176l-b2122179514s.jpg', false, NULL, NOW());
UPDATE properties SET image_url = 'https://ap.rdcpix.com/acdf405b3d2f911f4bac507f8c5cb176l-b898573106s.jpg' WHERE id = 4 AND image_url IS NULL;
INSERT INTO property_images (property_id, image_url, is_primary, labels, created_at) 
VALUES (5, 'https://ar.rdcpix.com/eae410977deb1fbe4c535ef6cbd54e40c-f4256898294s.jpg', true, NULL, NOW());
INSERT INTO property_images (property_id, image_url, is_primary, labels, created_at) 
VALUES (5, 'https://ar.rdcpix.com/eae410977deb1fbe4c535ef6cbd54e40c-f142054697s.jpg', false, NULL, NOW());
UPDATE properties SET image_url = 'https://ar.rdcpix.com/eae410977deb1fbe4c535ef6cbd54e40c-f4256898294s.jpg' WHERE id = 5 AND image_url IS NULL;
INSERT INTO property_images (property_id, image_url, is_primary, labels, created_at) 
VALUES (6, 'https://ap.rdcpix.com/8523424e85f64e51a1b5af1f07d09855l-b2736482765s.jpg', true, NULL, NOW());
INSERT INTO property_images (property_id, image_url, is_primary, labels, created_at) 
VALUES (6, 'https://ap.rdcpix.com/8523424e85f64e51a1b5af1f07d09855l-b765709644s.jpg', false, NULL, NOW());
UPDATE properties SET image_url = 'https://ap.rdcpix.com/8523424e85f64e51a1b5af1f07d09855l-b2736482765s.jpg' WHERE id = 6 AND image_url IS NULL;
INSERT INTO property_images (property_id, image_url, is_primary, labels, created_at) 
VALUES (7, 'https://ap.rdcpix.com/7e5d46b5028c4886c2fedf648473d0afl-m3245678743s.jpg', true, NULL, NOW());
INSERT INTO property_images (property_id, image_url, is_primary, labels, created_at) 
VALUES (7, 'https://ap.rdcpix.com/7e5d46b5028c4886c2fedf648473d0afl-m804206718s.jpg', false, NULL, NOW());
UPDATE properties SET image_url = 'https://ap.rdcpix.com/7e5d46b5028c4886c2fedf648473d0afl-m3245678743s.jpg' WHERE id = 7 AND image_url IS NULL;
INSERT INTO property_images (property_id, image_url, is_primary, labels, created_at) 
VALUES (8, 'https://ap.rdcpix.com/aadcffd5422ff99b23b276b7f2cd9dc9l-m1073036565s.jpg', true, NULL, NOW());
INSERT INTO property_images (property_id, image_url, is_primary, labels, created_at) 
VALUES (8, 'https://ap.rdcpix.com/aadcffd5422ff99b23b276b7f2cd9dc9l-m3558016735s.jpg', false, NULL, NOW());
UPDATE properties SET image_url = 'https://ap.rdcpix.com/aadcffd5422ff99b23b276b7f2cd9dc9l-m1073036565s.jpg' WHERE id = 8 AND image_url IS NULL;
INSERT INTO property_images (property_id, image_url, is_primary, labels, created_at) 
VALUES (9, 'https://ap.rdcpix.com/1caf98b5d98178e7116b1f2037d636e3l-m1882589596s.jpg', true, NULL, NOW());
INSERT INTO property_images (property_id, image_url, is_primary, labels, created_at) 
VALUES (9, 'https://ap.rdcpix.com/1caf98b5d98178e7116b1f2037d636e3l-m556979591s.jpg', false, NULL, NOW());
UPDATE properties SET image_url = 'https://ap.rdcpix.com/1caf98b5d98178e7116b1f2037d636e3l-m1882589596s.jpg' WHERE id = 9 AND image_url IS NULL;
INSERT INTO property_images (property_id, image_url, is_primary, labels, created_at) 
VALUES (10, 'https://ap.rdcpix.com/6b2d7785787a17bc4131b32c3a4f75a8l-m2674070436s.jpg', true, NULL, NOW());
INSERT INTO property_images (property_id, image_url, is_primary, labels, created_at) 
VALUES (10, 'https://ap.rdcpix.com/6b2d7785787a17bc4131b32c3a4f75a8l-m2656859030s.jpg', false, NULL, NOW());
UPDATE properties SET image_url = 'https://ap.rdcpix.com/6b2d7785787a17bc4131b32c3a4f75a8l-m2674070436s.jpg' WHERE id = 10 AND image_url IS NULL;
INSERT INTO property_images (property_id, image_url, is_primary, labels, created_at) 
VALUES (11, 'https://ap.rdcpix.com/a6c614c598ad6f16ce5058b3efe5aef1l-m2531204842s.jpg', true, NULL, NOW());
INSERT INTO property_images (property_id, image_url, is_primary, labels, created_at) 
VALUES (11, 'https://ap.rdcpix.com/a6c614c598ad6f16ce5058b3efe5aef1l-m2110305880s.jpg', false, NULL, NOW());
UPDATE properties SET image_url = 'https://ap.rdcpix.com/a6c614c598ad6f16ce5058b3efe5aef1l-m2531204842s.jpg' WHERE id = 11 AND image_url IS NULL;
INSERT INTO property_images (property_id, image_url, is_primary, labels, created_at) 
VALUES (12, 'https://ap.rdcpix.com/bc8b6981d8d5827c056ca9594e1f8381l-m2719905978s.jpg', true, NULL, NOW());
INSERT INTO property_images (property_id, image_url, is_primary, labels, created_at) 
VALUES (12, 'https://ap.rdcpix.com/bc8b6981d8d5827c056ca9594e1f8381l-m2096242334s.jpg', false, NULL, NOW());
UPDATE properties SET image_url = 'https://ap.rdcpix.com/bc8b6981d8d5827c056ca9594e1f8381l-m2719905978s.jpg' WHERE id = 12 AND image_url IS NULL;
INSERT INTO property_images (property_id, image_url, is_primary, labels, created_at) 
VALUES (13, 'https://ap.rdcpix.com/ae116d58d79be2b0ce48f0a21549bba7l-m3234768441s.jpg', true, NULL, NOW());
INSERT INTO property_images (property_id, image_url, is_primary, labels, created_at) 
VALUES (13, 'https://ap.rdcpix.com/ae116d58d79be2b0ce48f0a21549bba7l-m1926551985s.jpg', false, NULL, NOW());
UPDATE properties SET image_url = 'https://ap.rdcpix.com/ae116d58d79be2b0ce48f0a21549bba7l-m3234768441s.jpg' WHERE id = 13 AND image_url IS NULL;
INSERT INTO property_images (property_id, image_url, is_primary, labels, created_at) 
VALUES (14, 'https://ap.rdcpix.com/20132ba900f12d1e28ce99d6e60af183l-m323633575s.jpg', true, NULL, NOW());
INSERT INTO property_images (property_id, image_url, is_primary, labels, created_at) 
VALUES (14, 'https://ap.rdcpix.com/20132ba900f12d1e28ce99d6e60af183l-m306467066s.jpg', false, NULL, NOW());
UPDATE properties SET image_url = 'https://ap.rdcpix.com/20132ba900f12d1e28ce99d6e60af183l-m323633575s.jpg' WHERE id = 14 AND image_url IS NULL;
INSERT INTO property_images (property_id, image_url, is_primary, labels, created_at) 
VALUES (15, 'https://ap.rdcpix.com/58db88b2a34d89d3bd7823261de19199l-m3970213672s.jpg', true, NULL, NOW());
INSERT INTO property_images (property_id, image_url, is_primary, labels, created_at) 
VALUES (15, 'https://ap.rdcpix.com/58db88b2a34d89d3bd7823261de19199l-m3595145763s.jpg', false, NULL, NOW());
UPDATE properties SET image_url = 'https://ap.rdcpix.com/58db88b2a34d89d3bd7823261de19199l-m3970213672s.jpg' WHERE id = 15 AND image_url IS NULL;
INSERT INTO property_images (property_id, image_url, is_primary, labels, created_at) 
VALUES (16, 'https://ap.rdcpix.com/a81339225c3220ed2389c129bef97487l-m865561217s.jpg', true, NULL, NOW());
INSERT INTO property_images (property_id, image_url, is_primary, labels, created_at) 
VALUES (16, 'https://ap.rdcpix.com/a81339225c3220ed2389c129bef97487l-m2513615279s.jpg', false, NULL, NOW());
UPDATE properties SET image_url = 'https://ap.rdcpix.com/a81339225c3220ed2389c129bef97487l-m865561217s.jpg' WHERE id = 16 AND image_url IS NULL;
INSERT INTO property_images (property_id, image_url, is_primary, labels, created_at) 
VALUES (17, 'https://ap.rdcpix.com/2a49f162dc3ae9ee85116ac5749979e0l-m431946071s.jpg', true, NULL, NOW());
INSERT INTO property_images (property_id, image_url, is_primary, labels, created_at) 
VALUES (17, 'https://ap.rdcpix.com/2a49f162dc3ae9ee85116ac5749979e0l-m4185273030s.jpg', false, NULL, NOW());
UPDATE properties SET image_url = 'https://ap.rdcpix.com/2a49f162dc3ae9ee85116ac5749979e0l-m431946071s.jpg' WHERE id = 17 AND image_url IS NULL;
INSERT INTO property_images (property_id, image_url, is_primary, labels, created_at) 
VALUES (18, 'https://ar.rdcpix.com/6355a978f5e662496eb2457d6947b066c-f1906203999s.jpg', true, NULL, NOW());
UPDATE properties SET image_url = 'https://ar.rdcpix.com/6355a978f5e662496eb2457d6947b066c-f1906203999s.jpg' WHERE id = 18 AND image_url IS NULL;

-- Add fallback images
INSERT INTO property_images (property_id, image_url, is_primary, labels, created_at) 
VALUES (70, 'https://images.unsplash.com/photo-1568605114967-8130f3a36994?w=800&h=600&fit=crop&crop=entropy&cs=tinysrgb', true, '["fallback_image"]', NOW());
UPDATE properties SET image_url = 'https://images.unsplash.com/photo-1568605114967-8130f3a36994?w=800&h=600&fit=crop&crop=entropy&cs=tinysrgb' WHERE id = 70 AND image_url IS NULL;
INSERT INTO property_images (property_id, image_url, is_primary, labels, created_at) 
VALUES (71, 'https://images.unsplash.com/photo-1568605114967-8130f3a36994?w=800&h=600&fit=crop&crop=entropy&cs=tinysrgb', true, '["fallback_image"]', NOW());
UPDATE properties SET image_url = 'https://images.unsplash.com/photo-1568605114967-8130f3a36994?w=800&h=600&fit=crop&crop=entropy&cs=tinysrgb' WHERE id = 71 AND image_url IS NULL;
