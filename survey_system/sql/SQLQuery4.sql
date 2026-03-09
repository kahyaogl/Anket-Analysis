
DELETE FROM responses;
DELETE FROM answers;
DELETE FROM questions;
DELETE FROM surveys;

DBCC CHECKIDENT ('responses', RESEED, 0);
DBCC CHECKIDENT ('answers', RESEED, 0);
DBCC CHECKIDENT ('questions', RESEED, 0);
DBCC CHECKIDENT ('surveys', RESEED, 0);