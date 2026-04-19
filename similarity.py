from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from nltk.corpus import stopwords

def preprocess(text):
    words = text.lower().split()
    words = [w for w in words if w not in stopwords.words('english')]
    return " ".join(words)

def calculate_similarity(ans1, ans2):
    ans1 = preprocess(ans1)
    ans2 = preprocess(ans2)

    vectorizer = TfidfVectorizer()
    vectors = vectorizer.fit_transform([ans1, ans2])

    return cosine_similarity(vectors[0], vectors[1])[0][0]