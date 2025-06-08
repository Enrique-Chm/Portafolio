// Performance optimization
const loadingScreen = document.getElementById('loading');
const navMenu = document.getElementById('navMenu');
const mobileToggle = document.getElementById('mobileToggle');

// Remove loading screen when page loads
window.addEventListener('load', () => {
  setTimeout(() => {
    loadingScreen.classList.add('hidden');
  }, 500);
});

// Mobile menu toggle
mobileToggle.addEventListener('click', () => {
  navMenu.classList.toggle('active');
  mobileToggle.textContent = navMenu.classList.contains('active') ? '✕' : '☰';
});

// Smooth scrolling for navigation links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
  anchor.addEventListener('click', function (e) {
    e.preventDefault();
    const target = document.querySelector(this.getAttribute('href'));
    if (target) {
      target.scrollIntoView({
        behavior: 'smooth',
        block: 'start'
      });
      // Close mobile menu if open
      navMenu.classList.remove('active');
      mobileToggle.textContent = '☰';
    }
  });
});

// Header scroll effect
let lastScrollY = window.scrollY;
window.addEventListener('scroll', () => {
  const header = document.querySelector('.header');
  if (window.scrollY > lastScrollY && window.scrollY > 100) {
    header.style.transform = 'translateY(-100%)';
  } else {
    header.style.transform = 'translateY(0)';
  }
  lastScrollY = window.scrollY;
});

// Intersection Observer for animations
const observerOptions = {
  threshold: 0.1,
  rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.style.animation = 'fadeInUp 0.8s ease-out forwards';
    }
  });
}, observerOptions);

// Observe sections for scroll animations
document.querySelectorAll('section').forEach(section => {
  observer.observe(section);
});

// Service Worker registration for PWA capabilities
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js')
      .then(registration => {
        console.log('SW registered: ', registration);
      })
      .catch(registrationError => {
        console.log('SW registration failed: ', registrationError);
      });
  });
}

// Error handling
window.addEventListener('error', (e) => {
  console.error('Global error:', e.error);
});

// Performance monitoring
window.addEventListener('load', () => {
  if ('performance' in window) {
    const perfData = performance.getEntriesByType('navigation')[0];
    console.log('Page load time:', perfData.loadEventEnd - perfData.loadEventStart, 'ms');
  }
});
