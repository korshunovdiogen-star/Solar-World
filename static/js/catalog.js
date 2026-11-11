

(function () {
    function escapeHtml(value) {
        return String(value == null ? '' : value)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    function isSafeHref(value) {
        const url = String(value == null ? '' : value).trim();
        return (
            (url.startsWith('/') && !url.startsWith('//')) ||
            /^https?:\/\//i.test(url)
        );
    }

    function safeUrl(value, fallback) {
        const url = String(value == null ? '' : value).trim();
        return escapeHtml(isSafeHref(url) ? url : fallback || '');
    }

    function buildCard(item, options) {
        options = options || {};
        const title = options.title || item.name || '';
        const category = options.category || '';
        const description = options.description || '';
        const meta = options.meta || '';
        const imageUrl = safeUrl(
            item.image || item.image_url,
            '/static/images/default.jpg'
        );
        const categoryHtml = category
            ? `<div class="card-category">${escapeHtml(category)}</div>`
            : '';
        const descriptionHtml = description
            ? `<p>${escapeHtml(description)}</p>`
            : '';

        return `<div class="catalog-card">
    ${categoryHtml}
    <div class="card-content">
        <h3>${escapeHtml(title)}</h3>
        ${descriptionHtml}
        ${meta}
    </div>
    <div class="card-image">
        <img src="${imageUrl}" alt="${escapeHtml(title)}">
    </div>
</div>`;
    }

    function articleCard(item) {
        const type = item.model_type;
        let extraInfo = '';

        if (type === 'planet' || type === 'satellite') {
            const typeText = escapeHtml(item.type_display || '—');
            const radius = escapeHtml(item.radius ? item.radius + ' км' : '—');
            extraInfo = `<div class="card-meta">${typeText} • ${radius}</div>`;
        } else if (type === 'mission') {
            const agencies = item.agency_names && item.agency_names.length
                ? item.agency_names.map(name => escapeHtml(name)).join(', ')
                : '—';
            extraInfo = `<div class="card-meta">${escapeHtml(item.type_display || '—')} • ${agencies}</div>`;
        } else if (type === 'spaceagency') {
            extraInfo = `<div class="card-meta">${escapeHtml(item.country || '—')}</div>`;
        } else if (type === 'company') {
            const revenueText = item.annual_revenue
                ? `${escapeHtml(item.annual_revenue)} млн USD`
                : '—';
            extraInfo = `<div class="card-meta">${escapeHtml(item.country || '—')} • Выручка: ${revenueText}</div>`;
        }

        const categoryNames = {
            planet: 'Планета',
            satellite: 'Спутник',
            mission: 'Миссия',
            spaceagency: 'Агентство',
            company: 'Компания'
        };

        return buildCard(item, {
            category: categoryNames[type] || type,
            description: item.first_line || type,
            meta: extraInfo
        });
    }

    function productCard(item) {
        const meta = `<div class="card-meta">Цена: ${escapeHtml(item.price)} руб. • Остаток: ${escapeHtml(item.stock)} шт.</div>`;

        return buildCard(item, {
            category: item.category_name || 'Без категории',
            description: item.first_line || item.description || '',
            meta: meta
        });
    }

    const cardRenderers = {
        article: articleCard,
        product: productCard
    };

    // Оставлено для совместимости с внешними renderCard.
    window.catalogEscapeHtml = escapeHtml;
    window.catalogSafeUrl = safeUrl;

    document.addEventListener('DOMContentLoaded', function () {
        const config = window.catalogConfig || {};
        const apiUrl = config.apiUrl || '/api/catalog/';
        const categoryOptions = config.categoryOptions || {};
        const sortFieldsConfig = config.sortFields || {};
        const sortFieldsArePerCategory = Object.values(sortFieldsConfig)
            .some(value => value && typeof value === 'object');
        const renderCard =
            config.renderCard ||
            cardRenderers[config.cardType] ||
            articleCard;

        const searchInput = document.getElementById('search-input');
        const categorySelect = document.getElementById('category-select');
        const resultsContainer = document.getElementById('results-container');

        if (categoryOptions && typeof categoryOptions === 'object') {
            for (const [value, label] of Object.entries(categoryOptions)) {
                const opt = document.createElement('option');
                opt.value = value;
                opt.textContent = label;
                categorySelect.appendChild(opt);
            }
        }

        let currentPage = 1;
        let totalPages = 1;
        let currentSort = 'name';
        let sortOrder = 'asc';

        const sortPanel = document.querySelector('.sort-panel');

        function getSortFields(category) {
            if (!sortFieldsArePerCategory) {
                return sortFieldsConfig;
            }
            return sortFieldsConfig[category] || sortFieldsConfig.all || {};
        }

        function renderSortButtons(category) {
            if (!sortPanel) return;

            const fields = getSortFields(category);
            const oldGroup = sortPanel.querySelector('.sort-buttons-group');
            if (oldGroup) oldGroup.remove();

            if (Object.keys(fields).length === 0) return;

            if (!Object.prototype.hasOwnProperty.call(fields, currentSort)) {
                currentSort = Object.keys(fields)[0];
                sortOrder = 'asc';
            }

            const group = document.createElement('div');
            group.className = 'sort-buttons-group';
            group.style.display = 'flex';
            for (const [field, label] of Object.entries(fields)) {
                const btn = document.createElement('button');
                btn.className = 'sort-btn';
                btn.dataset.sort = field;
                btn.appendChild(document.createTextNode(`${label} `));
                const direction = document.createElement('span');
                direction.className = 'sort-direction';
                direction.textContent = '↑';
                btn.appendChild(direction);
                group.appendChild(btn);
            }
            sortPanel.appendChild(group);
            updateActiveButtons();
        }

        function getOrdering() {
            if (currentSort === 'name') {
                return sortOrder === 'asc' ? 'name_asc' : 'name_desc';
            }
            return sortOrder === 'asc' ? currentSort + '_asc' : currentSort + '_desc';
        }

        function updateActiveButtons() {
            const btns = document.querySelectorAll('.sort-btn');
            btns.forEach(btn => {
                const field = btn.dataset.sort;
                const dirSpan = btn.querySelector('.sort-direction');
                if (field === currentSort) {
                    btn.classList.add('active');
                    if (dirSpan) dirSpan.textContent = sortOrder === 'asc' ? '↑' : '↓';
                } else {
                    btn.classList.remove('active');
                    if (dirSpan) dirSpan.textContent = '↑';
                }
            });
        }

        sortPanel.addEventListener('click', (e) => {
            const btn = e.target.closest('.sort-btn');
            if (!btn) return;
            const field = btn.dataset.sort;
            if (field === currentSort) {
                sortOrder = sortOrder === 'asc' ? 'desc' : 'asc';
            } else {
                currentSort = field;
                sortOrder = 'asc';
            }
            updateActiveButtons();
            currentPage = 1;
            fetchCatalog();
        });

        function fetchCatalog() {
            const q = searchInput.value.trim();
            const category = categorySelect.value;
            const ordering = getOrdering();
            const url = `${apiUrl}?q=${encodeURIComponent(q)}&category=${category}&page=${currentPage}&ordering=${ordering}`;
            fetch(url)
                .then(response => response.json())
                .then(data => {
                    totalPages = data.total_pages || 1;
                    currentPage = data.current_page || currentPage;
                    renderResults(data.results);
                    renderPagination();
                })
                .catch(error => {
                    console.error('Ошибка загрузки:', error);
                    resultsContainer.innerHTML = '<div class="no-results">Не удалось загрузить данные</div>';
                });
        }

        function buildCard(item) {
            const wrapper = document.createElement('div');
            wrapper.innerHTML = renderCard(item);
            let card = wrapper.firstElementChild;
            if (!card) return null;

            // Ссылку на детальную страницу добавляет общий рендер,
            // чтобы карточки каталога и магазина работали одинаково.
            if (!card.closest('a') && isSafeHref(item.detail_url)) {
                const link = document.createElement('a');
                link.href = String(item.detail_url).trim();
                link.className = 'catalog-card-link';
                link.appendChild(card);
                card = link;
            }
            return card;
        }

        function renderResults(items) {
            resultsContainer.innerHTML = '';
            if (items.length === 0) {
                resultsContainer.innerHTML = '<div class="no-results">Ничего не найдено</div>';
                return;
            }
            items.forEach(item => {
                const card = buildCard(item);
                if (card) {
                    resultsContainer.appendChild(card);
                }
            });
        }

        function renderPagination() {
            let paginationDiv = document.getElementById('pagination-controls');
            if (!paginationDiv) {
                paginationDiv = document.createElement('div');
                paginationDiv.id = 'pagination-controls';
                paginationDiv.className = 'pagination';
                document.querySelector('.catalog-container').appendChild(paginationDiv);
            }
            paginationDiv.innerHTML = '';

            if (currentPage > 1) {
                const prevBtn = document.createElement('button');
                prevBtn.textContent = '← Назад';
                prevBtn.addEventListener('click', () => {
                    currentPage--;
                    fetchCatalog();
                });
                paginationDiv.appendChild(prevBtn);
            }

            const startPage = Math.max(1, currentPage - 2);
            const endPage = Math.min(totalPages, currentPage + 2);
            for (let i = startPage; i <= endPage; i++) {
                const pageBtn = document.createElement('button');
                pageBtn.textContent = i;
                if (i === currentPage) {
                    pageBtn.disabled = true;
                    pageBtn.classList.add('active');
                }
                pageBtn.addEventListener('click', () => {
                    currentPage = i;
                    fetchCatalog();
                });
                paginationDiv.appendChild(pageBtn);
            }

            if (currentPage < totalPages) {
                const nextBtn = document.createElement('button');
                nextBtn.textContent = 'Вперёд →';
                nextBtn.addEventListener('click', () => {
                    currentPage++;
                    fetchCatalog();
                });
                paginationDiv.appendChild(nextBtn);
            }
        }

        categorySelect.addEventListener('change', () => {
            currentPage = 1;
            currentSort = 'name';
            sortOrder = 'asc';
            renderSortButtons(categorySelect.value);
            fetchCatalog();
        });

        searchInput.addEventListener('input', () => {
            currentPage = 1;
            fetchCatalog();
        });

        renderSortButtons(categorySelect.value);
        updateActiveButtons();
        fetchCatalog();
    });
})();