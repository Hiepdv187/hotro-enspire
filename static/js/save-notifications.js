function saveNotificationsToFile(notifications) {
    const fs = require('fs'); // Nếu bạn đang làm việc trên Node.js
    const path = '/static/js/save-notifications.js';
    const content = `export const notificationsData = ${JSON.stringify(notifications)};`;
    
    fs.writeFile(path, content, err => {
        if (err) {
            console.error('Lỗi khi ghi file save-notifications.js:', err);
        } else {
            console.log('Thông báo đã được lưu vào file save-notifications.js');
        }
    });
}
