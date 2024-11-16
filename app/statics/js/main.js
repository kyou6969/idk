async function analyzeSingle() {
    const text = document.getElementById('singleText').value.trim();
    if (!text) {
        alert('请输入要分析的文本');
        return;
    }

    showLoading();

    try {
        const response = await fetch('/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ text }),
        });

        const result = await response.json();

        if (response.ok) {
            displaySingleResult(result);
        } else {
            alert('分析失败: ' + result.detail);
        }
    } catch (error) {
        alert('请求失败: ' + error.message);
    }

    hideLoading();
}

async function analyzeBatch() {
    const textArea = document.getElementById('batchText');
    const texts = textArea.value.split('\n').filter(text => text.trim() !== '');

    if (texts.length === 0) {
        alert('请输入要分析的文本');
        return;
    }

    showLoading();

    try {
        const response = await fetch('/analyze/batch', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ texts }),
        });

        const results = await response.json();

        if (response.ok) {
            displayBatchResults(results);
        } else {
            alert('分析失败: ' + results.detail);
        }
    } catch (error) {
        alert('请求失败: ' + error.message);
    }

    hideLoading();
}

function displaySingleResult(result) {
    const resultDiv = document.getElementById('singleResult');
    resultDiv.classList.remove('hidden');

    document.getElementById('sentiment').textContent = result.sentiment;
    document.getElementById('sentiment').className = getSentimentClass(result.sentiment);

    document.getElementById('score').textContent = result.score.toFixed(2);
    document.getElementById('intensity').textContent = result.intensity;

    const detailsContent = document.getElementById('detailsContent');
    detailsContent.innerHTML = '';

    for (const [key, value] of Object.entries(result.details)) {
        const p = document.createElement('p');
        p.textContent = `${getEmotionLabel(key)}: ${value.toFixed(2)}`;
        detailsContent.appendChild(p);
    }
}

function displayBatchResults(results) {
    const resultDiv = document.getElementById('batchResult');
    const contentDiv = document.getElementById('batchResultContent');

    resultDiv.classList.remove('hidden');
    contentDiv.innerHTML = '';

    results.forEach((result, index) => {
        const card = document.createElement('div');
        card.className = 'result-card bg-gray-50 p-4 rounded-lg';

        card.innerHTML = `
            <p class="font-medium mb-2">文本 ${index + 1}:</p>
            <p class="mb-2 text-gray-600">${result.text}</p>
            <p>情感倾向: <span class="${getSentimentClass(result.sentiment)}">${result.sentiment}</span></p>
            <p>情感分数: ${result.score.toFixed(2)}</p>
            <p>情感强度: ${result.intensity}</p>
            ${getDetailsHTML(result.details)}
        `;

        contentDiv.appendChild(card);
    });
}

function getSentimentClass(sentiment) {
    switch (sentiment) {
        case '积极': return 'sentiment-positive';
        case '消极': return 'sentiment-negative';
        default: return 'sentiment-neutral';
    }
}

function getEmotionLabel(key) {
    const labels = {
        'love': '喜爱',
        'happy': '快乐',
        'sad': '悲伤',
        'anger': '愤怒',
        'fear': '恐惧',
        'surprise': '惊讶',
        'good': '好感',
        'bad': '厌恶'
    };
    return labels[key] || key;
}

function getDetailsHTML(details) {
    if (!details || Object.keys(details).length === 0) return '';

    let html = '<div class="mt-2"><p class="font-medium">详细分析:</p><div class="ml-4">';
    for (const [key, value] of Object.entries(details)) {
        html += `<p>${getEmotionLabel(key)}: ${value.toFixed(2)}</p>`;
    }
    html += '</div></div>';
    return html;
}

function showLoading() {
    document.getElementById('loadingOverlay').classList.remove('hidden');
}

function hideLoading() {
    document.getElementById('loadingOverlay').classList.add('hidden');
}