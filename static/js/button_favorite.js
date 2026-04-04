
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Создаём элемент для динамического тултипа
const tooltip = document.createElement('div');
tooltip.className = 'dynamic-tooltip';
tooltip.style.position = 'fixed';
tooltip.style.backgroundColor = 'rgba(0, 0, 0, 0.85)';
tooltip.style.backdropFilter = 'blur(4px)';
tooltip.style.color = '#fff';
tooltip.style.fontFamily = "'Courier New', monospace";
tooltip.style.fontSize = '0.75rem';
tooltip.style.padding = '4px 10px';
tooltip.style.borderRadius = '4px';
tooltip.style.border = '1px solid #00d4ff';
tooltip.style.boxShadow = '0 0 8px rgba(0,212,255,0.3)';
tooltip.style.pointerEvents = 'none';
tooltip.style.zIndex = '10000';
tooltip.style.whiteSpace = 'nowrap';
tooltip.style.display = 'none';
document.body.appendChild(tooltip);

function showTooltip(event, text) {
    tooltip.textContent = text;
    tooltip.style.display = 'block';
    tooltip.style.left = (event.clientX + 15) + 'px';
    tooltip.style.top = (event.clientY + 15) + 'px';
}

function hideTooltip() {
    tooltip.style.display = 'none';
}

function updateTooltipPosition(event) {
    if (tooltip.style.display === 'block') {
        tooltip.style.left = (event.clientX + 15) + 'px';
        tooltip.style.top = (event.clientY + 15) + 'px';
    }
}

document.addEventListener('DOMContentLoaded', function () {
    const favoriteBtns = document.querySelectorAll('.favorite-btn');

    favoriteBtns.forEach(btn => {
        btn.addEventListener('mouseenter', (e) => {
            const isActive = btn.classList.contains('active');
            const text = isActive ? 'Удалить из избранного' : 'Добавить в избранное';
            showTooltip(e, text);
        });
        btn.addEventListener('mousemove', updateTooltipPosition);
        btn.addEventListener('mouseleave', hideTooltip);

        btn.addEventListener('click', function (e) {
            e.preventDefault();
            const url = this.dataset.url;
            const contentType = this.dataset.contentType;
            const objectId = this.dataset.objectId;
            fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({
                    content_type: contentType,
                    object_id: objectId
                })
            })
                .then(response => response.json())
                .then(data => {
                    if (data.is_favorite) {
                        this.classList.add('active');
                    } else {
                        this.classList.remove('active');
                    }
                    // Обновляем текст тултипа, если он сейчас виден
                    if (tooltip.style.display === 'block') {
                        const newText = data.is_favorite ? 'Удалить из избранного' : 'Добавить в избранное';
                        tooltip.textContent = newText;
                    }
                })
                .catch(error => console.error('Ошибка:', error));
        });
    });
});