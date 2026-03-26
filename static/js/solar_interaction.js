document.querySelectorAll('.planet-zone').forEach(zone => {
    zone.addEventListener('click', function () {
        const name = this.id.charAt(0).toUpperCase() + this.id.slice(1);
        const description = this.getAttribute('data-info');

        document.getElementById('planet-title').innerText = name;
        document.getElementById('planet-desc').innerText = description;

        // Добавим эффект "активности"
        console.log("Клик по планете:", name);
    });
});