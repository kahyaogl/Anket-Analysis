-- fulltext temizlendi
DROP TABLE IF EXISTS responses;
DROP TABLE IF EXISTS answers;
DROP TABLE IF EXISTS questions;
DROP TABLE IF EXISTS surveys;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS survey_topics;


IF EXISTS (SELECT * FROM sys.fulltext_catalogs WHERE name = 'SurveyCatalog')
    DROP FULLTEXT CATALOG SurveyCatalog;
GO



CREATE TABLE users (
    users_id INT IDENTITY(1,1),--kullanıcı id'si, otomatik artan
    users_name VARCHAR(100),--kullanıcı adı
    users_mail VARCHAR(100) NOT NULL UNIQUE,--e-posta adresi benzersiz olmalı
    users_password VARCHAR(255) NOT NULL,--şifrelenmiş olarak saklanmalı
    users_role VARCHAR(50) NOT NULL DEFAULT 'users',--kullanıcı rolü (admin/user)
    users_created_at DATETIME2 DEFAULT SYSDATETIME(),--otomatik arih ekleme

    CONSTRAINT PK_users PRIMARY KEY (users_id)--anahtar
);
GO

-- SQLQuery1.sql içinde ilgili kısmı şu şekilde güncelle:
CREATE TABLE surveys (
    surveys_id INT IDENTITY(1,1),
    surveys_title VARCHAR(200) NOT NULL ,
    surveys_description NVARCHAR(MAX) NULL, -- NOT NULL kaldırıldı
    surveys_created_at DATETIME2 DEFAULT SYSDATETIME(),
    created_by INT NOT NULL,

    CONSTRAINT PK_surveys PRIMARY KEY (surveys_id),
    CONSTRAINT fk_surveys_users FOREIGN KEY (created_by) REFERENCES users(users_id) ON DELETE CASCADE
);
GO

CREATE TABLE questions (
    questions_id INT IDENTITY(1,1),
    questions_text NVARCHAR(MAX) NOT NULL,
    surveys_id INT NOT NULL,

    CONSTRAINT PK_questions PRIMARY KEY (questions_id),

    CONSTRAINT fk_questions_surveys
        FOREIGN KEY (surveys_id)
        REFERENCES surveys(surveys_id)
        ON DELETE CASCADE--anket silindiğinde sorular da silinsin
);
GO

CREATE TABLE answers (
    answers_id INT IDENTITY(1,1),
    answers_text NVARCHAR(MAX) NOT NULL,
    questions_id INT NOT NULL,

    CONSTRAINT PK_answers PRIMARY KEY (answers_id),

    CONSTRAINT fk_answers_questions
        FOREIGN KEY (questions_id)
        REFERENCES questions(questions_id)
        ON DELETE CASCADE--anket silindiğinde cevaplar da silinsin
);
GO


CREATE TABLE responses (--anket yanıtları
    responses_id INT IDENTITY(1,1),--yanıt id'si, otomatik artan
    users_id INT NOT NULL,
    surveys_id INT NOT NULL,
    answers_id INT NOT NULL,
	topics_id INT NOT NULL,

    responses_created_at DATETIME DEFAULT GETDATE(),

    CONSTRAINT PK_responses PRIMARY KEY (responses_id),

    CONSTRAINT fk_responses_users--foreign key tanımı
        FOREIGN KEY (users_id)
        REFERENCES users(users_id),

    CONSTRAINT fk_responses_surveys
        FOREIGN KEY (surveys_id)
        REFERENCES surveys(surveys_id),

    CONSTRAINT fk_responses_answers
        FOREIGN KEY (answers_id)
        REFERENCES answers(answers_id)
);
GO
CREATE TABLE survey_topics (
    topic_id INT,
    surveys_id INT,
    topic_name NVARCHAR(200), -- LLM'den gelen isim: "Kargo Gecikmeleri" gibi
    top_words NVARCHAR(MAX)   -- Modelin bulduğu anahtar kelimeler
);





CREATE INDEX idx_responses_users_id ON responses(users_id);--kullanıcıya göre indeks
CREATE INDEX idx_responses_surveys_id ON responses(surveys_id);--ankete göre indeks
CREATE INDEX idx_responses_answers_id ON responses(answers_id);--cevaba göre indeks

CREATE INDEX idx_users_created_at ON users(users_created_at);
CREATE INDEX idx_surveys_created_at ON surveys(surveys_created_at);
CREATE INDEX idx_responses_created_at ON responses(responses_created_at);

CREATE INDEX idx_users_name ON users(users_name);
CREATE INDEX idx_users_role ON users(users_role);
GO

USE SurveyDB;
GO

-- Responses tablosuna BERT çıktıları için yeni sütunlar ekleyelim
ALTER TABLE responses
ADD 
    sentiment_score DECIMAL(5, 4) NULL, -- 0.9999 gibi hassas skorlar için
    sentiment_label VARCHAR(50) NULL,    -- "Pozitif", "Negatif" gibi etiketler için
    category_label NVARCHAR(200) NULL;   -- "Fiyat", "Hizmet kalitesi" vb. için
GO










