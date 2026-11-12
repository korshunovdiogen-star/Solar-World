(function () {
    'use strict';

    function readCsrfToken() {
        const meta = document.querySelector('meta[name="csrf-token"]');
        return meta ? meta.content : '';
    }

    function postQuantity(url, quantity) {
        return fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': readCsrfToken(),
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: new URLSearchParams({ quantity: String(quantity) })
        }).then(response => {
            if (!response.ok) {
                throw new Error('HTTP ' + response.status);
            }
            return response.json();
        });
    }

    function formatMoney(value) {
        return Number(value).toLocaleString('ru-RU', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
    }

    function parseMoney(value) {
        return Number(String(value).replace(/\s/g, '').replace(',', '.')) || 0;
    }

    function showError(element, message) {
        if (!element) return;
        element.textContent = message;
        element.hidden = false;
    }

    function clearError(element) {
        if (!element) return;
        element.textContent = '';
        element.hidden = true;
    }

    function initProductControls() {
        const form = document.querySelector('.product-cart-controls');
        if (!form) return;

        const toggle = form.querySelector('[data-role="toggle"]');
        const quantityBox = form.querySelector('[data-role="quantity"]');
        const valueElement = form.querySelector('[data-role="value"]');
        const decreaseButton = form.querySelector('[data-action="decrease"]');
        const increaseButton = form.querySelector('[data-action="increase"]');
        const errorElement = form.querySelector('[data-role="error"]');

        const url = form.dataset.addUrl;
        const cartUrl = form.dataset.cartUrl;
        const stock = parseInt(form.dataset.stock, 10) || 0;

        let quantity = parseInt(form.dataset.quantity, 10) || 0;
        let busy = false;

        function render() {
            const inCart = quantity > 0;

            valueElement.textContent = quantity;
            form.dataset.quantity = quantity;
            toggle.textContent = inCart ? 'К корзине' : 'Добавить в корзину';
            toggle.classList.toggle('is-in-cart', inCart);
            quantityBox.classList.toggle('is-visible', inCart);
            quantityBox.setAttribute('aria-hidden', inCart ? 'false' : 'true');

            toggle.disabled = busy || (!inCart && stock < 1);
            decreaseButton.disabled = busy;
            increaseButton.disabled = busy || quantity >= stock;
        }

        function applyQuantity(nextQuantity) {
            if (busy) return;

            const previousQuantity = quantity;
            quantity = nextQuantity;
            busy = true;
            clearError(errorElement);
            render();

            postQuantity(url, nextQuantity)
                .then(data => {
                    quantity = Number(data.quantity) || 0;
                })
                .catch(error => {
                    console.error('Ошибка корзины:', error);
                    quantity = previousQuantity;
                    showError(errorElement, 'Не удалось обновить корзину. Попробуйте ещё раз.');
                })
                .finally(() => {
                    busy = false;
                    render();
                });
        }

        form.addEventListener('submit', function (event) {
            event.preventDefault();

            if (quantity > 0) {
                window.location.href = cartUrl;
                return;
            }

            if (stock < 1) return;
            applyQuantity(1);
        });

        decreaseButton.addEventListener('click', function () {
            applyQuantity(Math.max(0, quantity - 1));
        });

        increaseButton.addEventListener('click', function () {
            if (quantity >= stock) return;
            applyQuantity(quantity + 1);
        });

        render();
    }

    function initCartPage() {
        const table = document.querySelector('.cart-table');
        if (!table) return;

        const content = document.querySelector('[data-role="cart-content"]');
        const emptyState = document.querySelector('[data-role="cart-empty"]');
        const totalElement = document.querySelector('[data-role="cart-total"]');
        const errorElement = document.querySelector('[data-role="cart-error"]');

        function activeRows() {
            return Array.from(table.querySelectorAll('.cart-row')).filter(
                row => row.dataset.removing !== '1'
            );
        }

        function rowQuantity(row) {
            return parseInt(row.dataset.quantity, 10) || 0;
        }

        function rowTotal(row) {
            return parseMoney(row.dataset.price) * rowQuantity(row);
        }

        function cartTotal() {
            return activeRows().reduce((sum, row) => sum + rowTotal(row), 0);
        }

        function renderTotal() {
            if (totalElement) {
                totalElement.textContent = formatMoney(cartTotal()) + ' руб.';
            }
        }

        function updateButtons(row) {
            const quantity = rowQuantity(row);
            const stock = parseInt(row.dataset.stock, 10) || 0;
            const busy = row.dataset.busy === '1';

            row.querySelector('[data-cart-action="decrease"]').disabled =
                busy || quantity <= 0;
            row.querySelector('[data-cart-action="increase"]').disabled =
                busy || quantity >= stock;
            row.querySelector('[data-cart-action="remove"]').disabled = busy;
        }

        function renderRow(row) {
            row.querySelector('[data-role="quantity"]').textContent = rowQuantity(row);
            row.querySelector('[data-role="row-total"]').textContent =
                formatMoney(rowTotal(row)) + ' руб.';
            updateButtons(row);
        }

        function removeRow(row, url) {
            row.dataset.removing = '1';
            row.style.display = 'none';
            renderTotal();

            postQuantity(url, 0)
                .then(data => {
                    row.remove();
                    if (totalElement) {
                        totalElement.textContent = formatMoney(data.total) + ' руб.';
                    }
                    if (activeRows().length === 0) {
                        if (content) content.hidden = true;
                        if (emptyState) emptyState.hidden = false;
                    }
                })
                .catch(error => {
                    console.error('Ошибка корзины:', error);
                    delete row.dataset.removing;
                    row.style.display = '';
                    delete row.dataset.busy;
                    renderRow(row);
                    renderTotal();
                    showError(errorElement, 'Не удалось удалить товар. Попробуйте ещё раз.');
                });
        }

        table.addEventListener('click', function (event) {
            const button = event.target.closest('[data-cart-action]');
            if (!button) return;

            const row = button.closest('.cart-row');
            if (!row || row.dataset.busy === '1') return;

            const url = row.dataset.setUrl;
            const action = button.dataset.cartAction;
            const currentQuantity = rowQuantity(row);
            const stock = parseInt(row.dataset.stock, 10) || 0;
            const nextQuantity = action === 'decrease'
                ? Math.max(0, currentQuantity - 1)
                : Math.min(stock, currentQuantity + 1);

            clearError(errorElement);

            if (action === 'remove' || nextQuantity === 0) {
                removeRow(row, url);
                return;
            }

            if (nextQuantity === currentQuantity) return;

            const previousQuantity = currentQuantity;
            row.dataset.quantity = nextQuantity;
            row.dataset.busy = '1';
            renderRow(row);
            renderTotal();

            postQuantity(url, nextQuantity)
                .then(data => {
                    if (data.in_cart === false) {
                        row.remove();
                        if (activeRows().length === 0) {
                            if (content) content.hidden = true;
                            if (emptyState) emptyState.hidden = false;
                        }
                    } else {
                        row.dataset.quantity = Number(data.quantity) || 0;
                    }
                    if (totalElement) {
                        totalElement.textContent = formatMoney(data.total) + ' руб.';
                    }
                })
                .catch(error => {
                    console.error('Ошибка корзины:', error);
                    row.dataset.quantity = previousQuantity;
                    renderTotal();
                    showError(errorElement, 'Не удалось обновить корзину. Попробуйте ещё раз.');
                })
                .finally(() => {
                    delete row.dataset.busy;
                    if (row.isConnected) {
                        renderRow(row);
                    }
                });
        });
    }

    document.addEventListener('DOMContentLoaded', function () {
        initProductControls();
        initCartPage();
    });
})();
