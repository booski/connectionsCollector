CREATE TABLE `temp` (
       `id` TEXT PRIMARY KEY,
       `author` TEXT,
       `date` TEXT UNIQUE
);
INSERT INTO `temp` (`id`, `author`, `date`) SELECT `id`, `author`, `date` FROM `puzzles`;
DROP TABLE `puzzles`;
UPDATE `temp` SET `date`=NULL WHERE `date` > date();
ALTER TABLE `temp` RENAME TO `puzzles`;
