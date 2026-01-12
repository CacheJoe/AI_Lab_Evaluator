from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

model = SentenceTransformer("all-MiniLM-L6-v2")

def similarity(a, b):
    if not a.strip():
        return 0.0
    emb = model.encode([a, b])
    return cosine_similarity([emb[0]], [emb[1]])[0][0]

def evaluate_sections(topic, theory, algorithm, analysis, conclusion):
    return {
        "Theory_Relevance": similarity(topic, theory),
        "Algorithm_Relevance": similarity(topic, algorithm),
        "Analysis_Relevance": similarity(topic, analysis),
        "Conclusion_Relevance": similarity(topic, conclusion)
    }
