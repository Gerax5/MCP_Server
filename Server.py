from fastmcp import FastMCP
import requests
from textblob import TextBlob
from collections import Counter
import re

YOUTUBE_API_KEY = "" 

mcp = FastMCP("youtube-community")


def get_channel_id(query):
    url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&type=channel&q={query}&key={YOUTUBE_API_KEY}"
    r = requests.get(url).json()
    if "items" in r and len(r["items"]) > 0:
        return r["items"][0]["snippet"]["channelId"]
    return None

def get_comments(channel_id, max_comments=100):
    videos_url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&channelId={channel_id}&maxResults=5&order=date&type=video&key={YOUTUBE_API_KEY}"
    videos = requests.get(videos_url).json()
    comments = []
    for v in videos.get("items", []):
        vid = v["id"]["videoId"]
        comments_url = f"https://www.googleapis.com/youtube/v3/commentThreads?part=snippet&videoId={vid}&maxResults=10&key={YOUTUBE_API_KEY}"
        resp = requests.get(comments_url).json()
        for c in resp.get("items", []):
            text = c["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
            comments.append(text)
    return comments[:max_comments]

def analyze_sentiment(comments):
    polarity = [TextBlob(c).sentiment.polarity for c in comments]
    if not polarity:
        return {"sentiment": "neutral", "summary": "No se encontraron comentarios"}
    avg = sum(polarity) / len(polarity)
    if avg > 0.1:
        sentiment = "positivo"
    elif avg < -0.1:
        sentiment = "negativo"
    else:
        sentiment = "neutral"
    return {"sentiment": sentiment, "comments": len(comments)}

def extract_keywords(comments, top_n=5):
    text = " ".join(comments).lower()
    words = re.findall(r"\b\w+\b", text)
    stopwords = set([
        "de","la","que","el","en","y","a","los","se","del","las","un","por",
        "con","no","una","su","para","es","al","lo","como","más","pero","sus",
        "le","ya","o","este","sí","porque","esta","entre","cuando","muy","sin",
        "sobre","también","me","hasta","hay","donde","quien","desde","todo",
        "nos","durante","todos","uno","les","ni","contra","otros","ese","eso",
        "ante","ellos","e","esto","mí","antes","algunos","qué","unos","yo",
        "otro","otras","otra","él","tanto","esa","estos","mucho","quienes",
        "nada","muchos","cual","poco","ella","estar","estas","algunas","algo",
        "nosotros","mi","mis","tú","te","ti","tu","tus","ellas","nosotras",
        "vosostros","vosostras","os","mío","mía","míos","mías","tuyo","tuya",
        "tuyos","tuyas","suyo","suya","suyos","suyas","nuestro","nuestra",
        "nuestros","nuestras","vuestro","vuestra","vuestros","vuestras",
        "esos","esas","estoy","estás","está","estamos","estáis","están"
    ])
    filtered = [w for w in words if w not in stopwords and len(w) > 2]
    counter = Counter(filtered)
    return counter.most_common(top_n)

# ---------------------------
# MCP Tool
# ---------------------------
@mcp.tool()
def youtube_analysis(channel: str, max_comments: int = 50, top_words: int = 5) -> dict:
    channel_id = get_channel_id(channel)
    if not channel_id:
        return {"error": "Canal no encontrado"}
    comments = get_comments(channel_id, max_comments)
    analysis = analyze_sentiment(comments)
    keywords = extract_keywords(comments, top_words)
    return {
        "channel": channel,
        "analysis": analysis,
        "keywords": keywords
    }

if __name__ == "__main__":
    mcp.run(
        transport="stdio"
    )
