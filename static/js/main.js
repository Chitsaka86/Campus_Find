document.addEventListener('DOMContentLoaded', () => {
    // Slider functionality
    let currentSlide = 0;
    const slides = document.querySelectorAll('.slide');
    
    if (slides.length > 0) {
        // Show first slide
        slides[0].style.display = 'block';
        
        // Auto-advance slides every 5 seconds
        setInterval(() => {
            slides[currentSlide].style.display = 'none';
            currentSlide = (currentSlide + 1) % slides.length;
            slides[currentSlide].style.display = 'block';
        }, 5000);
    }

    // Scrollable container for listing cards
    const container = document.querySelector('.scroll-container');
    if (container) {
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
    }

    // Chart for ratings (if Chart.js is available)
    const ratingsChart = document.getElementById('ratingsChart');
    if (ratingsChart && typeof Chart !== 'undefined') {
        const ctx = ratingsChart.getContext('2d');
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['1⭐','2⭐','3⭐','4⭐','5⭐'],
                datasets: [{
                    label: 'User Ratings',
                    data: [5, 10, 15, 25, 45],
                    backgroundColor: '#667eea'
                }]
            },
            options: { responsive: true }
        });
    }
});
