import os
import pyodbc
import pandas as pd
from fpdf import FPDF
import datetime
from dotenv import load_dotenv

# Kendi yazdığın grafik modülü
import grafik_olusturma 

# .env dosyasındaki değişkenleri (DB_SERVER, DB_NAME vb.) yükle
load_dotenv()

def get_db_connection():
    """Veritabanı bağlantısını .env dosyasındaki bilgilerle kurar."""
    server = os.getenv("DB_SERVER")
    database = os.getenv("DB_NAME")
    
    conn_str = (
        f"Driver={{ODBC Driver 17 for SQL Server}};"
        f"Server={server};"
        f"Database={database};"
        "Trusted_Connection=yes;"
    )
    return pyodbc.connect(conn_str)

def create_pro_report(survey_id):
    """Anket verilerini çekerek profesyonel bir PDF raporu oluşturur."""
    
    # 1. Klasör ve Dosya Yolu Ayarları
    base_path = os.path.dirname(os.path.abspath(__file__))
    temp_dir = os.path.join(base_path, "temp_charts")
    os.makedirs(temp_dir, exist_ok=True)
    
    # Font yolları (fonts klasörü altında olmalı)
    font_path = os.path.join(base_path, "fonts", "arial.ttf")
    font_bold_path = os.path.join(base_path, "fonts", "arialbd.ttf")

    # 2. Veritabanından Veri Çekme
    try:
        conn = get_db_connection()
        query = """
            SELECT surveys_title, questions_id, questions_text,
                   answers_text, answer_count,
                   sentiment_label, category_label
            FROM View_SurveyReport
            WHERE surveys_id = ?
        """
        df = pd.read_sql(query, conn, params=[survey_id])
        conn.close()

        if df.empty:
            print(f"Hata: {survey_id} ID'li anket için veri bulunamadı.")
            return None
            
    except Exception as e:
        print(f"Veritabanı hatası: {e}")
        return None

    # 3. PDF Başlatma ve Font Ayarları
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    if os.path.exists(font_path):
        pdf.add_font("ArialTR", "", font_path, unicode=True)
        pdf.set_font("ArialTR", "", 12)
    else:
        pdf.set_font("Arial", "", 12)
        print("Uyarı: Arial.ttf bulunamadı, varsayılan font kullanılıyor.")

    if os.path.exists(font_bold_path):
        pdf.add_font("ArialTR", "B", font_bold_path, unicode=True)

    # --- KAPAK SAYFASI ---
    pdf.add_page()
    survey_title = df['surveys_title'].iloc[0]
    pdf.set_font("ArialTR", "B", 22)
    pdf.set_text_color(44, 62, 80)
    pdf.ln(40)
    pdf.cell(190, 20, "ANKET ANALİZ RAPORU", ln=True, align="C")
    pdf.set_font("ArialTR", "B", 16)
    pdf.set_text_color(242, 122, 26) # ACEY Turuncusu
    pdf.multi_cell(190, 15, survey_title, align="C")
    pdf.ln(20)
    pdf.set_font("ArialTR", "", 12)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(190, 10, f"Rapor Oluşturma Tarihi: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}", ln=True, align="C")

    # --- EXECUTIVE SUMMARY ---
    pdf.add_page()
    pdf.set_font("ArialTR", "B", 18)
    pdf.cell(190, 12, "Yönetici Özeti (Executive Summary)", ln=True, align="C")
    pdf.ln(8)

    total_responses = df["answer_count"].sum()
    sent_counts = df.groupby("sentiment_label")["answer_count"].sum()
    sent_total = sent_counts.sum() if not sent_counts.empty else 1

    pdf.set_font("ArialTR", "", 12)
    pdf.cell(190, 8, f"Toplam Katılımcı Yanıtı: {int(total_responses)}", ln=True)
    pdf.ln(5)
    pdf.set_font("ArialTR", "B", 12)
    pdf.cell(190, 8, "Genel Duygu Dağılımı:", ln=True)
    pdf.set_font("ArialTR", "", 12)
    for label, count in sent_counts.items():
        percent = round((count / sent_total) * 100, 1)
        pdf.cell(190, 8, f"- {label} yanıt: {int(count)} (%{percent})", ln=True)

    top_categories = df.groupby("category_label")["answer_count"].sum().sort_values(ascending=False).head(3)
    pdf.ln(5)
    pdf.set_font("ArialTR", "B", 12)
    pdf.cell(190, 8, "Öne Çıkan Kritik Konular:", ln=True)
    pdf.set_font("ArialTR", "", 12)
    pdf.multi_cell(190, 8, f"{', '.join(top_categories.index.astype(str))}")

    # --- GENEL DAĞILIMLAR (NİCEL SORULAR) ---
    categorical_q_ids = grafik_olusturma.find_categorical_questions(df)
    if categorical_q_ids:
        pdf.add_page()
        pdf.set_font("ArialTR", "B", 18)
        pdf.cell(190, 12, "Genel Anket Dağılımları", ln=True, align="C")
        pdf.ln(8)

        y_position = 40
        for q_id in categorical_q_ids:
            q_data = df[df["questions_id"] == q_id]
            question_title = q_data["questions_text"].iloc[0]
            chart_file = os.path.join(temp_dir, f"dist_{q_id}.png")
            
            grafik_olusturma.save_question_distribution_chart_by_id(df, q_id, chart_file)
            
            if os.path.exists(chart_file):
                if y_position > 220:
                    pdf.add_page()
                    y_position = 20
                
                pdf.set_font("ArialTR", "B", 11)
                pdf.text(15, y_position, question_title[:80] + "..." if len(question_title) > 80 else question_title)
                pdf.image(chart_file, x=15, y=y_position + 2, w=170)
                y_position += 85

    # --- HER SORU DETAYLARI ---
    for q_id in df["questions_id"].unique():
        q_data = df[df["questions_id"] == q_id]
        q_text = q_data["questions_text"].iloc[0]
        pdf.add_page()

        pdf.set_font("ArialTR", "B", 14)
        pdf.set_fill_color(245, 245, 245)
        pdf.multi_cell(190, 10, f"Soru: {q_text}", fill=True, align='L')
        pdf.ln(5)

        # Grafik Ekleme
        chart_filename = os.path.join(temp_dir, f"q_{q_id}_{survey_id}.png")
        grafik_olusturma.save_combined_chart(q_text, q_data, chart_filename)
        
        if os.path.exists(chart_filename):
            pdf.image(chart_filename, x=10, y=pdf.get_y(), w=190)
            pdf.set_y(pdf.get_y() + 105)
        else:
            pdf.set_font("ArialTR", "I", 11)
            pdf.cell(190, 8, "Bu soru için görsel veri bulunamadı.", ln=True)

        # Tablo (Cevap Sayıları)
        pdf.ln(5)
        pdf.set_font("ArialTR", "B", 11)
        pdf.set_fill_color(242, 122, 26) # Turuncu başlık
        pdf.set_text_color(255, 255, 255)
        pdf.cell(140, 8, "Cevap Seçeneği", 1, 0, 'C', True)
        pdf.cell(50, 8, "Katılımcı Sayısı", 1, 1, 'C', True)
        
        pdf.set_font("ArialTR", "", 10)
        pdf.set_text_color(0, 0, 0)
        
        answer_counts = q_data.groupby("answers_text")["answer_count"].sum().reset_index()
        for _, row in answer_counts.iterrows():
            clean_answer = str(row['answers_text']).replace('\n', ' ')
            if len(clean_answer) > 75: clean_answer = clean_answer[:72] + "..."
            pdf.cell(140, 8, clean_answer, 1, 0, 'L')
            pdf.cell(50, 8, str(int(row['answer_count'])), 1, 1, 'C')

    # --- YAPAY ZEKA ANALİZ SONUÇLARI ---
    pdf.add_page()
    pdf.set_font("ArialTR", "B", 20)
    pdf.set_text_color(44, 62, 80)
    pdf.cell(190, 20, "Yapay Zeka (AI) Detay Analizi", ln=True, align="C")
    pdf.ln(10)

    # Sentiment Özeti
    pdf.set_font("ArialTR", "B", 14)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(190, 10, "Duygu Analizi (BERT) Kırılımı:", ln=True)
    pdf.set_font("ArialTR", "", 12)
    sent_counts = df.groupby("sentiment_label")["answer_count"].sum().dropna()
    total_sent = sent_counts.sum() if not sent_counts.empty else 1
    for label, count in sent_counts.items():
        percent = round((count / total_sent) * 100, 1)
        pdf.cell(190, 8, f"- {label}: {int(count)} Yanıt (%{percent})", ln=True)

    pdf.ln(10)
    # Kategori Özeti
    pdf.set_font("ArialTR", "B", 14)
    pdf.cell(190, 10, "Akıllı Konu Etiketleri (Gemini):", ln=True)
    cat_counts = df.groupby("category_label")["answer_count"].sum().dropna().sort_values(ascending=False)
    total_cat = cat_counts.sum() if not cat_counts.empty else 1
    
    pdf.set_fill_color(230, 230, 230)
    pdf.set_font("ArialTR", "B", 11)
    pdf.cell(140, 10, "Yapay Zeka Tarafından Belirlenen Kategori", 1, 0, "L", True)
    pdf.cell(50, 10, "Yoğunluk (%)", 1, 1, "C", True)
    
    pdf.set_font("ArialTR", "", 11)
    for cat, count in cat_counts.items():
        percent = round((count / total_cat) * 100, 1)
        pdf.cell(140, 10, f" {cat}", 1, 0, "L")
        pdf.cell(50, 10, f"%{percent}", 1, 1, "C")

    # Çıktı Alma
    output_name = f"ACEY_Analiz_Raporu_{survey_id}.pdf"
    pdf.output(output_name)
    return output_name