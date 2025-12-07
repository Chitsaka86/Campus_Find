document.addEventListener('DOMContentLoaded', () => {
    const container = document.querySelector('.scroll-container');
    let isDown = false;
    let startX, scrollLeft;

    container.addEventListener('mousedown', (e) => {
        isDown = true;
        startX = e.pageX - container.offsetLeft;
        scrollLeft = container.scrollLeft;
    });
    container.addEventListener('mouseleave', () => isDown = false);
    container.addEventListener('mouseup', () => isDown = false);
    container.addEventListener('mousemove', (e) => {
        if(!isDown) return;
        e.preventDefault();
        const x = e.pageX - container.offsetLeft;
        const walk = (x - startX) * 3;
        container.scrollLeft = scrollLeft - walk;
    });

    // Chart JS example for ratings
    const ctx = document.getElementById('ratingsChart').getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['1⭐','2⭐','3⭐','4⭐','5⭐'],
            datasets: [{
                label: 'User Ratings',
                data: [5, 10, 15, 25, 45],
                backgroundColor: '#4f46e5'
            }]
        },
        options: { responsive: true }
    });
});
