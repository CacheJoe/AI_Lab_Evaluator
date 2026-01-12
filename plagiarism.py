import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

DOMAIN_STOPWORDS = {
    "model","dataset","data","training","train","testing","test","accuracy",
    "algorithm","python","sklearn","keras","tensorflow","neural","network",
    "classification","classifier","regression","input","output","loss","epoch"
}

# ---------- Utilities ----------
def normalize(text):
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    words = [w for w in text.split() if w not in DOMAIN_STOPWORDS]
    return " ".join(words)

def long_sentences(text):
    sents = re.split(r"[.!?]", text)
    return [s.strip() for s in sents if len(s.split()) >= 8]

def char_ngrams(text, n=5):
    return {text[i:i+n] for i in range(len(text)-n+1)} if len(text) >= n else set()

def jaccard(a, b):
    if not a or not b:
        return 0
    return len(a & b) / len(a | b)

# ---------- Core hybrid similarity ----------
def hybrid_similarity(texts):
    cleaned = []
    index = []

    for i, t in enumerate(texts):
        sents = long_sentences(t)
        if len(sents) >= 2:
            cleaned.append(" ".join(normalize(s) for s in sents))
            index.append(i)

    if len(cleaned) < 2:
        return None, index

    tfidf = TfidfVectorizer(min_df=2).fit_transform(cleaned)
    tfidf_sim = cosine_similarity(tfidf)

    ngram_sets = [char_ngrams(t) for t in cleaned]

    phrase_sets = []
    for t in cleaned:
        w = t.split()
        phrase_sets.append(set(tuple(w[i:i+3]) for i in range(len(w)-2)))

    n = len(cleaned)
    hybrid = [[0]*n for _ in range(n)]

    for i in range(n):
        for j in range(n):
            if i == j:
                hybrid[i][j] = 1.0
            else:
                s1 = tfidf_sim[i][j]
                s2 = jaccard(ngram_sets[i], ngram_sets[j])
                s3 = jaccard(phrase_sets[i], phrase_sets[j])
                hybrid[i][j] = max(s1, s2, s3)

    return hybrid, index

# ---------- Flags ----------
def plagiarism_flags(theories):
    hybrid, index = hybrid_similarity(theories)

    if hybrid is None:
        return ["LOW"] * len(theories)

    flags = ["LOW"] * len(theories)

    for i, orig in enumerate(index):
        max_sim = max(hybrid[i][j] for j in range(len(hybrid)) if j != i)

        if max_sim > 0.65:
            flags[orig] = "HIGH"
        elif max_sim > 0.45:
            flags[orig] = "MEDIUM"
        else:
            flags[orig] = "LOW"

    return flags

# ---------- Matrix for reports ----------
def plagiarism_matrix(theories):
    return hybrid_similarity(theories)
