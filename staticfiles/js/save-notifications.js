export function saveNotificationsToDatabase(notifications) {
    try {
        localStorage.setItem('notifications', JSON.stringify(notifications));
    } catch (error) {
        console.error('Lỗi khi lưu trữ thông báo:', error);
    }
}