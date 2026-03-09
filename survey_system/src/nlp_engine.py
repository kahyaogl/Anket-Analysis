import os
import torch

from transformers import pipeline
from bertopic import BERTopic
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.cluster import KMeans
import google.generativeai as genai
import bertopic
print(bertopic.__version__)



device = 0 if torch.cuda.is_available() else -1#PyTorch'un CUDA destekli bir GPU'nun mevcut olup olmadığını kontrol eder ve uygun cihazı belirler. 

import os
from dotenv import load_dotenv
import google.generativeai as genai

# .env dosyasındaki verileri yükle
load_dotenv()

# API Key'i güvenli bir şekilde al
api_key = os.getenv("GEMINI_API_KEY")

# Gemini'yi bu key ile yapılandır
genai.configure(api_key=api_key)

sentiment_model = pipeline(
    "sentiment-analysis",
    model="savasy/bert-base-turkish-sentiment-cased",
    device=device
)



embedding_model = SentenceTransformer(
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)



turkish_stopwords = [
    "ve", "bir", "bu", "çok", "da", "de", "için", "ile",
    "ama", "fakat", "ancak", "mi", "mı", "mu", "mü",
    "daha", "gibi", "şu", "o", "ben", "biz"
]
# CountVectorizer için Türkçe stopword listesi oluşturulur. Bu kelimeler analiz sırasında göz ardı edilir, böylece daha anlamlı konular ortaya çıkar.
vectorizer_model = CountVectorizer(
    stop_words=turkish_stopwords
)



def create_topic_model(data_size):
    # 1. Kümeleme modelini tanımla
    cluster_model = KMeans(#KMeans algoritması kullanarak metinleri kümelendirir. n_clusters parametresi, oluşturulacak küme sayısını belirler. random_state ise sonuçların tekrarlanabilir olması için sabitlenir.
        n_clusters=6,
        random_state=42#Rastgele durumun sabitlenmesi, aynı veri ve parametrelerle her çalıştırıldığında aynı sonuçların elde edilmesini sağlar.
    )
# 2. BERTopic modelini oluşturur
    topic_model = BERTopic(
        embedding_model=embedding_model,
        vectorizer_model=vectorizer_model,
        calculate_probabilities=False,
        verbose=False
    )  

    # 3. Kümeleme modelini manuel olarak ata
    topic_model.hdbscan_model = cluster_model # BERTopic arka planda KMeans'i de bu isimle tutar
    
    return topic_model




genai.configure(api_key=api_key)



def get_gemini_model():
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        model.generate_content("test")
        return model
    except Exception as e:
        print("Gemini bağlantı hatası:")
        return None


gemini_model = get_gemini_model()



def analiz_et(metin):
    try:
        result = sentiment_model(metin[:512])[0]
        label = result["label"].lower()
        score = result["score"]

        if "pos" in label:
            return score, "Pozitif", label
        elif "neg" in label:
            return score, "Negatif", label
        else:
            return score, "Nötr", label

    except Exception as e:
        print("BERT hatası:", e)
        return 0, "Nötr", "neutral"



def konu_basligi_olustur(anahtar_kelimeler):

    if not gemini_model:
        return "Müşteri Geri Bildirimi"

    prompt = f"""
    Aşağıdaki kelimelerin temsil ettiği ana müşteri geri bildirim konusuna
    maksimum 3 kelimelik profesyonel Türkçe başlık üret.
    Kelimeler: {anahtar_kelimeler}
    Sadece başlığı yaz.
    """

    try:
        response = gemini_model.generate_content(prompt)

        if hasattr(response, "text") and response.text:
            return response.text.strip().replace('"', '')
        else:
            return "Müşteri Geri Bildirimi"

    except Exception as e:
        print("Gemini hata:", e)
        return "Müşteri Geri Bildirimi"



def toplu_analiz_yap(metin_listesi):

    if len(metin_listesi) < 3:
        return [0] * len(metin_listesi), {0: "Yetersiz Veri"}

    try:
        temiz_metinler = [x.lower().strip() for x in metin_listesi]

        topic_model = create_topic_model(len(temiz_metinler))
        topics, _ = topic_model.fit_transform(temiz_metinler)

        # DEBUG
        print("Topic dağılımı:",
              {t: list(topics).count(t) for t in set(topics)})

        unique_topics = set(topics)
        topic_labels = {}

        for t in unique_topics:

            raw_words = topic_model.get_topic(t)

            if raw_words:
                words = [word for word, _ in raw_words[:6]]
                topic_labels[t] = konu_basligi_olustur(", ".join(words))
            else:
                topic_labels[t] = "Tanımlanamayan"

        return topics, topic_labels

    except Exception as e:
        print("Toplu analiz hatası:", e)
        return [0] * len(metin_listesi), {0: "Genel"}


