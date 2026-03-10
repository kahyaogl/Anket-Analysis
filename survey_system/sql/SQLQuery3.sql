--Tüm anketlerde,
--her soru için,
--her cevabın
--kaç kez seçildiğini göstermekTüm anketlerde,
--her soru için,
--her cevabın
--kaç kez seçildiğini göstermek
SELECT * FROM users
SELECT * FROM surveys;
SELECT * FROM questions;
SELECT * FROM answers;

-- Kim?
--Hangi ankete?
--Hangi soruya?
--Ne cevap vermiş?
--Ne zaman?
SELECT 
    u.users_name,
    s.surveys_title,
    q.questions_text,
    a.answers_text,
    r.responses_created_at
FROM responses r
JOIN users u      ON r.users_id = u.users_id--  yanıt veren kullanıcı ile users tablosunu birleştir
JOIN surveys s    ON r.surveys_id = s.surveys_id--  yanıt verilen anket ile surveys tablosunu birleştir
JOIN answers a    ON r.answers_id = a.answers_id--  verilen cevaba göre answers tablosunu birleştir
JOIN questions q  ON a.questions_id = q.questions_id;--  cevaba göre questions tablosunu birleştir
USE SurveyDB;
GO

SELECT
    s.surveys_title,
    q.questions_text,
    a.answers_text,
    x.answer_count
FROM (
    SELECT
        r.surveys_id,
        q.questions_id,
        a.answers_id,
        COUNT(*) AS answer_count
    FROM responses r
    JOIN answers a   ON r.answers_id = a.answers_id
    JOIN questions q ON a.questions_id = q.questions_id
    GROUP BY
        r.surveys_id,
        q.questions_id,
        a.answers_id
) x
JOIN surveys s   ON x.surveys_id = s.surveys_id
JOIN questions q ON x.questions_id = q.questions_id
JOIN answers a   ON x.answers_id = a.answers_id
ORDER BY
    s.surveys_id,
    q.questions_id;
--anket,soru,cevap ve cevap sayısını getiren sorgu, sonuçları anket id'sine göre sıralar

SELECT
    s.surveys_title,
    q.questions_text,
    a.answers_text,
    x.answer_count
FROM (
    SELECT
        r.surveys_id,
        q.questions_id,
        a.answers_id,
        COUNT(*) AS answer_count
    FROM responses r
    JOIN answers a   ON r.answers_id = a.answers_id
    JOIN questions q ON a.questions_id = q.questions_id
    GROUP BY
        r.surveys_id,
        q.questions_id,
        a.answers_id
) x
JOIN surveys s   ON x.surveys_id = s.surveys_id
JOIN questions q ON x.questions_id = q.questions_id
JOIN answers a   ON x.answers_id = a.answers_id
ORDER BY
    s.surveys_id,
    q.questions_id;
--anket başlığı, soru metni, cevap metni ve cevap sayısını getiren sorgu, sonuçları soru id'sine göre sıralar

--hiç seçilmeyen cevapları da göstermek için LEFT JOIN kullanarak sorguyu güncelleyelim
SELECT
    s.surveys_title,
    q.questions_text,
    a.answers_text,
    COUNT(r.responses_id) AS answer_count
FROM surveys s
JOIN questions q ON s.surveys_id = q.surveys_id
JOIN answers a   ON q.questions_id = a.questions_id
LEFT JOIN responses r 
       ON r.answers_id = a.answers_id
      AND r.surveys_id = s.surveys_id
WHERE s.surveys_id = 1
GROUP BY
    s.surveys_title,
    q.questions_text,
    a.answers_text
ORDER BY q.questions_text;


DROP VIEW IF EXISTS View_SurveyReport;
GO

CREATE VIEW View_SurveyReport AS
SELECT
    s.surveys_id,
    s.surveys_title,
    q.questions_id,
    q.questions_text,
    a.answers_id,
    a.answers_text,
    COUNT(r.responses_id) AS answer_count,
    r.sentiment_label,
    r.category_label
FROM surveys s
JOIN questions q ON s.surveys_id = q.surveys_id
JOIN answers a   ON q.questions_id = a.questions_id
LEFT JOIN responses r 
       ON r.answers_id = a.answers_id
       AND r.surveys_id = s.surveys_id
GROUP BY
    s.surveys_id,
    s.surveys_title,
    q.questions_id,
    q.questions_text,
    a.answers_id,
    a.answers_text,
    r.sentiment_label,
    r.category_label;
GO
