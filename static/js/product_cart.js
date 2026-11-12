(function () {
    'use strict';

    function readCsrfToken() {
        const meta = document.querySelector('meta[name="csrf-token"]');
        return meta ? meta.content : '';
    }

    document.addEventListener('DOMContentLoaded', function () {
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

        function showError(message) {
            if (!errorElement) return;
            errorElement.textContent = message;
            errorElement.hidden = false;
        }

        function clearError() {
            if (!errorElement) return;
            errorElement.textContent = '';
            errorElement.hidden = true;
        }

        function setQuantity(nextQuantity) {
            if (busy) return;

            busy = true;
            clearError();
            render();

            fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': readCsrfToken(),
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: new URLSearchParams({ quantity: String(nextQuantity) })
            })
                .then(response => {
                    if (!response.ok) {
                        throw new Error('HTTP ' + response.status);
                    }
                    return response.json();
                })
                .then(data => {
                    quantity = Number(data.quantity) || 0;
                })
                .catch(error => {
                    console.error('Ошибка корзины:', error);
                    showError('Не удалось обновить корзину. Попробуйте ещё раз.');
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
            setQuantity(1);
        });

        decreaseButton.addEventListener('click', function () {
            setQuantity(Math.max(0, quantity - 1));
        });

        increaseButton.addEventListener('click', function () {
            if (quantity >= stock) return;
            setQuantity(quantity + 1);
        });

        render();
    });
})();
