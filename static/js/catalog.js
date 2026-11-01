

(function () {
    document.addEventListener('DOMContentLoaded', function () {
        const config = window.catalogConfig || {};
        const apiUrl = config.apiUrl || '/api/catalog/';
        const categoryOptions = config.categoryOptions || {};
        const sortFields = config.sortFields || {};
        const renderCard = config.renderCard || function (item) { return ''; };

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
        if (sortFields && Object.keys(sortFields).length > 0) {
            const group = document.createElement('div');
            group.className = 'sort-buttons-group';
            group.style.display = 'flex';
            for (const [field, label] of Object.entries(sortFields)) {
                const btn = document.createElement('button');
                btn.className = 'sort-btn';
                btn.dataset.sort = field;
                btn.innerHTML = `${label} <span class="sort-direction">↑</span>`;
                group.appendChild(btn);
            }
            sortPanel.appendChild(group);
        }

        function getOrdering() {
            if (currentSort === 'name') {
                return sortOrder === 'asc' ? 'name_asc' : 'name_desc';
            }
            // Если поле не name, строим "поле_asc/desc"
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
                    totalPages = data.total_pages;
                    renderResults(data.results);
                    renderPagination();
                })
                .catch(error => {
                    console.error('Ошибка загрузки:', error);
                    resultsContainer.innerHTML = '<div class="no-results">Не удалось загрузить данные</div>';
                });
        }

        function renderResults(items) {
            resultsContainer.innerHTML = '';
            if (items.length === 0) {
                resultsContainer.innerHTML = '<div class="no-results">Ничего не найдено</div>';
                return;
            }
            items.forEach(item => {
                const cardHTML = renderCard(item);
                const div = document.createElement('div');
                div.innerHTML = cardHTML;
                resultsContainer.appendChild(div.firstElementChild);
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
            fetchCatalog();
        });

        searchInput.addEventListener('input', () => {
            currentPage = 1;
            fetchCatalog();
        });

        updateActiveButtons();
        fetchCatalog();
    });
})();