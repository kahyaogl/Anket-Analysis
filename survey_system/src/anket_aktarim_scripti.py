import pandas as pd
import pyodbc
import os
import survey_system.src.nlp_engine as nlp_engine
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    # .env'den bilgileri çek
    server = os.getenv("DB_SERVER")
    database = os.getenv("DB_NAME")
    
    conn_str = (
        f"Driver={{ODBC Driver 17 for SQL Server}};"
        f"Server={server};"
        f"Database={database};"
        "Trusted_Connection=yes;"
    )
    return pyodbc.connect(conn_str)#SQL Server bağlantısı oluşturur


def veritabanini_sifirla(cursor):#cursor (imleç)nesnesi alır ve veritabanındaki tüm anket verilerini siler
    """Sadece anket verilerini temizler, kullanıcıları korur."""
    cursor.execute("DELETE FROM responses")#responses tablosundaki tüm verileri siler
    cursor.execute("DELETE FROM answers")
    cursor.execute("DELETE FROM questions")
    cursor.execute("DELETE FROM surveys")

    cursor.execute("DBCC CHECKIDENT ('responses', RESEED, 0)")
    cursor.execute("DBCC CHECKIDENT ('answers', RESEED, 0)")
    cursor.execute("DBCC CHECKIDENT ('questions', RESEED, 0)")
    cursor.execute("DBCC CHECKIDENT ('surveys', RESEED, 0)")



def anket_yukle_ve_kaydet(file_obj, user_id):
    try:
        conn = get_db_connection()#SQL Server veritabanına bağlanır
        cursor = conn.cursor()#imleç oluşturur

        veritabanini_sifirla(cursor)
        conn.commit()#Değişiklikleri veritabanına kaydeder
                  
        df = pd.read_excel(file_obj)#Excel dosyasını pandas ile okur

        # Dosya adı varsa al
        survey_title = (
            os.path.splitext(file_obj.name)[0]#Dosya adından uzantıyı kaldırarak başlık oluşturur
            if hasattr(file_obj, "name")#Dosya adının olup olmadığını kontrol eder
            else "Yüklenen Anket"#Eğer dosya adı yoksa varsayılan bir başlık kullanır
        )

        # Anket oluştur
        cursor.execute("""
            INSERT INTO surveys (surveys_title, created_by)
            OUTPUT INSERTED.surveys_id
            VALUES (?, ?)
        """, (survey_title, user_id))#surveys tablosuna yeni bir anket kaydı ekler ve eklenen kaydın ID'sini döndürür

        survey_id = cursor.fetchone()[0]#Eklenen anket kaydının ID'sini alır

        all_responses = []#Tüm yanıtları geçici olarak saklamak için bir liste oluşturur

       
        for col in df.columns[1:]:#Excel dosyasındaki her bir sütun için (ilk sütun genellikle kullanıcı bilgisi içerdiği varsayılarak atlanır)
            cursor.execute("""
                INSERT INTO questions (questions_text, surveys_id)
                OUTPUT INSERTED.questions_id
                VALUES (?, ?)
            """, (col, survey_id))#questions tablosuna yeni bir soru kaydı ekler ve eklenen kaydın ID'sini döndürür

            question_id = cursor.fetchone()[0]#Eklenen soru kaydının ID'sini alır

            unique_answers = df[col].dropna().unique()#Sütundaki benzersiz ve boş olmayan yanıtları alır 
            answer_map = {}#Yanıt metinlerini yanıt ID'lerine eşlemek için bir sözlük oluşturur

            for ans_text in unique_answers:
                cursor.execute("""
                    INSERT INTO answers (answers_text, questions_id)
                    OUTPUT INSERTED.answers_id
                    VALUES (?, ?)
                """, (str(ans_text), question_id))

                answer_map[str(ans_text)] = cursor.fetchone()[0]

            for val in df[col]:
                if pd.isna(val):
                    continue

                ans_id = answer_map.get(str(val))

                if ans_id:
                    skor, etiket, _ = nlp_engine.analiz_et(str(val))

                    cursor.execute("""
                        INSERT INTO responses 
                        (users_id, surveys_id, answers_id, sentiment_score, sentiment_label, category_label)
                        OUTPUT INSERTED.responses_id
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (user_id, survey_id, ans_id, skor, etiket, "İşleniyor..."))

                    res_id = cursor.fetchone()[0]
                    all_responses.append({"id": res_id, "text": str(val)})

        conn.commit()

        # Toplu konu analizi
        if all_responses:
            metinler = [r["text"] for r in all_responses]
            topics, topic_labels = nlp_engine.toplu_analiz_yap(metinler)

            for i, res_obj in enumerate(all_responses):
                final_category = topic_labels.get(topics[i])

                cursor.execute("""
                    UPDATE responses 
                    SET category_label = ?
                    WHERE responses_id = ?
                """, (final_category, res_obj["id"]))

            conn.commit()

        conn.close()

        return survey_id, survey_title

    except Exception as e:
        print(f"Yükleme Hatası: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return None, None
def ham_veri_kaydet(metin_listesi, user_id, survey_title=f"Ham Veri Analizi - {datetime.now().strftime('%Y%m%d_%H%M%S')}"):
    conn = None # Bağlantıyı dışarıda tanımlayalım
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Yeni survey oluştur
        cursor.execute("""
            INSERT INTO surveys (surveys_title, created_by)
            OUTPUT INSERTED.surveys_id
            VALUES (?, ?)
        """, (survey_title, user_id))
        survey_id = cursor.fetchone()[0]

        # Tek soru oluştur
        cursor.execute("""
            INSERT INTO questions (questions_text, surveys_id)
            OUTPUT INSERTED.questions_id
            VALUES (?, ?)
        """, ("Genel Geri Bildirim", survey_id))
        question_id = cursor.fetchone()[0]

        all_responses = []

        for text in metin_listesi:
            if not text.strip():
                continue

            # Cevap olarak kaydet
            cursor.execute("""
                INSERT INTO answers (answers_text, questions_id)
                OUTPUT INSERTED.answers_id
                VALUES (?, ?)
            """, (text, question_id))
            answer_id = cursor.fetchone()[0]

            # BERT analizi
            skor, etiket, _ = nlp_engine.analiz_et(text)

            # DİKKAT: topics_id'yi burada 0 olarak gönderiyoruz
            cursor.execute("""
                INSERT INTO responses 
                (users_id, surveys_id, answers_id, topics_id, sentiment_score, sentiment_label, category_label)
                OUTPUT INSERTED.responses_id
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (user_id, survey_id, answer_id, 0, skor, etiket, "İşleniyor..."))

            res_id = cursor.fetchone()[0]
            all_responses.append({"id": res_id, "text": text})

        # Döngü bitti, buraya kadar olanları kaydet (Duygu analizleri garantiye alınsın)
        conn.commit()

        # Toplu konu analizi (Gemini)
        if all_responses:
            try:
                metinler = [r["text"] for r in all_responses]
                topics, topic_labels = nlp_engine.toplu_analiz_yap(metinler)

                for i, res_obj in enumerate(all_responses):
                    final_category = topic_labels.get(topics[i], "Genel")

                    cursor.execute("""
                        UPDATE responses 
                        SET category_label = ?
                        WHERE responses_id = ?
                    """, (final_category, res_obj["id"]))

                conn.commit()
            except Exception as e:
                print(f"Konu Analizi Hatası (Gemini Atlandı): {e}")

        return survey_id, survey_title

    except Exception as e:
        print(f"Genel Kayıt Hatası: {e}")
        if conn:
            conn.rollback()
        return None, None
    finally:
        if conn:
            conn.close()