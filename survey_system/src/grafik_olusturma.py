import matplotlib.pyplot as plt
import pandas as pd

def save_combined_chart(q_text, q_data, filename):
    """
    Anket sorusuna ait hem Bar (cevap sayıları) hem de Pie (duygu/yüzde) grafiğini kaydeder.
    """
    q_data = q_data.copy()
    q_data["answer_count"] = q_data["answer_count"].fillna(0)

    if q_data.empty or q_data["answer_count"].sum() <= 0:
        return

    # --- Bar Chart Verisi ---
    answer_counts = q_data.groupby('answers_text')['answer_count'].sum().sort_values(ascending=False).head(8)
    labels_bar = answer_counts.index.astype(str).map(lambda x: x[:20] + "..." if len(x) > 20 else x)
    counts_bar = answer_counts.values

    # --- Pie Chart Verisi ---
    sent_col = "sentiment_label"
    if sent_col in q_data.columns and q_data[sent_col].nunique() > 1:
        sent_df = q_data.groupby(sent_col)["answer_count"].sum().reset_index()
        mode = "sentiment"
    else:
        sent_df = answer_counts.reset_index()
        sent_df.columns = [sent_col, "answer_count"]
        mode = "distribution"

    # --- Grafik Oluştur ---
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))

    # Bar Chart
    colors_bar = ['#F27A1A', '#3498db', '#2ecc71', '#9b59b6', '#34495e', '#16a085', '#27ae60', '#2980b9']
    ax1.bar(labels_bar, counts_bar, color=colors_bar[:len(labels_bar)], edgecolor='black', alpha=0.8)
    ax1.set_title("📌 Cevap Sayıları", fontsize=12, fontweight='bold', pad=15)
    ax1.set_xticks(range(len(labels_bar)))
    ax1.set_xticklabels(labels_bar, rotation=45, ha="right", fontsize=9)
    ax1.set_ylabel("Toplam Adet")
    ax1.grid(axis='y', linestyle='--', alpha=0.6)

    # Pie Chart
    if mode == "sentiment":
        colors_map = {'Pozitif': '#2ecc71', 'Negatif': '#e74c3c', 'Nötr': '#f1c40f'}
        current_colors = [colors_map.get(x, '#95a5a6') for x in sent_df[sent_col]]
        title_pie = "🎭 Duygu Tonu (BERT)"
    else:
        current_colors = plt.cm.Pastel1.colors
        title_pie = "📈 Yüzdesel Dağılım"

    ax2.pie(
        sent_df["answer_count"],
        labels=sent_df[sent_col].astype(str),
        autopct="%1.1f%%",
        startangle=140,
        colors=current_colors,
        textprops={'fontsize': 10, 'fontweight': 'bold'},
        wedgeprops={'edgecolor': 'white', 'linewidth': 1.5}
    )
    ax2.set_title(title_pie, fontsize=12, fontweight='bold', pad=15)

    plt.suptitle(f"Soru Analizi: {q_text}", fontsize=14, fontweight='bold', y=1.03, color='#2c3e50')
    plt.tight_layout()
    plt.savefig(filename, dpi=200, bbox_inches='tight')
    plt.close()


def find_categorical_questions(df, max_unique=2):
    """
    Sadece az sayıda eşsiz cevaba sahip soruları (ör: evet/hayır) döndürür.
    """
    categorical_questions = []
    for q_id in df["questions_id"].unique():
        q_data = df[df["questions_id"] == q_id]
        unique_answers = q_data["answers_text"].nunique()
        if 1 < unique_answers <= max_unique:
            categorical_questions.append(q_id)
    return categorical_questions


def save_question_distribution_chart_by_id(df, question_id, filename):
    """
    Sadece kategorik sorular için tek bar chart oluşturur.
    """
    q_data = df[df["questions_id"] == question_id]
    if q_data.empty:
        return

    counts = q_data.groupby("answers_text")["answer_count"].sum().sort_index()
    if counts.sum() == 0:
        return

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(counts.index.astype(str), counts.values, color='#3498db', edgecolor='black', alpha=0.8)
    ax.set_ylabel("Kişi Sayısı")
    ax.set_xlabel("Cevap")
    ax.set_xticks(range(len(counts.index)))
    ax.set_xticklabels(counts.index.astype(str), rotation=45, ha='right', fontsize=10)
    ax.set_title("📌 Cevap Dağılımı", fontsize=12, fontweight='bold')
    ax.grid(axis='y', linestyle='--', alpha=0.6)

    plt.tight_layout()
    plt.savefig(filename, dpi=200, bbox_inches='tight')
    plt.close()