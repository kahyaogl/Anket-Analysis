import streamlit as st
import os
import pyodbc
import pandas as pd
import plotly.express as px




from dotenv import load_dotenv

from survey_system.src import anket_aktarim_scripti
from survey_system.src import rapor_olusturucu
from survey_system.src import nlp_engine
from survey_system.src import grafik_olusturma
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
    return pyodbc.connect(conn_str)
st.set_page_config(

    page_title="ACEY | Anket Analiz Paneli",
    page_icon="📊",
    layout="wide"

)
st.markdown("""

<style>



@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;800&display=swap');



html, body, [class*="css"]  {

    font-family: 'Poppins', sans-serif;

}



.stApp {

    background: linear-gradient(135deg, #f5f7fa, #eef2f7);

}



/* HERO */

.hero-container {

    background: linear-gradient(135deg, #F27A1A, #FFB600);

    padding: 90px;

    border-radius: 0px 0px 60px 60px;

    text-align: center;

    color: white;

    margin-bottom: 50px;

    box-shadow: 0 15px 40px rgba(0,0,0,0.1);

}



/* CARDS */

.data-card {

    background: rgba(255, 255, 255, 0.85);

    backdrop-filter: blur(15px);

    padding: 30px;

    border-radius: 20px;

    box-shadow: 0 10px 30px rgba(0,0,0,0.08);

    transition: 0.3s;

    text-align: center;

}



.data-card:hover {

    transform: translateY(-8px);

}



/* METRIC BOX */

.metric-box {

    background: white;

    padding: 25px;

    border-radius: 18px;

    box-shadow: 0 10px 25px rgba(0,0,0,0.07);

    text-align: center;

}



/* BUTTON STYLE */

div.stButton > button {

    background: linear-gradient(45deg, #F27A1A, #FFB600);

    color: white !important;

    border-radius: 30px !important;

    padding: 12px 35px !important;

    font-weight: 600 !important;

    border: none !important;

    transition: 0.3s;

}



div.stButton > button:hover {
    transform: scale(1.05);
    box-shadow: 0 8px 20px rgba(242,122,26,0.4);

}



/* TAB STYLE */

button[data-baseweb="tab"] {
    font-weight: 600;
    font-size: 16px;
    border-radius: 10px;

}



</style>

""", unsafe_allow_html=True)





# Hero bölümünü bu şekilde güncellersen HTML etiketleri düzgün çalışacaktır
st.markdown(f"""
<div class="hero-container">
    <h1 style='font-size: 64px; font-weight: 800; margin: 0;'>ACEY</h1>
    <p style='font-size: 22px;'>Profesyonel Anket Analiz Platformu</p>
    <div style='background:white; color:#F27A1A; 
                display:inline-block; padding:10px 25px; 
                border-radius:30px; font-weight:600; margin-top: 15px;'>
        Anket Raporlamanın En Akıllı Yolu
    </div>
</div>
""", unsafe_allow_html=True) # <-- Bu parametre hayati önem taşıyor!



tab1, tab2 = st.tabs(["🏠 ANA SAYFA", "📥 ANKET YÜKLE"])

