// カテゴリと日本語名のマッピング
const categoryNames = {
    'technology': 'テクノロジー',
    'business': 'ビジネス',
    'entertainment': 'エンターテインメント',
    'sports': 'スポーツ'
};

let currentCategory = null;

// ページ読み込み時にカテゴリボタンを生成
document.addEventListener('DOMContentLoaded', async () => {
    await loadCategories();
});

// カテゴリ一覧を取得してボタンを生成
async function loadCategories() {
    try {
        const response = await fetch('/api/categories');
        const data = await response.json();
        
        const categoryButtons = document.getElementById('categoryButtons');
        categoryButtons.innerHTML = '';
        
        data.categories.forEach(category => {
            const button = document.createElement('button');
            button.className = 'category-btn';
            button.textContent = categoryNames[category] || category;
            button.onclick = (e) => selectCategory(category, e.target);
            categoryButtons.appendChild(button);
        });
    } catch (error) {
        console.error('Error loading categories:', error);
    }
}

// カテゴリを選択
async function selectCategory(category, buttonElement) {
    if (currentCategory === category) return;
    
    currentCategory = category;
    
    // ボタンのアクティブ状態を更新
    document.querySelectorAll('.category-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    if (buttonElement) {
        buttonElement.classList.add('active');
    }
    
    // ローディング表示
    const loading = document.getElementById('loading');
    const newsContainer = document.getElementById('newsContainer');
    loading.style.display = 'block';
    newsContainer.innerHTML = '';
    
    try {
        // ニュースを取得
        const response = await fetch(`/api/news/${category}`);
        const data = await response.json();
        
        // ニュースを表示
        displayNews(data);
    } catch (error) {
        console.error('Error fetching news:', error);
        newsContainer.innerHTML = `
            <div class="error-message">
                <p>エラーが発生しました: ${error.message}</p>
            </div>
        `;
    } finally {
        loading.style.display = 'none';
    }
}

// HTMLエスケープ関数
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ニュースを表示
function displayNews(data) {
    const newsContainer = document.getElementById('newsContainer');
    
    if (!data.news || data.news.length === 0) {
        newsContainer.innerHTML = `
            <div class="welcome-message">
                <p>ニュースが見つかりませんでした</p>
            </div>
        `;
        return;
    }
    
    // カテゴリヘッダー
    const categoryName = categoryNames[data.category] || data.category;
    let html = `
        <div class="category-header">
            <h3>${escapeHtml(categoryName)}</h3>
            <div class="news-count">${data.count}件のニュース</div>
        </div>
    `;
    
    // ニュースアイテム
    data.news.forEach(item => {
        const summary = item.summary || '概要なし';
        const published = item.published || '';
        const source = item.source || 'Unknown';
        const title = escapeHtml(item.title);
        const link = escapeHtml(item.link);
        const escapedSummary = escapeHtml(summary.substring(0, 300) + (summary.length > 300 ? '...' : ''));
        const escapedPublished = escapeHtml(published);
        const escapedSource = escapeHtml(source);
        
        // タグの表示
        const tagsHtml = item.tags && item.tags.length > 0
            ? item.tags.map(tag => `<span class="tag">${escapeHtml(tag)}</span>`).join('')
            : '<span class="tag">General</span>';
        
        html += `
            <div class="news-item">
                <div class="news-title">
                    <a href="${link}" target="_blank" rel="noopener noreferrer">
                        ${title}
                    </a>
                </div>
                <div class="news-summary">
                    ${escapedSummary}
                </div>
                <div class="news-meta">
                    <span>📅 ${escapedPublished}</span>
                    <span>📰 ${escapedSource}</span>
                </div>
                <div class="news-tags">
                    ${tagsHtml}
                </div>
            </div>
        `;
    });
    
    newsContainer.innerHTML = html;
}

