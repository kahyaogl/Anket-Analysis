USE SurveyDB;
GO

IF OBJECT_ID('responses', 'U') IS NOT NULL DROP TABLE responses;
IF OBJECT_ID('answers', 'U') IS NOT NULL DROP TABLE answers;
IF OBJECT_ID('questions', 'U') IS NOT NULL DROP TABLE questions;
IF OBJECT_ID('surveys', 'U') IS NOT NULL DROP TABLE surveys;



