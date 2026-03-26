document.addEventListener('DOMContentLoaded', function () {
    const btn = document.getElementById('space-btn');
    const hoverSound = new Audio(window.soundUrl);
    hoverSound.volume = 0.2;
    if (btn) {
        btn.addEventListener('mouseenter', () => {
            hoverSound.currentTime = 0;
            hoverSound.play().catch(e => console.log("Для звука нужно взаимодействие с документом"));
        });
    }
});