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
CREATE TABLE `polls` (
  `poll_date` date NOT NULL,
  `description` varchar(256) DEFAULT NULL,
  `correct_answer` varchar(256) DEFAULT NULL,
  `end_time` datetime NOT NULL,
  PRIMARY KEY (`poll_date`)
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