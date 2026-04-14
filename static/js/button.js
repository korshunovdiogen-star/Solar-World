document.addEventListener('DOMContentLoaded', function () {
    const hoverSound = new Audio(window.soundUrl);
    hoverSound.volume = 0.1;

    // Все элементы с классом 'sound-hover'
    document.querySelectorAll('.sound-hover').forEach(btn => {
        btn.addEventListener('mouseenter', () => {
            hoverSound.currentTime = 0;
            hoverSound.play().catch(e => console.log("Для звука нужно взаимодействие с документом"));
        });
    });
});