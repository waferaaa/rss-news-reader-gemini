from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import feedparser
import google.generativeai as genai
import os
from datetime import datetime
import time
import re
from dotenv import load_dotenv

# .envファイルから環境変数を読み込む
load_dotenv()

app = Flask(__name__)
CORS(app)

# Gemini APIの設定
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# カテゴリとRSSフィードのマッピング
RSS_FEEDS = {
    'technology': [
        'https://techcrunch.com/feed/',
        'https://www.theverge.com/rss/index.xml',
        'https://feeds.feedburner.com/oreilly/radar'
    ],
    'business': [
        'https://feeds.reuters.com/reuters/businessNews',
        'https://www.bloomberg.com/feed/topics/economics',
        'https://feeds.feedburner.com/oreilly/business'
    ],
    'entertainment': [
        'https://feeds.feedburner.com/oreilly/entertainment',
        'https://www.ew.com/feed/',
        'https://variety.com/feed/'
    ],
    'sports': [
        'https://www.espn.com/espn/rss/news',
        'https://feeds.bbci.co.uk/sport/rss.xml',
        'https://www.theguardian.com/sport/rss'
    ]
}

def clean_html(text):
    """HTMLタグを除去"""
    if not text:
        return ''
    # HTMLタグを除去
    text = re.sub(r'<[^>]+>', '', text)
    # エンティティをデコード
    text = text.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    text = text.replace('&quot;', '"').replace('&#39;', "'")
    return text.strip()

def fetch_news_from_rss(feed_urls):
    """RSSフィードからニュースを取得"""
    all_entries = []
    
    for feed_url in feed_urls:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:15]:  # 各フィードから最大15件取得
                summary = entry.get('summary', entry.get('description', ''))
                summary = clean_html(summary)
                
                all_entries.append({
                    'title': entry.get('title', 'No title'),
                    'link': entry.get('link', ''),
                    'summary': summary if summary else '概要なし',
                    'published': entry.get('published', ''),
                    'source': feed.feed.get('title', 'Unknown')
                })
        except Exception as e:
            print(f"Error fetching {feed_url}: {e}")
            continue
    
    # 重複を除去（タイトルで判定）
    seen_titles = set()
    unique_entries = []
    for entry in all_entries:
        if entry['title'] not in seen_titles:
            seen_titles.add(entry['title'])
            unique_entries.append(entry)
    
    return unique_entries[:20]  # 最大20件返す

def generate_tags_with_gemini(news_item):
    """Gemini APIを使用してニュースにタグを生成"""
    if not GEMINI_API_KEY:
        return ['No API Key']
    
    try:
        model = genai.GenerativeModel('gemini-pro')
        
        prompt = f"""以下のニュース記事に対して、適切なタグを3-5個生成してください。
タグは英語で、カンマ区切りで返してください。

タイトル: {news_item['title']}
概要: {news_item['summary'][:500]}

タグのみを返してください（説明不要）:"""
        
        response = model.generate_content(prompt)
        tags_text = response.text.strip()
        
        # タグを分割してクリーンアップ
        tags = [tag.strip() for tag in tags_text.split(',') if tag.strip()]
        return tags[:5] if tags else ['General']
    except Exception as e:
        print(f"Error generating tags: {e}")
        return ['Error']

@app.route('/')
def index():
    """メインページ"""
    return render_template('index.html')

@app.route('/api/news/<category>')
def get_news(category):
    """カテゴリに応じたニュースを取得"""
    if category not in RSS_FEEDS:
        return jsonify({'error': 'Invalid category'}), 400
    
    feed_urls = RSS_FEEDS[category]
    news_items = fetch_news_from_rss(feed_urls)
    
    # 各ニュースにタグを付与
    news_with_tags = []
    for item in news_items[:15]:  # 最大15件処理
        tags = generate_tags_with_gemini(item)
        item['tags'] = tags
        news_with_tags.append(item)
        # API制限を考慮して少し待機
        time.sleep(0.1)
    
    return jsonify({
        'category': category,
        'news': news_with_tags,
        'count': len(news_with_tags)
    })

@app.route('/api/categories')
def get_categories():
    """利用可能なカテゴリ一覧を取得"""
    return jsonify({
        'categories': list(RSS_FEEDS.keys())
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)

