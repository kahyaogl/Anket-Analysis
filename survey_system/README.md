ACEY: Yapay Zeka Destekli Uçtan Uca Anket Analiz Sistemi
ACEY, geleneksel anket yöntemlerini modern Doğal Dil İşleme (NLP) teknikleriyle birleştiren, ham veriden profesyonel PDF raporuna kadar tüm süreci otomatize eden bir karar destek sistemidir.

 Öne Çıkan Özellikler
Duygu Analizi (Sentiment Analysis): savasy/bert-base-turkish-sentiment-cased modeli kullanılarak anket yorumları Pozitif, Negatif ve Nötr olarak sınıflandırılır.

Akıllı Konu Etiketleme: BERTopic ve Google Gemini API entegrasyonu ile binlerce yorum içinden ana temalar (Kargo, Fiyat, Memnuniyet vb.) otomatik olarak belirlenir ve isimlendirilir.

İnteraktif Dashboard: Streamlit tabanlı arayüz sayesinde veriler anlık olarak filtrelenebilir ve görselleştirilebilir.

Kurumsal Raporlama: FPDF kütüphanesi ile analiz sonuçları, grafikler ve AI özetleri içeren profesyonel PDF raporları tek tıkla oluşturulur.

İlişkisel Veri Yönetimi: MS SQL Server mimarisi üzerine kurulu, performans odaklı veritabanı yapısı.

🛠️ Teknoloji Yığını
Dil: Python 3.x

NLP Modelleri: BERT (Sentiment), BERTopic (Clustering), Gemini Pro (LLM)

Veritabanı: Microsoft SQL Server

Arayüz: Streamlit

Görselleştirme: Plotly, Matplotlib

Raporlama: FPDF

🚀 Kurulum ve Çalıştırma
Depoyu Klonlayın:

Bash
git clone https://github.com/ceylankahyaoglu/ACEY.git
cd ACEY
Gerekli Kütüphaneleri Yükleyin:

Bash
pip install -r requirements.txt
Ortam Değişkenlerini Ayarlayın:
.env dosyasını oluşturun ve bilgilerinizi girin:

Plaintext
DB_SERVER=YOUR_SERVER_NAME
DB_NAME=SurveyDB
GEMINI_API_KEY=YOUR_API_KEY
Uygulamayı Başlatın:

Bash
streamlit run src/web_panel.py
📂 Proje Yapısı
Plaintext
ACEY/
├── src/                # Uygulama kaynak kodları
├── sql/                # Veritabanı şemaları ve View'lar
├── fonts/              # PDF için Türkçe karakter destekli fontlar
├── assets/             # Ekran görüntüleri ve logolar
├── .env                # Gizli yapılandırma dosyası (Yüklenmez!)
├── .gitignore          # Git dışı bırakılacaklar
└── requirements.txt    # Bağımlılık listesi