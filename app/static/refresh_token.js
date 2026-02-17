let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
    failedQueue.forEach(prom => {
        if (error) {
            prom.reject(error);
        } else {
            prom.resolve();
        }
    });
    failedQueue = [];
};

async function apiCall(url, options = {}) {
    const originalRequest = { url, options };

    try {
        // Пробуем выполнить запрос
        let response = await fetch(url, {
            ...options,
            credentials: 'include'
        });

        // Если не 401 — просто возвращаем
        if (response.status !== 401) {
            return response;
        }

        // Если 401 — пробуем обновить токен
        if (!isRefreshing) {
            isRefreshing = true;

            try {
                // Зовем refresh endpoint
                const refreshResponse = await fetch('/refresh', {
                    method: 'POST',
                    credentials: 'include'
                });

                if (refreshResponse.ok) {
                    // Успешно обновили
                    processQueue(null);
                    // Повторяем исходный запрос
                    return await fetch(url, {
                        ...options,
                        credentials: 'include'
                    });
                } else {
                    // Refresh не удался
                    processQueue(new Error('Refresh failed'));
                    // 👇 ВАЖНО: делаем редирект и возвращаем что-то
                    window.location.href = '/login';
                    return null;  // ← ЯВНО ВОЗВРАЩАЕМ null
                }
            } finally {
                isRefreshing = false;
            }
        }

        // Если уже идет refresh, ставим в очередь
        return new Promise((resolve, reject) => {
            failedQueue.push({
                resolve: () => resolve(apiCall(url, options)),
                reject
            });
        });

    } catch (error) {
        console.error('API call failed:', error);
        throw error;
    }
}

// Исправленная функция использования
async function loadData() {
    try {
        const response = await apiCall('/api/protected');

        // Проверяем, что response существует и успешен
        if (response && response.ok) {
            const data = await response.json();
            console.log('✅ Успех:', data);
            // Здесь рисуем данные на странице
        } else if (response && response.status === 401) {
            console.log('⚠️ Требуется авторизация');
            // Можно ничего не делать, редирект уже произошел
        } else if (response === null) {
            console.log('🔄 Произошел редирект на логин');
            // Тоже ничего не делаем, редирект уже выполнен
        }
    } catch (error) {
        console.error('❌ Ошибка загрузки данных:', error);
    }
}

// Запускаем при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    console.log('Страница загружена, проверяем авторизацию...');
    loadData();
});