DROP DATABASE metabet;
CREATE DATABASE metabet;
USE metabet;
CREATE TABLE `choices` (
  `poll_date` date NOT NULL,
  `choice` varchar(50) NOT NULL,
  `s3_filename` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`poll_date`,`choice`)
);
CREATE TABLE `votes` (
  `user_id` varchar(50) NOT NULL,
  `vote_date` date NOT NULL,
  `choice` varchar(50) NOT NULL,
  PRIMARY KEY (`user_id`,`vote_date`)
);
CREATE TABLE `tournaments` (
  `id` int NOT NULL AUTO_INCREMENT,
  `start_date` date DEFAULT NULL,
  `theme` varchar(255) DEFAULT NULL,
  `logo` varchar(255) DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`)
);
CREATE TABLE `user_entries` (
  `metamask_id` varchar(255) NOT NULL,
  `num_nfts` int NOT NULL DEFAULT '1',
  `is_alive` tinyint(1) NOT NULL DEFAULT '1',
  `used_redemption` tinyint(1) NOT NULL,
  `in_redemption` tinyint(1) NOT NULL,
  `votes_left` int NOT NULL DEFAULT '1',
  PRIMARY KEY (`metamask_id`)
);
CREATE TABLE `polls` (
  `id` int NOT NULL AUTO_INCREMENT,
  `tournament_id` int DEFAULT NULL,
  `round` int DEFAULT NULL,
  `redemption_poll` tinyint(1) NOT NULL,
  `poll_date` date NOT NULL,
  `description` varchar(256) DEFAULT NULL,
  `correct_answer` varchar(256) DEFAULT NULL,
  `end_time` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `tournament_id` (`tournament_id`),
  CONSTRAINT `polls_ibfk_1` FOREIGN KEY (`tournament_id`) REFERENCES `tournaments` (`id`)
);
CREATE TABLE `owners` (
  `user_id` varchar(50) NOT NULL,
  `password` varchar(256) NOT NULL,
  `num_owns` int NOT NULL DEFAULT '1',
  PRIMARY KEY (`user_id`)
);
CREATE TABLE `nfts` (
  `nft_id` varchar(256) NOT NULL,
  `owner` varchar(50) DEFAULT NULL,
  `position` varchar(50) NOT NULL,
  PRIMARY KEY (`nft_id`),
  KEY `owner` (`owner`)
);
CREATE TABLE `admin` (
  `email` VARCHAR(50) NOT NULL,
  `password` VARCHAR(256) NOT NULL,
  `fullname` VARCHAR(50) NOT NULL,
  PRIMARY KEY (`email`)
);

INSERT INTO `admin` (fullname, email, password)
VALUES  ('Joshua Goldstein', 'joshag@umich.edu', 'sha512$a45ffdcc71884853a2cba9e6bc55e812$c739cef1aec45c6e345c8463136dc1ae2fe19963106cf748baf87c7102937aa96928aa1db7fe1d8da6bd343428ff3167f4500c8a61095fb771957b4367868fb8');

-- insets some fake values to test, can be removed later

INSERT INTO `tournaments` (start_date, theme, is_active)
VALUES  ('2022-01-01', 'fake1', '0'),
        ('2022-02-01', 'fake2', '0'),
        ('2022-03-01', 'fake3', '0');

INSERT INTO `polls` (tournament_id, round, poll_date, description, redemption_poll, end_time)
VALUES  ('1', '0', '2022-01-02', "test poll 1", '0', '2022-01-02 12:00'),
        ('1', '1', '2022-01-03', "test poll 2", '0', '2022-01-02 12:00'),
        ('1', '2', '2022-01-04', "test poll 3", '0', '2022-01-02 12:00'),
        ('2', '0', '2022-02-02', "test poll 1", '0', '2022-01-02 12:00'),
        ('2', '1', '2022-02-03', "test poll 2", '0', '2022-01-02 12:00'),
        ('2', '2', '2022-02-04', "test poll 3", '0', '2022-01-02 12:00'),
        ('3', '0', '2022-03-02', "test poll 1", '0', '2022-01-02 12:00'),
        ('3', '1', '2022-03-03', "test poll 2", '0', '2022-01-02 12:00'),
        ('3', '2', '2022-03-04', "test poll 3", '0', '2022-01-02 12:00');

INSERT INTO `owners` (user_id, num_owns)
VALUES  ('0', '4'),
        ('1', '1'),
        ('2', '0');


-- note: make this into a script so tables are destroyued then reset