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

        const REMOVAL_DELAY_SECONDS = 10;

        function rows() {
            return Array.from(table.querySelectorAll('.cart-row'));
        }

        function rowQuantity(row) {
            return Math.max(0, parseInt(row.dataset.quantity, 10) || 0);
        }

        function rowTotal(row) {
            return parseMoney(row.dataset.price) * rowQuantity(row);
        }

        function cartTotal() {
            return rows().reduce((sum, row) => sum + rowTotal(row), 0);
        }

        function renderTotal() {
            if (totalElement) {
                totalElement.textContent = formatMoney(cartTotal()) + ' руб.';
            }
        }

        function showEmptyState() {
            if (content) content.hidden = true;
            if (emptyState) emptyState.hidden = false;
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

        function clearPendingRemoval(row) {
            if (row.removeTimer) {
                clearInterval(row.removeTimer);
                row.removeTimer = null;
            }

            const hint = row.querySelector('[data-role="removal-hint"]');
            if (hint) hint.remove();

            row.classList.remove('is-pending-removal');
        }

        function finishRemoval(row) {
            clearPendingRemoval(row);
            row.remove();
            renderTotal();

            if (rows().length === 0) {
                showEmptyState();
            }
        }

        function startPendingRemoval(row) {
            if (row.removeTimer) return;

            row.classList.add('is-pending-removal');

            const hint = document.createElement('div');
            hint.className = 'cart-removal-hint';
            hint.dataset.role = 'removal-hint';
            row.appendChild(hint);

            let secondsLeft = REMOVAL_DELAY_SECONDS;
            const paintHint = () => {
                hint.textContent =
                    'Товар исчезнет из корзины через ' +
                    secondsLeft +
                    ' с. Нажмите «+», чтобы вернуть его.';
            };
            paintHint();

            row.removeTimer = setInterval(() => {
                secondsLeft -= 1;
                if (secondsLeft <= 0) {
                    finishRemoval(row);
                    return;
                }
                paintHint();
            }, 1000);
        }

        function sendQuantity(row, quantity) {
            row.dataset.busy = '1';
            updateButtons(row);

            return postQuantity(row.dataset.setUrl, quantity)
                .then(data => {
                    row.dataset.quantity = Math.max(0, Number(data.quantity) || 0);
                    if (totalElement) {
                        totalElement.textContent = formatMoney(data.total) + ' руб.';
                    }
                })
                .finally(() => {
                    delete row.dataset.busy;
                    if (row.isConnected) {
                        renderRow(row);
                    }
                });
        }

        function changeQuantity(row, nextQuantity, previousQuantity) {
            row.dataset.quantity = nextQuantity;
            renderRow(row);
            renderTotal();

            sendQuantity(row, nextQuantity).catch(error => {
                console.error('Ошибка корзины:', error);
                row.dataset.quantity = previousQuantity;
                renderRow(row);
                renderTotal();
                showError(errorElement, 'Не удалось обновить корзину. Попробуйте ещё раз.');
            });
        }

        function removeRow(row) {
            const previousQuantity = rowQuantity(row);

            clearPendingRemoval(row);
            row.dataset.busy = '1';
            row.dataset.quantity = 0;
            row.style.display = 'none';
            renderTotal();

            postQuantity(row.dataset.setUrl, 0)
                .then(data => {
                    row.remove();
                    if (totalElement) {
                        totalElement.textContent = formatMoney(data.total) + ' руб.';
                    }
                    if (rows().length === 0) {
                        showEmptyState();
                    }
                })
                .catch(error => {
                    console.error('Ошибка корзины:', error);
                    row.style.display = '';
                    delete row.dataset.busy;
                    row.dataset.quantity = previousQuantity;
                    renderRow(row);
                    renderTotal();
                    showError(errorElement, 'Не удалось удалить товар. Попробуйте ещё раз.');
                });
        }

        table.addEventListener('click', function (event) {
            const button = event.target.closest('[data-cart-action]');
            if (!button) return;

            const row = button.closest('.cart-row');
            if (!row) return;

            clearError(errorElement);

            const action = button.dataset.cartAction;

            if (action === 'remove') {
                if (row.dataset.busy === '1') return;
                removeRow(row);
                return;
            }

            if (row.dataset.busy === '1') return;

            const currentQuantity = rowQuantity(row);
            const stock = parseInt(row.dataset.stock, 10) || 0;

            if (action === 'decrease') {
                if (currentQuantity <= 0) return;

                const nextQuantity = Math.max(0, currentQuantity - 1);

                if (nextQuantity === 0) {
                    row.dataset.quantity = 0;
                    renderRow(row);
                    renderTotal();
                    startPendingRemoval(row);

                    sendQuantity(row, 0).catch(error => {
                        console.error('Ошибка корзины:', error);
                        clearPendingRemoval(row);
                        row.dataset.quantity = currentQuantity;
                        renderRow(row);
                        renderTotal();
                        showError(errorElement, 'Не удалось обновить корзину. Попробуйте ещё раз.');
                    });
                    return;
                }

                changeQuantity(row, nextQuantity, currentQuantity);
                return;
            }

            if (action === 'increase') {
                if (currentQuantity >= stock) return;

                if (row.removeTimer) {
                    clearPendingRemoval(row);
                }

                changeQuantity(row, currentQuantity + 1, currentQuantity);
            }
        });
    }

    document.addEventListener('DOMContentLoaded', function () {
        initProductControls();
        initCartPage();
    });
})();
