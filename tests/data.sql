INSERT INTO user (phonenumber, firstname, lastname, email, check_in_state, last_time_in)
VALUES  ('2615556666', 'user1','last1', 'user@email.com', 1, CURRENT_TIMESTAMP),
('2615557777', 'user2','last2', 'user2@email.com', 1, CURRENT_TIMESTAMP);
INSERT INTO time_sheet (user_id, check_in_state, time_in, time_out)
VALUES(1, 1, '2018-01-01 00:00:00', '2018-01-01 09:00:00');



