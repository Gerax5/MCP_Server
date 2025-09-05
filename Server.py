import sys, json, requests, re
from textblob import TextBlob
from collections import Counter
from datetime import datetime

YOUTUBE_API_KEY = "AIzaSyDYKprvfDamr4hmaV51urC6FEFfawZ42Bc"

LOG_FILE = "mcp_debug.txt"

def log_debug(message):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().isoformat()}] {message}\n")

def send(msg):
    try:
        sys.stdout.write(json.dumps(msg) + "\n")
        sys.stdout.flush()
        log_debug(f"Sent: {msg}")
    except Exception as e:
        log_debug(f"Error in send: {e}")

def recv():
    try:
        line = sys.stdin.readline()
        if not line:
            return None
        msg = json.loads(line)
        log_debug(f"Received: {msg}")
        return msg
    except Exception as e:
        log_debug(f"Error in recv: {e}")
        return None

def get_channel_id(query):
    try:
        url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&type=channel&q={query}&key={YOUTUBE_API_KEY}"
        r = requests.get(url).json()
        log_debug(f"Channel search response: {r}")
        if "items" in r and len(r["items"]) > 0:
            return r["items"][0]["snippet"]["channelId"]
        return None
    except Exception as e:
        log_debug(f"Error in get_channel_id: {e}")
        return None

def get_comments(channel_id, max_comments=100):
    try:
        videos_url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&channelId={channel_id}&maxResults=5&order=date&type=video&key={YOUTUBE_API_KEY}"
        videos = requests.get(videos_url).json()
        comments = []
        for v in videos.get("items", []):
            vid = v["id"]["videoId"]
            comments_url = f"https://www.googleapis.com/youtube/v3/commentThreads?part=snippet&videoId={vid}&maxResults=50&key={YOUTUBE_API_KEY}"
            resp = requests.get(comments_url).json()
            for c in resp.get("items", []):
                text = c["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
                comments.append(text)
        log_debug(f"Fetched {len(comments)} comments")
        return comments[:max_comments]
    except Exception as e:
        log_debug(f"Error in get_comments: {e}")
        return []

def analyze_sentiment(comments):
    try:
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
    except Exception as e:
        log_debug(f"Error in analyze_sentiment: {e}")
        return {"sentiment": "neutral", "summary": "Error en análisis"}

def extract_keywords(comments, top_n=5):
    try:
        text = " ".join(comments).lower()
        words = re.findall(r"\b\w+\b", text)
        stopwords = {"de","la","que","el","en","y","a","los","se","del","las","un","por",
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
        "esos","esas","estoy","estás","está","estamos","estáis","están"}
        filtered = [w for w in words if w not in stopwords and len(w) > 2]
        counter = Counter(filtered)
        return counter.most_common(top_n)
    except Exception as e:
        log_debug(f"Error in extract_keywords: {e}")
        return []

def main():
    log_debug("Server started")
    while True:
        msg = recv()
        if msg is None:
            continue

        if msg.get("method") == "initialize":
            send({
                "jsonrpc": "2.0",
                "id": msg["id"],
                "result": {
                    "protocolVersion": msg["params"].get("protocolVersion", "0.1"),
                    "capabilities": {"tools": {"listChanged": True}},
                    "resources": {},
                    "serverInfo": {"name": "youtube", "version": "1.0.0"}
                }
            })

        elif msg.get("method") == "tools/list":
            send({
                "jsonrpc": "2.0",
                "id": msg["id"],
                "result": {
                    "tools": [
                        {
                            "name": "youtube_analysis",
                            "title": "YouTube Analysis",
                            "description": "Analiza la comunidad, audiencia, seguidores y comentarios de canales de YouTube para entender su demografía y comportamiento",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "channel": {"type": "string"},
                                    "max_comments": {"type": "integer", "default": 100},
                                    "top_words": {"type": "integer", "default": 5}
                                },
                                "required": ["channel"]
                            }
                        }
                    ]
                }
            })

        elif msg.get("method") == "tools/call":
            params = msg.get("params", {}) or {}
            name = params.get("name")
            args = params.get("arguments", {}) or {}

            if name == "youtube_analysis":
                try:
                    channel = args.get("channel")
                    max_comments = int(args.get("max_comments", 100))
                    top_words = int(args.get("top_words", 5))

                    channel_id = get_channel_id(channel)
                    if not channel_id:
                        content = [{"type": "text", "text": "Canal no encontrado"}]
                    else:
                        comments = get_comments(channel_id, max_comments)
                        analysis = analyze_sentiment(comments)
                        kw_pairs = extract_keywords(comments, top_words)
                        keywords = [{"word": w, "count": int(n)} for (w, n) in kw_pairs]

                        payload = {
                            "channel": channel,
                            "analysis": analysis,
                            "keywords": keywords,
                        }

                        content = [{
                            "type": "text",
                            "text": json.dumps(payload, ensure_ascii=False)
                        }]

                    send({
                        "jsonrpc": "2.0",
                        "id": msg["id"],
                        "result": { "content": content }
                    })

                except Exception as e:
                    send({
                        "jsonrpc": "2.0",
                        "id": msg["id"],
                        "result": {
                            "content": [{"type": "text", "text": f"Error: {e}"}]
                        }
                    })

        elif msg.get("method") == "prompts/list":
            send({
                "jsonrpc": "2.0",
                "id": msg["id"],
                "result": {
                    "prompts": [] 
                }
            })

        elif msg.get("method") == "resources/list":
            send({
                "jsonrpc": "2.0",
                "id": msg["id"],
                "result": {
                    "resources": []  
                }
            })

        elif msg.get("method", "").startswith("notifications/"):
            log_debug(f"Ignoring notification: {msg.get('method')}")
        else:
            log_debug(f"Unknown method: {msg.get('method')}")

if __name__ == "__main__":
    main()
