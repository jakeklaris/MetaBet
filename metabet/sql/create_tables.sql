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