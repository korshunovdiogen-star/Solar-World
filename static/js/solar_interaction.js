document.addEventListener('DOMContentLoaded', function () {
    let tooltip = document.querySelector('.custom-tooltip');
    if (!tooltip) {
        tooltip = document.createElement('div');
        tooltip.className = 'custom-tooltip';
        document.body.appendChild(tooltip);
    }

    function getPlanetName(id) {
        return id.charAt(0).toUpperCase() + id.slice(1);
    }

    const planets = document.querySelectorAll('.planet-zone');
    if (planets.length === 0) {
        console.warn('Элементы .planet-zone не найдены');
        return;
    }

    planets.forEach(zone => {
        zone.addEventListener('mouseenter', function (e) {
            const name = getPlanetName(this.id);
            tooltip.textContent = name;
            tooltip.classList.add('visible');
            tooltip.style.left = (e.clientX + 15) + 'px';
            tooltip.style.top = (e.clientY + 15) + 'px';
        });

        zone.addEventListener('mousemove', function (e) {
            tooltip.style.left = (e.clientX + 15) + 'px';
            tooltip.style.top = (e.clientY + 15) + 'px';
        });

        zone.addEventListener('mouseleave', function () {
            tooltip.classList.remove('visible');
        });
    });
});