with tab1:
    st.subheader("🔐 Kullanıcı Girişi ve Kayıt")

    if 'current_user_id' not in st.session_state:
        choice = st.radio(
            label="AuthChoice", 
            options=["Giriş Yap", "Yeni Kayıt Oluştur"], 
            horizontal=True,
            label_visibility="collapsed"
        )

        with st.form("auth_form", border=False):
            st.markdown(f"### {choice}")
            u_mail = st.text_input("E-posta Adresiniz", placeholder="example@mail.com")

            if choice == "Yeni Kayıt Oluştur":
                u_name = st.text_input("Ad Soyad", placeholder="Adınız ve Soyadınız")
                submit_auth = st.form_submit_button("Hesap Oluştur")
            else:
                u_name = None
                submit_auth = st.form_submit_button("Sisteme Giriş")

            if submit_auth:
                if u_mail:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("SELECT users_id, users_name FROM users WHERE users_mail = ?", (u_mail,))
                    user = cursor.fetchone()

                    if choice == "Giriş Yap":
                        if user:
                            st.session_state['current_user_id'] = user[0]
                            st.session_state['current_user_name'] = user[1]
                            st.success(f"Tekrar hoş geldin, {user[1]}!")
                            st.rerun()
                        else:
                            st.error("Kullanıcı bulunamadı.")
                    else:
                        if user:
                            st.warning("Bu e-posta zaten kayıtlı.")
                        elif u_name:
                            cursor.execute("INSERT INTO users (users_name, users_mail, users_password) OUTPUT INSERTED.users_id VALUES (?, ?, '1234')", (u_name, u_mail))
                            st.session_state['current_user_id'] = cursor.fetchone()[0]
                            st.session_state['current_user_name'] = u_name
                            conn.commit()
                            st.rerun()
                    conn.close()
    else:
        st.success(f"✅ Giriş Yapıldı: {st.session_state['current_user_name']}")
        if st.button("Çıkış Yap"):
            del st.session_state['current_user_id']
            del st.session_state['current_user_name']
            st.rerun()
        
    # ... (Mevcut Giriş/Kayıt Kodların) ...
    if 'current_user_id' in st.session_state:
        st.divider()
        st.markdown(f"### 📂 Geçmiş Anketleriniz ve Raporlarınız")
        
        try:
            conn = get_db_connection()
            # Kullanıcının anketlerini tarihe göre azalan sırada getiriyoruz
            query = """
                SELECT surveys_id, surveys_title, surveys_created_at 
                FROM surveys 
                WHERE created_by = ? 
                ORDER BY surveys_created_at DESC
            """
            user_surveys = pd.read_sql(query, conn, params=[st.session_state['current_user_id']])
            conn.close()

            if not user_surveys.empty:
                # Daha şık bir görünüm için tarih formatını düzenleyelim
                user_surveys['created_at'] = pd.to_datetime(user_surveys['created_at']).dt.strftime('%d.%m.%Y %H:%M')
                
                # Tabloyu gösteriyoruz
                st.dataframe(
                    user_surveys,
                    column_config={
                        "surveys_id": "ID",
                        "surveys_title": "Anket Başlığı",
                        "created_at": "Oluşturulma Tarihi"
                    },
                    hide_index=True,
                    use_container_width=True
                )

                # Seçim kutusu ile eski bir anketi tekrar yükleme özelliği
                selected_survey = st.selectbox(
                    "İncelemek istediğiniz anketi seçin:",
                    options=user_surveys['surveys_title'].tolist(),
                    index=None,
                    placeholder="Anket seçiniz..."
                )

                if selected_survey:
                    # Seçilen anketin ID'sini bulup session_state'e aktaralım
                    sid = user_surveys[user_surveys['surveys_title'] == selected_survey]['surveys_id'].values[0]
                    if st.button("Analizi Görüntüle"):
                        st.session_state['last_id'] = int(sid)
                        st.session_state['last_title'] = selected_survey
                        st.success(f"{selected_survey} verileri yüklendi! Lütfen 'Anket Yükle' sekmesine bakın.")
                        # Opsiyonel: st.rerun() ile sayfayı tazeleyebilirsin
            else:
                st.info("Henüz bir anket oluşturmamışsınız. 'Anket Yükle' sekmesinden başlayabilirsiniz.")

        except Exception as e:
            st.error(f"Veriler yüklenirken bir hata oluştu: {e}")
   

with tab2:
    st.subheader("📥 Anket Yükle")
    uploaded_file = st.file_uploader("Excel dosyanızı seçin", type=["xlsx"])
    bulk_text = st.text_area("Geri bildirimleri satır satır yapıştırın", height=150)

    if st.button("Analiz Et"):
        if 'current_user_id' not in st.session_state:
            st.error("Lütfen önce giriş yapın!")
        else:
            metinler = []
            if uploaded_file:
                df = pd.read_excel(uploaded_file)
                metinler = df.iloc[:, 0].dropna().astype(str).tolist()
                st.session_state['last_title'] = uploaded_file.name
            elif bulk_text.strip():
                metinler = bulk_text.split("\n")
                st.session_state['last_title'] = "Yorumların Analizi"

            if metinler:
                with st.spinner("Analiz ediliyor..."):
                    sid, title = anket_aktarim_scripti.ham_veri_kaydet(metinler, st.session_state['current_user_id'])
                    st.session_state['last_id'] = sid
                    st.success("Analiz tamamlandı!")
                    st.rerun()

    # --- ANALİZ SONUÇLARI BÖLÜMÜ ---
    if st.session_state.get('last_id'):
        survey_id = st.session_state['last_id']
        raw_title = st.session_state.get('last_title', 'Analiz')
        
        # Başlık Temizleme
        if raw_title.lower().endswith(('.xlsx', '.xls', '.csv')):
            display_title = os.path.splitext(raw_title)[0]
        else:
            display_title = "Yorumların Analizi"

        st.divider()
        st.subheader(f" Analiz Sonuçları: {display_title}")

        conn = get_db_connection()
        df_sent = pd.read_sql("SELECT sentiment_label, COUNT(*) as adet FROM responses WHERE surveys_id = ? GROUP BY sentiment_label", conn, params=[survey_id])
        df_ozet = pd.read_sql("SELECT category_label, COUNT(*) as adet FROM responses WHERE surveys_id = ? GROUP BY category_label", conn, params=[survey_id])
        conn.close()

        if not df_sent.empty or not df_ozet.empty:
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("####  Duygu Dağılımı")
                fig_pie = px.pie(df_sent, values='adet', names='sentiment_label', hole=0.4,
                                 color='sentiment_label', 
                                 color_discrete_map={'Pozitif':'#2ecc71', 'Negatif':'#e74c3c', 'Nötr':'#f1c40f'})
                st.plotly_chart(fig_pie, use_container_width=True)
            with c2:
                st.markdown("####  Öne Çıkan Konular")
                fig_bar = px.bar(df_ozet, x='adet', y='category_label', orientation='h', color='category_label')
                st.plotly_chart(fig_bar, use_container_width=True)

            if st.button(" PDF RAPORU OLUŞTUR"):
                path = rapor_olusturucu.create_pro_report(survey_id)
                if path:
                    with open(path, "rb") as f:
                        st.download_button("Raporu İndir", f, file_name=f"Analiz_{survey_id}.pdf")
        else:
            st.info("Henüz veri bulunamadı.")