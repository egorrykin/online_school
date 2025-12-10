// Основные JavaScript функции для Online School
document.addEventListener('DOMContentLoaded', function() {
    // Анимация при загрузке
    const cards = document.querySelectorAll('.card');
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';

        setTimeout(() => {
            card.style.transition = 'all 0.6s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 100);
    });

    // Валидация форм
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const requiredInputs = this.querySelectorAll('input[required], textarea[required], select[required]');
            let valid = true;

            requiredInputs.forEach(input => {
                if (!input.value.trim()) {
                    valid = false;
                    input.classList.add('is-invalid');

                    let errorDiv = input.parentElement.querySelector('.invalid-feedback');
                    if (!errorDiv) {
                        errorDiv = document.createElement('div');
                        errorDiv.className = 'invalid-feedback';
                        errorDiv.textContent = 'Это поле обязательно для заполнения';
                        input.parentElement.appendChild(errorDiv);
                    }
                } else {
                    input.classList.remove('is-invalid');
                    const errorDiv = input.parentElement.querySelector('.invalid-feedback');
                    if (errorDiv) {
                        errorDiv.remove();
                    }
                }
            });

            if (!valid) {
                e.preventDefault();
            }
        });
    });

    // Автоматическое скрытие сообщений
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.transition = 'opacity 0.5s';
            alert.style.opacity = '0';
            setTimeout(() => {
                if (alert.parentElement) {
                    alert.remove();
                }
            }, 500);
        }, 5000);
    });

    // Подтверждение удаления
    const deleteButtons = document.querySelectorAll('.btn-delete');
    deleteButtons.forEach(btn => {
        btn.addEventListener('click', function(e) {
            if (!confirm('Вы уверены, что хотите удалить этот элемент?')) {
                e.preventDefault();
            }
        });
    });

    // Переключение вкладок
    const tabButtons = document.querySelectorAll('[data-bs-toggle="tab"]');
    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            const target = document.querySelector(this.getAttribute('data-bs-target'));
            if (target) {
                target.classList.add('show', 'active');
            }
        });
    });

    // Анимация статистики
    const statNumbers = document.querySelectorAll('.stat-number');
    statNumbers.forEach(stat => {
        const text = stat.textContent;
        if (text && /\d+/.test(text)) {
            const target = parseInt(text.replace(/[^\d]/g, ''));
            let current = 0;
            const increment = target / 50;
            const timer = setInterval(() => {
                current += increment;
                if (current >= target) {
                    current = target;
                    clearInterval(timer);
                }
                stat.textContent = Math.round(current) + (text.replace(/\d+/g, '') || '');
            }, 30);
        }
    });

    // Подсветка активных элементов навигации
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });

    // Управление видимостью пароля
    const passwordToggles = document.querySelectorAll('.password-toggle');
    passwordToggles.forEach(toggle => {
        toggle.addEventListener('click', function() {
            const input = this.previousElementSibling;
            if (input.type === 'password') {
                input.type = 'text';
                this.innerHTML = '<i class="fas fa-eye-slash"></i>';
            } else {
                input.type = 'password';
                this.innerHTML = '<i class="fas fa-eye"></i>';
            }
        });
    });

    // Динамическая загрузка данных (пример)
    window.loadCourseData = function(courseId) {
        fetch(`/api/courses/${courseId}/stats/`)
            .then(response => response.json())
            .then(data => {
            // Обновление статистики курса
            console.log('Course data loaded:', data);
        })
            .catch(error => console.error('Error loading course data:', error));
    };

    // Инициализация всех компонентов
    initComponents();
});

function initComponents() {
    // Инициализация тултипов
    const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    tooltips.forEach(tooltip => {
        new bootstrap.Tooltip(tooltip);
    });

    // Инициализация попапов
    const popovers = document.querySelectorAll('[data-bs-toggle="popover"]');
    popovers.forEach(popover => {
        new bootstrap.Popover(popover);
    });
}

// Утилиты
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('ru-RU', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function truncateText(text, maxLength) {
    if (text.length <= maxLength) return text;
    return text.substr(0, maxLength) + '...';
}

// Обработчики событий для улучшения UX
document.addEventListener('click', function(e) {
    // Подтверждение действий
    if (e.target.classList.contains('confirm-action')) {
        const message = e.target.dataset.confirmMessage || 'Вы уверены, что хотите выполнить это действие?';
        if (!confirm(message)) {
            e.preventDefault();
            return false;
        }
    }

    // Плавная прокрутка к якорям
    if (e.target.hash && e.target.hash.startsWith('#')) {
        e.preventDefault();
        const target = document.querySelector(e.target.hash);
        if (target) {
            target.scrollIntoView({ behavior: 'smooth' });
        }
    }
});