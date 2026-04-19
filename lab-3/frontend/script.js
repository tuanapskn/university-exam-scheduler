/**
 * KOSTÜ Sınav Programı - Frontend JavaScript
 * Rol tabanlı arayüz, API entegrasyonu, sınav yönetimi
 */

// ==================== GLOBAL DURUM ====================

let currentUser = null;
let currentRole = null;
let authToken = null;

const API_BASE = 'http://localhost:5000/api';

// Sayfalama değişkenleri
let teachersCurrentPage = 1;
const TEACHERS_PER_PAGE = 6;
let allTeachersData = [];
let filteredTeachersData = [];

let classroomsCurrentPage = 1;
const CLASSROOMS_PER_PAGE = 6;
let allClassroomsData = [];
let filteredClassroomsData = [];

let coursesCurrentPage = 1;
const COURSES_PER_PAGE = 6;
let allCoursesData = [];
let filteredCoursesData = [];

// ==================== HELPERs ====================

function escapeHtml(text) {
    const map = {'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;'};
    return text.replace(/[&<>"']/g, m => map[m]);
}

function showMessage(message, type = 'success', duration = 5000) {
    const messageArea = document.getElementById('messageArea');
    const icon = type === 'success' ? '✅' : type === 'error' ? '❌' : 'ℹ️';
    messageArea.innerHTML = `<div class="${type}">${icon} ${escapeHtml(message)}</div>`;
    setTimeout(() => {
        messageArea.innerHTML = '';
    }, duration);
}

function updateConnectionStatus(isHealthy) {
    const indicator = document.getElementById('statusIndicator');
    const statusText = document.getElementById('statusText');
    
    if (isHealthy) {
        indicator.className = 'status-indicator status-healthy';
        statusText.innerHTML = '<i class="fas fa-check-circle"></i> Sistem Çalışıyor';
    } else {
        indicator.className = 'status-indicator status-unhealthy';
        statusText.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Bağlantı Problemi';
    }
}

async function apiCall(endpoint, method = 'GET', body = null) {
    const options = {
        method,
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authToken}`
        }
    };
    
    if (body) options.body = JSON.stringify(body);
    
    try {
        const url = `${API_BASE}${endpoint}`;
        console.log(`📡 API Call: ${method} ${url}`, body || '');
        
        const response = await fetch(url, options);
        
        console.log(`📡 Response Status: ${response.status}`);
        
        if (response.status === 401) {
            logout();
            return null;
        }
        
        const data = await response.json();
        console.log(`📡 Response Data:`, data);
        return data;
    } catch (error) {
        console.error('❌ API Error:', error);
        showMessage('Ağ hatası: ' + error.message, 'error');
        return null;
    }
}

// ==================== LOGIN / LOGOUT ====================

async function login() {
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value.trim();
    const loginMessage = document.getElementById('loginMessage');
    
    console.log('🔐 Login başlatılıyor:', username);
    
    if (!username || !password) {
        loginMessage.textContent = 'Kullanıcı adı ve şifre zorunlu';
        loginMessage.className = 'login-message error';
        console.error('❌ Boş username/password');
        return false;
    }
    
    const result = await apiCall('/login', 'POST', { username, password });
    
    console.log('🔍 Login response:', result);
    
    if (!result || result.status !== 'success') {
        loginMessage.textContent = result?.message || 'Giriş başarısız';
        loginMessage.className = 'login-message error';
        console.error('❌ Login başarısız:', result?.message);
        return false;
    }
    
    // Token ve kullanıcı bilgisini kaydet
    authToken = result.token;
    currentUser = result.user;
    currentRole = result.user.role;
    
    console.log('✅ Token ve kullanıcı kaydedildi:', currentRole);
    
    localStorage.setItem('authToken', authToken);
    localStorage.setItem('user', JSON.stringify(currentUser));
    localStorage.setItem('role', currentRole);
    
    loginMessage.textContent = 'Giriş başarılı, yönlendiriliyor...';
    loginMessage.className = 'login-message success';
    
    setTimeout(() => {
        console.log('⏱️ UI değiştiriliyor...');
        showLoginUI(false);
        showMainUI(true);
        showRoleSpecificUI();
        initializeApp();
    }, 1000);
    
    return false;
}

function logout() {
    authToken = null;
    currentUser = null;
    currentRole = null;
    
    // Refresh interval'i temizle
    stopStudentExamsRefresh();
    
    localStorage.removeItem('authToken');
    localStorage.removeItem('user');
    localStorage.removeItem('role');
    
    showLoginUI(true);
    showMainUI(false);
    
    document.getElementById('username').value = '';
    document.getElementById('password').value = '';
}

function checkLogin() {
    const token = localStorage.getItem('authToken');
    const user = localStorage.getItem('user');
    const role = localStorage.getItem('role');
    
    if (token && user && role) {
        authToken = token;
        currentUser = JSON.parse(user);
        currentRole = role;
        
        showLoginUI(false);
        showMainUI(true);
        showRoleSpecificUI();
        initializeApp();
    } else {
        showLoginUI(true);
        showMainUI(false);
    }
}

function showLoginUI(show) {
    document.getElementById('loginContainer').style.display = show ? 'flex' : 'none';
}

function showMainUI(show) {
    document.getElementById('mainContainer').style.display = show ? 'block' : 'none';
}

function showRoleSpecificUI() {
    // Tüm panelleri gizle
    document.getElementById('adminPanel').style.display = 'none';
    document.getElementById('deptPanel').style.display = 'none';
    document.getElementById('teacherPanel').style.display = 'none';
    document.getElementById('studentPanel').style.display = 'none';
    
    // Role göre göster
    switch (currentRole) {
        case 'admin':
            document.getElementById('adminPanel').style.display = 'block';
            break;
        case 'bolum_yetkilisi':
            document.getElementById('deptPanel').style.display = 'block';
            break;
        case 'hoca':
            document.getElementById('teacherPanel').style.display = 'block';
            break;
        case 'ogrenci':
            document.getElementById('studentPanel').style.display = 'block';
            break;
    }
    
    // Kullanıcı adını göster
    document.getElementById('currentUsername').textContent = currentUser.username;
}

// ==================== TEMEL VERI YÜKLEME ====================

async function checkServiceHealth() {
    try {
        const response = await fetch(`${API_BASE.replace('/api', '')}/health`);
        const data = await response.json();
        updateConnectionStatus(data.status === 'healthy');
        return true;
    } catch (error) {
        updateConnectionStatus(false);
        return false;
    }
}

async function initializeApp() {
    console.log('🚀 Uygulama başlatılıyor...');
    checkServiceHealth();
    
    if (currentRole === 'admin') {
        loadDepartments();
        loadTeachers();
        loadClassrooms();
        loadCourses();
        loadExams();
    } else if (currentRole === 'bolum_yetkilisi') {
        setupDeptPanelListeners();
        await initDeptPanel();
    } else if (currentRole === 'hoca') {
        loadTeacherExams();
    } else if (currentRole === 'ogrenci') {
        loadStudentExams();
    }
    
    // Periyodik sağlık kontrolü
    setInterval(checkServiceHealth, 30000);
}

function setupDeptPanelListeners() {
    // Akademik kadro yükleme listener'ı
    document.getElementById('deptImportTeachersBtn')?.addEventListener('click', async () => {
        const fileInput = document.getElementById('deptTeachersFileInput');
        if (!fileInput.files || !fileInput.files[0]) {
            showMessage('Lütfen akademik_kadro.xlsx dosyasını seçin', 'error');
            return;
        }
        
        const formData = new FormData();
        formData.append('file', fileInput.files[0]);
        
        const btn = document.getElementById('deptImportTeachersBtn');
        const originalText = btn.innerHTML;
        
        try {
            btn.disabled = true;
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> İşleniyor...';
            
            showMessage('Akademik kadro verisi işleniyor...', 'success', 8000);
            
            const response = await fetch(`${API_BASE}/excel/import-teachers`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${authToken}` },
                body: formData
            });
            
            const result = await response.json();
            
            if (result?.status === 'success') {
                const message = `✅ ${result.created_teachers} yeni hoca eklendi, ${result.updated_teachers} hoca güncellendi, ${result.created_faculties} fakülte oluşturuldu`;
                showMessage(message, 'success', 8000);
                fileInput.value = '';
                
                // Listeler yenileme
                setTimeout(() => {
                    initDeptPanel();
                }, 500);
            } else {
                showMessage(`❌ Hata: ${result?.message || 'İçe aktarma başarısız'}`, 'error', 6000);
            }
        } catch (error) {
            showMessage(`❌ Yükleme hatası: ${error.message}`, 'error');
        } finally {
            btn.disabled = false;
            btn.innerHTML = originalText;
        }
    });
}

// ==================== ADMIN PANEL FONKSİYONLARI ====================

// Öğretim Üyesi Yönetimi
document.getElementById('teacherForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const name = document.getElementById('teacherName').value.trim();
    const days = document.getElementById('teacherDays').value.trim();
    const departmentId = parseInt(document.getElementById('teacherDepartment').value) || null;
    
    const result = await apiCall('/teachers', 'POST', {
        name,
        available_days: days || 'Mon,Tue,Wed,Thu,Fri',
        department_id: departmentId
    });
    
    if (result?.status === 'success') {
        showMessage('Öğretim üyesi eklendi', 'success');
        document.getElementById('teacherForm').reset();
        loadDepartments();
        loadTeachers();
    } else {
        showMessage(result?.message || 'Hata oluştu', 'error');
    }
});

async function loadDepartments() {
    const result = await apiCall('/departments');
    
    if (!result?.data) return;
    
    // Tüm fakülteleri göster (admin için)
    const faculties = result.data;
    
    const courseDepartmentSelect = document.getElementById('courseDepartment');
    if (courseDepartmentSelect) {
        courseDepartmentSelect.innerHTML = '<option value="">-- Fakülte Seç --</option>' +
            faculties.map(d => `<option value="${d.id}">${escapeHtml(d.name)}</option>`).join('');
    }
    
    const editTeacherDepartmentSelect = document.getElementById('editTeacherDepartment');
    if (editTeacherDepartmentSelect) {
        editTeacherDepartmentSelect.innerHTML = '<option value="">-- Fakülte Seç --</option>' +
            faculties.map(d => `<option value="${d.id}">${escapeHtml(d.name)}</option>`).join('');
    }
    
    const editCourseDepartmentSelect = document.getElementById('editCourseDepartment');
    if (editCourseDepartmentSelect) {
        editCourseDepartmentSelect.innerHTML = '<option value="">-- Fakülte Seç --</option>' +
            faculties.map(d => `<option value="${d.id}">${escapeHtml(d.name)}</option>`).join('');
    }
    
    // Fakülte filtre dropdown'larını doldur
    const teacherFacultyFilter = document.getElementById('teacherFacultyFilter');
    if (teacherFacultyFilter) {
        teacherFacultyFilter.innerHTML = '<option value="">📚 Tüm Fakülteler</option>' +
            faculties.map(d => `<option value="${d.id}">${escapeHtml(d.name)}</option>`).join('');
    }
    
    const courseFacultyFilter = document.getElementById('courseFacultyFilter');
    if (courseFacultyFilter) {
        courseFacultyFilter.innerHTML = '<option value="">📚 Tüm Fakülteler</option>' +
            faculties.map(d => `<option value="${d.id}">${escapeHtml(d.name)}</option>`).join('');
    }
}

// Bölüm değiştiğinde öğretim üyelerini filtrele
document.getElementById('courseDepartment')?.addEventListener('change', filterCourseTeachers);
document.getElementById('editCourseDepartment')?.addEventListener('change', filterEditCourseTeachers);

function filterCourseTeachers() {
    const selectedDeptId = parseInt(document.getElementById('courseDepartment')?.value);
    const teacherSelect = document.getElementById('courseTeacher');
    
    if (!teacherSelect || !allTeachersData.length) return;
    
    let filteredTeachers = allTeachersData;
    if (selectedDeptId) {
        filteredTeachers = allTeachersData.filter(t => t.department_id === selectedDeptId);
    }
    
    teacherSelect.innerHTML = '<option value="">-- Öğretim Üyesi Seç --</option>' +
        filteredTeachers.map(t => `<option value="${t.id}">${escapeHtml(t.name)}</option>`).join('');
}

function filterEditCourseTeachers() {
    const selectedDeptId = parseInt(document.getElementById('editCourseDepartment')?.value);
    const teacherSelect = document.getElementById('editCourseTeacher');
    
    if (!teacherSelect || !allTeachersData.length) return;
    
    const currentTeacherId = teacherSelect.value;
    
    let filteredTeachers = allTeachersData;
    if (selectedDeptId) {
        filteredTeachers = allTeachersData.filter(t => t.department_id === selectedDeptId);
    }
    
    teacherSelect.innerHTML = '<option value="">-- Öğretim Üyesi Seç --</option>' +
        filteredTeachers.map(t => `<option value="${t.id}">${escapeHtml(t.name)}</option>`).join('');
    
    // Önceki seçimi koru (eğer hala listede varsa)
    if (currentTeacherId && filteredTeachers.some(t => t.id === parseInt(currentTeacherId))) {
        teacherSelect.value = currentTeacherId;
    }
}

async function loadTeachers() {
    const result = await apiCall('/teachers');
    
    if (!result?.data) return;
    
    const container = document.getElementById('teachersList');
    if (!container) return;
    
    // Tüm öğretim üyelerini global değişkende sakla
    let teachersData = result.data;
    
    allTeachersData = teachersData;
    filteredTeachersData = teachersData;
    teachersCurrentPage = 1;
    
    if (teachersData.length === 0) {
        container.innerHTML = '<div class="empty-state">Hiçbir öğretim üyesi yok</div>';
        document.getElementById('teachersPagination').innerHTML = '';
        return;
    }
    
    // Select'leri başlangıçta tüm öğretim üyeleri ile doldur
    const select = document.getElementById('courseTeacher');
    if (select) {
        select.innerHTML = '<option value="">-- Öğretim Üyesi Seç --</option>' +
            result.data.map(t => `<option value="${t.id}">${escapeHtml(t.name)}</option>`).join('');
    }
    
    const editSelect = document.getElementById('editCourseTeacher');
    if (editSelect) {
        editSelect.innerHTML = '<option value="">-- Öğretim Üyesi Seç --</option>' +
            result.data.map(t => `<option value="${t.id}">${escapeHtml(t.name)}</option>`).join('');
    }
    
    // Mevcut fakülte seçimine göre filtrele
    filterCourseTeachers();
    filterEditCourseTeachers();
    
    // Arama ve filtreleme setup'ını yap
    setupTeachersSearch();
    setupTeachersFacultyFilter();
    
    // İlk sayfayı göster
    displayTeachersPage(1);
}

function setupTeachersFacultyFilter() {
    const facultyFilter = document.getElementById('teacherFacultyFilter');
    if (!facultyFilter) return;
    
    if (!facultyFilter.dataset.listenerAdded) {
        facultyFilter.addEventListener('change', () => {
            applyTeachersFilters();
        });
        facultyFilter.dataset.listenerAdded = 'true';
    }
}

function setupTeachersSearch() {
    const searchInput = document.getElementById('teachersSearchInput');
    if (!searchInput) return;
    
    if (!searchInput.dataset.listenerAdded) {
        searchInput.addEventListener('input', () => {
            applyTeachersFilters();
        });
        searchInput.dataset.listenerAdded = 'true';
    }
}

function applyTeachersFilters() {
    const searchQuery = document.getElementById('teachersSearchInput')?.value.toLowerCase().trim() || '';
    const selectedFacultyId = document.getElementById('teacherFacultyFilter')?.value || '';
    
    filteredTeachersData = allTeachersData.filter(t => {
        // Fakülte filtresi
        if (selectedFacultyId && parseInt(t.department_id) !== parseInt(selectedFacultyId)) {
            return false;
        }
        
        // Arama filtresi
        if (searchQuery) {
            const name = (t.name || '').toLowerCase();
            const title = (t.title || '').toLowerCase();
            const faculty = (t.faculty || '').toLowerCase();
            if (!name.includes(searchQuery) && !title.includes(searchQuery) && !faculty.includes(searchQuery)) {
                return false;
            }
        }
        
        return true;
    });
    
    teachersCurrentPage = 1;
    displayTeachersPage(1);
}

function displayTeachersPage(pageNum) {
    const container = document.getElementById('teachersList');
    if (!container) return;
    
    const totalPages = Math.ceil(filteredTeachersData.length / TEACHERS_PER_PAGE);
    const startIdx = (pageNum - 1) * TEACHERS_PER_PAGE;
    const endIdx = startIdx + TEACHERS_PER_PAGE;
    const pageData = filteredTeachersData.slice(startIdx, endIdx);
    
    if (pageData.length === 0) {
        container.innerHTML = '<div class="empty-state" style="grid-column: 1/-1;">Sonuç bulunamadı</div>';
        document.getElementById('teachersPagination').innerHTML = '';
        return;
    }
    
    // Kart grid'i
    container.innerHTML = pageData.map(t => `
        <div class="teacher-card">
            <div class="teacher-card-header">
                <div class="teacher-card-name">${escapeHtml(t.name)}</div>
                ${t.title ? `<div class="teacher-card-title">${escapeHtml(t.title)}</div>` : ''}
            </div>
            <div class="teacher-card-body">
                ${t.faculty ? `<div class="teacher-card-meta"><strong>Fakülte:</strong> ${escapeHtml(t.faculty)}</div>` : ''}
                <div class="teacher-card-days"><i class="fas fa-calendar"></i> Müsait: ${t.available_days}</div>
            </div>
            <div class="teacher-card-actions">
                <button class="btn-edit" onclick="editTeacher(${t.id}, '${escapeHtml(t.name).replace(/'/g, "\\'")}', '${t.available_days}')">
                    <i class="fas fa-edit"></i> Düzenle
                </button>
                <button class="btn-delete" onclick="deleteTeacher(${t.id}, '${escapeHtml(t.name).replace(/'/g, "\\'")}')">
                    <i class="fas fa-trash"></i> Sil
                </button>
            </div>
        </div>
    `).join('');
    
    // Sayfalama düğmeleri
    displayTeachersPagination(pageNum, totalPages);
}

function displayTeachersPagination(currentPage, totalPages) {
    const paginationContainer = document.getElementById('teachersPagination');
    if (!paginationContainer) return;
    
    if (totalPages <= 1) {
        paginationContainer.innerHTML = '';
        return;
    }
    
    let paginationHTML = '';
    
    // Önceki düğme
    paginationHTML += `
        <button class="pagination-btn" ${currentPage === 1 ? 'disabled' : ''} onclick="displayTeachersPage(${currentPage - 1})">
            <i class="fas fa-chevron-left"></i> Önceki
        </button>
    `;
    
    // Sayfa numaraları
    for (let i = 1; i <= totalPages; i++) {
        if (
            i === 1 ||
            i === totalPages ||
            (i >= currentPage - 1 && i <= currentPage + 1)
        ) {
            paginationHTML += `
                <button class="pagination-btn ${i === currentPage ? 'active' : ''}" onclick="displayTeachersPage(${i})">
                    ${i}
                </button>
            `;
        } else if (
            (i === 2 && currentPage > 3) ||
            (i === totalPages - 1 && currentPage < totalPages - 2)
        ) {
            paginationHTML += `<span class="pagination-info">...</span>`;
        }
    }
    
    // Sonraki düğme
    paginationHTML += `
        <button class="pagination-btn" ${currentPage === totalPages ? 'disabled' : ''} onclick="displayTeachersPage(${currentPage + 1})">
            Sonraki <i class="fas fa-chevron-right"></i>
        </button>
    `;
    
    paginationHTML += `
        <span class="pagination-info">${filteredTeachersData.length} hocanın ${currentPage}/${totalPages}. sayfası</span>
    `;
    
    paginationContainer.innerHTML = paginationHTML;
    teachersCurrentPage = currentPage;
}

// Derslik Yönetimi
document.getElementById('classroomForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const name = document.getElementById('classroomName').value.trim();
    const capacity = parseInt(document.getElementById('classroomCapacity').value) || 30;
    
    const result = await apiCall('/classrooms', 'POST', { name, capacity });
    
    if (result?.status === 'success') {
        showMessage('Derslik eklendi', 'success');
        document.getElementById('classroomForm').reset();
        loadClassrooms();
    } else {
        showMessage(result?.message || 'Hata oluştu', 'error');
    }
});

async function loadClassrooms() {
    const result = await apiCall('/classrooms');
    
    if (!result?.data) return;
    
    const container = document.getElementById('classroomsList');
    if (!container) return;
    
    allClassroomsData = result.data;
    filteredClassroomsData = result.data;
    classroomsCurrentPage = 1;
    
    if (result.data.length === 0) {
        container.innerHTML = '<div class="empty-state">Hiçbir derslik yok</div>';
        document.getElementById('classroomsPagination').innerHTML = '';
        return;
    }
    
    // Arama input'u setup'ını yap
    setupClassroomsSearch();
    
    // İlk sayfayı göster
    displayClassroomsPage(1);
}

function setupClassroomsSearch() {
    const searchInput = document.getElementById('classroomsSearchInput');
    if (!searchInput) return;
    
    if (!searchInput.dataset.listenerAdded) {
        searchInput.addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase().trim();
            
            if (!query) {
                filteredClassroomsData = allClassroomsData;
            } else {
                filteredClassroomsData = allClassroomsData.filter(c => {
                    const name = (c.name || '').toLowerCase();
                    return name.includes(query);
                });
            }
            
            classroomsCurrentPage = 1;
            displayClassroomsPage(1);
        });
        
        searchInput.dataset.listenerAdded = 'true';
    }
}

function displayClassroomsPage(pageNum) {
    const container = document.getElementById('classroomsList');
    if (!container) return;
    
    const totalPages = Math.ceil(filteredClassroomsData.length / CLASSROOMS_PER_PAGE);
    const startIdx = (pageNum - 1) * CLASSROOMS_PER_PAGE;
    const endIdx = startIdx + CLASSROOMS_PER_PAGE;
    const pageData = filteredClassroomsData.slice(startIdx, endIdx);
    
    if (pageData.length === 0) {
        container.innerHTML = '<div class="empty-state" style="grid-column: 1/-1;">Sonuç bulunamadı</div>';
        document.getElementById('classroomsPagination').innerHTML = '';
        return;
    }
    
    // Kart grid'i
    container.innerHTML = pageData.map(c => `
        <div class="item-card">
            <div class="item-card-header">
                <div class="item-card-title">${escapeHtml(c.name)}</div>
            </div>
            <div class="item-card-body">
                <div class="item-card-badge"><i class="fas fa-users"></i> Kapasite: ${c.capacity} kişi</div>
            </div>
            <div class="item-card-actions">
                <button class="btn-edit" onclick="editClassroom(${c.id}, '${escapeHtml(c.name).replace(/'/g, "\\'")}', ${c.capacity})">
                    <i class="fas fa-edit"></i> Düzenle
                </button>
                <button class="btn-delete" onclick="deleteClassroom(${c.id}, '${escapeHtml(c.name).replace(/'/g, "\\'")}')">
                    <i class="fas fa-trash"></i> Sil
                </button>
            </div>
        </div>
    `).join('');
    
    // Sayfalama düğmeleri
    displayClassroomsPagination(pageNum, totalPages);
}

function displayClassroomsPagination(currentPage, totalPages) {
    const paginationContainer = document.getElementById('classroomsPagination');
    if (!paginationContainer) return;
    
    if (totalPages <= 1) {
        paginationContainer.innerHTML = '';
        return;
    }
    
    let paginationHTML = '';
    
    paginationHTML += `
        <button class="pagination-btn" ${currentPage === 1 ? 'disabled' : ''} onclick="displayClassroomsPage(${currentPage - 1})">
            <i class="fas fa-chevron-left"></i> Önceki
        </button>
    `;
    
    for (let i = 1; i <= totalPages; i++) {
        if (
            i === 1 ||
            i === totalPages ||
            (i >= currentPage - 1 && i <= currentPage + 1)
        ) {
            paginationHTML += `
                <button class="pagination-btn ${i === currentPage ? 'active' : ''}" onclick="displayClassroomsPage(${i})">
                    ${i}
                </button>
            `;
        } else if (
            (i === 2 && currentPage > 3) ||
            (i === totalPages - 1 && currentPage < totalPages - 2)
        ) {
            paginationHTML += `<span class="pagination-info">...</span>`;
        }
    }
    
    paginationHTML += `
        <button class="pagination-btn" ${currentPage === totalPages ? 'disabled' : ''} onclick="displayClassroomsPage(${currentPage + 1})">
            Sonraki <i class="fas fa-chevron-right"></i>
        </button>
    `;
    
    paginationHTML += `
        <span class="pagination-info">${filteredClassroomsData.length} dersliğin ${currentPage}/${totalPages}. sayfası</span>
    `;
    
    paginationContainer.innerHTML = paginationHTML;
    classroomsCurrentPage = currentPage;
}

// Ders Yönetimi
document.getElementById('courseForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const name = document.getElementById('courseName').value.trim();
    const code = document.getElementById('courseCodeInput').value.trim();
    const departmentId = parseInt(document.getElementById('courseDepartment').value) || null;
    const teacherId = parseInt(document.getElementById('courseTeacher').value) || null;
    const studentCount = parseInt(document.getElementById('courseStudentCount').value) || 0;
    const examDuration = parseInt(document.getElementById('courseExamDuration').value) || 60;
    
    const result = await apiCall('/courses', 'POST', {
        name,
        code,
        department_id: departmentId,
        teacher_id: teacherId,
        student_count: studentCount,
        exam_duration: examDuration
    });
    
    if (result?.status === 'success') {
        showMessage('Ders eklendi', 'success');
        document.getElementById('courseForm').reset();
        loadDepartments();
        loadTeachers();
        loadCourses();
    } else {
        showMessage(result?.message || 'Hata oluştu', 'error');
    }
});

async function loadCourses() {
    const result = await apiCall('/courses');
    
    if (!result?.data) return;
    
    const container = document.getElementById('coursesList');
    if (!container) return;
    
    allCoursesData = result.data;
    filteredCoursesData = result.data;
    coursesCurrentPage = 1;
    
    if (result.data.length === 0) {
        container.innerHTML = '<div class="empty-state">Hiçbir ders yok</div>';
        document.getElementById('coursesPagination').innerHTML = '';
        return;
    }
    
    // Arama ve filtreleme setup'ını yap
    setupCoursesSearch();
    setupCoursesFacultyFilter();
    
    // İlk sayfayı göster
    displayCoursesPage(1);
}

function setupCoursesFacultyFilter() {
    const facultyFilter = document.getElementById('courseFacultyFilter');
    if (!facultyFilter) return;
    
    if (!facultyFilter.dataset.listenerAdded) {
        facultyFilter.addEventListener('change', () => {
            applyCoursesFilters();
        });
        facultyFilter.dataset.listenerAdded = 'true';
    }
}

function setupCoursesSearch() {
    const searchInput = document.getElementById('coursesSearchInput');
    if (!searchInput) return;
    
    if (!searchInput.dataset.listenerAdded) {
        searchInput.addEventListener('input', () => {
            applyCoursesFilters();
        });
        searchInput.dataset.listenerAdded = 'true';
    }
}

function applyCoursesFilters() {
    const searchQuery = document.getElementById('coursesSearchInput')?.value.toLowerCase().trim() || '';
    const selectedFacultyId = document.getElementById('courseFacultyFilter')?.value || '';
    
    filteredCoursesData = allCoursesData.filter(c => {
        // Fakülte filtresi
        if (selectedFacultyId && parseInt(c.department_id) !== parseInt(selectedFacultyId)) {
            return false;
        }
        
        // Arama filtresi
        if (searchQuery) {
            const name = (c.name || '').toLowerCase();
            const code = (c.code || '').toLowerCase();
            const teacherName = (c.teacher_name || '').toLowerCase();
            if (!name.includes(searchQuery) && !code.includes(searchQuery) && !teacherName.includes(searchQuery)) {
                return false;
            }
        }
        
        return true;
    });
    
    coursesCurrentPage = 1;
    displayCoursesPage(1);
}

function displayCoursesPage(pageNum) {
    const container = document.getElementById('coursesList');
    if (!container) return;
    
    const totalPages = Math.ceil(filteredCoursesData.length / COURSES_PER_PAGE);
    const startIdx = (pageNum - 1) * COURSES_PER_PAGE;
    const endIdx = startIdx + COURSES_PER_PAGE;
    const pageData = filteredCoursesData.slice(startIdx, endIdx);
    
    if (pageData.length === 0) {
        container.innerHTML = '<div class="empty-state" style="grid-column: 1/-1;">Sonuç bulunamadı</div>';
        document.getElementById('coursesPagination').innerHTML = '';
        return;
    }
    
    // Kart grid'i
    container.innerHTML = pageData.map(c => `
        <div class="item-card">
            <div class="item-card-header">
                <div class="item-card-title">${escapeHtml(c.name)}</div>
                ${c.code ? `<div class="item-card-subtitle">Kod: ${escapeHtml(c.code)}</div>` : ''}
            </div>
            <div class="item-card-body">
                <div class="item-card-meta"><strong>👨‍🏫 Hoca:</strong> ${escapeHtml(c.teacher_name || 'Atanmamış')}</div>
                <div class="item-card-meta"><strong>👥 Öğrenci:</strong> ${c.student_count}</div>
                <div class="item-card-badge"><i class="fas fa-clock"></i> ${c.exam_duration} dakika</div>
            </div>
            <div class="item-card-actions">
                <button class="btn-edit" onclick="editCourse(${c.id})">
                    <i class="fas fa-edit"></i> Düzenle
                </button>
                <button class="btn-delete" onclick="deleteCourse(${c.id}, '${escapeHtml(c.name).replace(/'/g, "\\'")}')">
                    <i class="fas fa-trash"></i> Sil
                </button>
            </div>
        </div>
    `).join('');
    
    // Sayfalama düğmeleri
    displayCoursesPagination(pageNum, totalPages);
}

function displayCoursesPagination(currentPage, totalPages) {
    const paginationContainer = document.getElementById('coursesPagination');
    if (!paginationContainer) return;
    
    if (totalPages <= 1) {
        paginationContainer.innerHTML = '';
        return;
    }
    
    let paginationHTML = '';
    
    paginationHTML += `
        <button class="pagination-btn" ${currentPage === 1 ? 'disabled' : ''} onclick="displayCoursesPage(${currentPage - 1})">
            <i class="fas fa-chevron-left"></i> Önceki
        </button>
    `;
    
    for (let i = 1; i <= totalPages; i++) {
        if (
            i === 1 ||
            i === totalPages ||
            (i >= currentPage - 1 && i <= currentPage + 1)
        ) {
            paginationHTML += `
                <button class="pagination-btn ${i === currentPage ? 'active' : ''}" onclick="displayCoursesPage(${i})">
                    ${i}
                </button>
            `;
        } else if (
            (i === 2 && currentPage > 3) ||
            (i === totalPages - 1 && currentPage < totalPages - 2)
        ) {
            paginationHTML += `<span class="pagination-info">...</span>`;
        }
    }
    
    paginationHTML += `
        <button class="pagination-btn" ${currentPage === totalPages ? 'disabled' : ''} onclick="displayCoursesPage(${currentPage + 1})">
            Sonraki <i class="fas fa-chevron-right"></i>
        </button>
    `;
    
    paginationHTML += `
        <span class="pagination-info">${filteredCoursesData.length} dersin ${currentPage}/${totalPages}. sayfası</span>
    `;
    
    paginationContainer.innerHTML = paginationHTML;
    coursesCurrentPage = currentPage;
}

// Sınav Listesi
let allExamsData = [];
let selectedFacultyId = null;

async function loadExams() {
    const result = await apiCall('/exams');
    
    if (!result?.data) return;
    
    allExamsData = result.data;
    
    const container = document.getElementById('examsList');
    if (!container) return;
    
    if (allExamsData.length === 0) {
        const tabsContainer = document.getElementById('facultyTabs');
        if (tabsContainer) tabsContainer.innerHTML = '';
        container.innerHTML = '<div class="empty-exams"><i class="fas fa-calendar-times"></i>Henüz planlanmış sınav yok</div>';
        return;
    }
    
    // Sınavların faculty_id'si var mı kontrol et
    const hasValidFaculties = allExamsData.some(exam => exam.faculty_id);
    
    if (!hasValidFaculties) {
        // Faculty_id yoksa basit tablo göster
        const tabsContainer = document.getElementById('facultyTabs');
        if (tabsContainer) tabsContainer.innerHTML = '';
        displaySimpleExamTable();
        return;
    }
    
    // Fakülte listesi oluştur
    await loadFacultyTabs();
}

function displaySimpleExamTable() {
    const container = document.getElementById('examsList');
    if (!container) return;
    
    const tableHTML = `
        <table class="exams-table">
            <thead>
                <tr>
                    <th>📅 Tarih</th>
                    <th>⏰ Saat</th>
                    <th>📚 Ders</th>
                    <th>👨‍🏫 Hoca</th>
                    <th>🚪 Derslik</th>
                    <th>⏱️ Süre</th>
                </tr>
            </thead>
            <tbody>
                ${allExamsData.map(e => `
                    <tr>
                        <td class="exam-date">${e.slot_start?.substring(0,10) || 'N/A'}</td>
                        <td class="exam-time">${e.slot_start?.substring(11,16) || 'N/A'}</td>
                        <td class="exam-course">${escapeHtml(e.course_name)}</td>
                        <td class="exam-teacher">${escapeHtml(e.teacher_name || 'Atanmamış')}</td>
                        <td><span class="exam-classroom">${escapeHtml(e.room_name)}</span></td>
                        <td class="exam-duration">${e.duration || 60} dk</td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
    
    container.innerHTML = tableHTML;
}

async function loadFacultyTabs() {
    // Fakülteleri API'den çekelim
    const facultiesResult = await apiCall('/facilities');
    if (!facultiesResult?.data) return;
    
    const faculties = facultiesResult.data;
    
    const tabsContainer = document.getElementById('facultyTabs');
    if (!tabsContainer) return;
    
    tabsContainer.innerHTML = faculties.map(faculty => `
        <button class="faculty-tab" data-faculty-id="${faculty.id}">
            ${escapeHtml(faculty.name)}
        </button>
    `).join('');
    
    // Tab tıklama olayları
    tabsContainer.querySelectorAll('.faculty-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            tabsContainer.querySelectorAll('.faculty-tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            selectedFacultyId = parseInt(tab.dataset.facultyId);
            displayWeeklySchedule(selectedFacultyId);
        });
    });
    
    // İlk fakülteyi varsayılan olarak seç
    if (faculties.length > 0) {
        const firstTab = tabsContainer.querySelector('.faculty-tab');
        if (firstTab) firstTab.click();
    } else {
        // Hiç fakülte yoksa basit tablo göster
        displaySimpleExamTable();
    }
}

function displayWeeklySchedule(facultyId) {
    const container = document.getElementById('examsList');
    if (!container) return;
    
    // Fakülte sınavlarını filtrele - faculty_id'ye göre
    const facultyExams = allExamsData.filter(exam => exam.faculty_id === facultyId);
    
    if (facultyExams.length === 0) {
        container.innerHTML = '<div class="empty-exams"><i class="fas fa-calendar-times"></i>Bu fakülte için henüz planlanmış sınav yok</div>';
        return;
    }
    
    // Sınavları tarihlere göre grupla
    const examsByDate = {};
    const timeSlots = new Set();
    
    facultyExams.forEach(exam => {
        const datetime = exam.slot_start || '';
        const date = datetime.substring(0, 10);
        const time = datetime.substring(11, 16);
        
        if (!examsByDate[date]) {
            examsByDate[date] = {};
        }
        
        if (!examsByDate[date][time]) {
            examsByDate[date][time] = [];
        }
        
        examsByDate[date][time].push(exam);
        timeSlots.add(time);
    });
    
    // Tarih ve saat dilimlerini sırala
    const sortedDates = Object.keys(examsByDate).sort();
    const sortedTimeSlots = Array.from(timeSlots).sort();
    
    // Haftaları böl (her hafta 5 gün)
    const weeks = [];
    for (let i = 0; i < sortedDates.length; i += 5) {
        weeks.push(sortedDates.slice(i, i + 5));
    }
    
    // Her hafta için tablo oluştur
    const weeklyHTML = weeks.map((weekDates, weekIndex) => {
        const weekNumber = weekIndex + 1;
        const firstDate = new Date(weekDates[0]);
        const lastDate = new Date(weekDates[weekDates.length - 1]);
        
        const weekTitle = `${weekNumber}. Hafta (${formatDate(firstDate)} - ${formatDate(lastDate)})`;
        
        const tableHTML = `
            <div class="week-schedule">
                <div class="week-title">${weekTitle}</div>
                <table class="schedule-table">
                    <thead>
                        <tr>
                            <th>Tarih / Saat</th>
                            ${sortedTimeSlots.map(time => `<th>${time}</th>`).join('')}
                        </tr>
                    </thead>
                    <tbody>
                        ${weekDates.map(date => {
                            const dateObj = new Date(date);
                            const dayName = getDayName(dateObj);
                            const formattedDate = formatDate(dateObj);
                            
                            return `
                                <tr>
                                    <td><strong>${dayName}</strong><br>${formattedDate}</td>
                                    ${sortedTimeSlots.map(time => {
                                        const exams = examsByDate[date]?.[time] || [];
                                        
                                        if (exams.length === 0) {
                                            return '<td class="empty-cell">-</td>';
                                        }
                                        
                                        return `
                                            <td>
                                                ${exams.map(exam => `
                                                    <div class="exam-cell">
                                                        <div class="exam-cell-title">${escapeHtml(exam.course_code || exam.course_name)}</div>
                                                        <div class="exam-cell-teacher">${escapeHtml(exam.teacher_name || 'Atanmamış')}</div>
                                                        <div class="exam-cell-room">📍 ${escapeHtml(exam.room_name)}</div>
                                                    </div>
                                                `).join('')}
                                            </td>
                                        `;
                                    }).join('')}
                                </tr>
                            `;
                        }).join('')}
                    </tbody>
                </table>
            </div>
        `;
        
        return tableHTML;
    }).join('');
    
    container.innerHTML = weeklyHTML;
}

function getDayName(date) {
    const days = ['Pazar', 'Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma', 'Cumartesi'];
    return days[date.getDay()];
}

function formatDate(date) {
    const day = String(date.getDate()).padStart(2, '0');
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const year = date.getFullYear();
    return `${day}.${month}.${year}`;
}

// Planlama
document.getElementById('runScheduler')?.addEventListener('click', async () => {
    if (!confirm('Sınav planlaması çalıştırılsın mı?')) return;
    
    showMessage('Planlama başlatılıyor...', 'success', 10000);
    
    const result = await apiCall('/schedule', 'POST', {
        days: 5,
        force: false
    });
    
    if (result?.status === 'success') {
        showMessage(`Planlama tamamlandı: ${result.created} ders planlandı`, 'success');
        
        // Admin panel'deki sınavları güncelle
        loadExams();
        
        // Öğrenci verilerini DE güncelle (1 saniye gecikme ile sistem stabil olsun diye)
        setTimeout(() => {
            refreshStudentExamsData();
        }, 1000);
    } else {
        showMessage(result?.message || 'Planlama başarısız', 'error');
    }
});

document.getElementById('clearExams')?.addEventListener('click', async () => {
    if (!confirm('Tüm sınav planlarını silmek istediğinize emin misiniz?')) return;
    
    const result = await apiCall('/exams?confirm=true', 'DELETE');
    
    if (result?.status === 'success') {
        showMessage(`${result.deleted} sınav silindi`, 'success');
        
        // Admin panel'deki sınavları güncelle
        loadExams();
        
        // Öğrenci verilerini DE güncelle (1 saniye gecikme ile sistem stabil olsun diye)
        setTimeout(() => {
            refreshStudentExamsData();
        }, 1000);
    } else {
        showMessage(result?.message || 'Silme başarısız', 'error');
    }
});

// ==================== HOCA PANEL FONKSİYONLARI ====================

// ==================== BÖLÜM YETKİLİSİ PANEL FONKSİYONLARI ====================

// Bölüm yönetimi başlatıldığında çalıştır
async function initDeptPanel() {
    // muh_yetkili için Mühendislik verilerini yükle
    await loadMuhTeachers();
    await loadMuhCourses();
    await loadMuhExams();
}

async function loadMuhTeachers() {
    const result = await apiCall('/muhendislik/ogretim-uyeleri');
    if (!result?.data) return;
    
    const container = document.getElementById('muhTeachersContainer');
    if (!container) return;
    
    if (result.data.length === 0) {
        container.innerHTML = '<div class="empty-state" style="grid-column: 1/-1;">Öğretim üyesi bulunamadı</div>';
        return;
    }
    
    container.innerHTML = result.data.map(t => `
        <div class="teacher-card">
            <div class="teacher-card-header">
                <div class="teacher-card-name">${escapeHtml(t.name)}</div>
                ${t.title ? `<div class="teacher-card-title">${escapeHtml(t.title)}</div>` : ''}
            </div>
            <div class="teacher-card-body">
                <div class="teacher-card-meta"><strong>Bölüm:</strong> ${escapeHtml(t.department_name)}</div>
                <div class="teacher-card-days"><i class="fas fa-calendar"></i> Müsait: ${t.available_days}</div>
            </div>
            <div class="teacher-card-actions">
                <button class="btn-edit" onclick="editDeptTeacher(${t.id}, '${escapeHtml(t.name).replace(/'/g, "\\'")}', '${escapeHtml(t.title || '').replace(/'/g, "\\'")}', '${t.available_days}')">
                    <i class="fas fa-edit"></i> Düzenle
                </button>
                <button class="btn-delete" onclick="deleteDeptTeacher(${t.id}, '${escapeHtml(t.name).replace(/'/g, "\\'")}')">
                    <i class="fas fa-trash"></i> Sil
                </button>
            </div>
        </div>
    `).join('');
}

async function editDeptTeacher(id, name, title, availableDays) {
    openEditDeptTeacherModal(id, name, '', title, availableDays);
}

function openEditDeptTeacherModal(id, name, faculty, title, availableDays) {
    document.getElementById('editDeptTeacherId').value = id;
    document.getElementById('editDeptTeacherName').value = name;
    document.getElementById('editDeptTeacherFaculty').value = faculty || '';
    document.getElementById('editDeptTeacherTitle').value = title || '';
    document.getElementById('editDeptTeacherDays').value = availableDays || 'Mon,Tue,Wed,Thu,Fri';
    document.getElementById('editDeptTeacherModal').style.display = 'flex';
}

function closeEditDeptTeacherModal() {
    document.getElementById('editDeptTeacherModal').style.display = 'none';
}

document.getElementById('editDeptTeacherForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const id = document.getElementById('editDeptTeacherId').value;
    const title = document.getElementById('editDeptTeacherTitle').value.trim();
    const availableDays = document.getElementById('editDeptTeacherDays').value.trim();
    
    const result = await apiCall(`/teachers/${id}`, 'PUT', {
        title: title,
        available_days: availableDays
    });
    
    if (result?.status === 'success') {
        showMessage('Öğretim üyesi güncellendi', 'success');
        closeEditDeptTeacherModal();
        await loadMuhTeachers();
    } else {
        showMessage(result?.message || 'Güncelleme başarısız', 'error');
    }
});

async function deleteDeptTeacher(id, name) {
    if (!confirm(`${name} adlı öğretim üyesini silmek istediğinize emin misiniz?`)) return;
    
    const result = await apiCall(`/teachers/${id}`, 'DELETE');
    
    if (result?.status === 'success') {
        showMessage('Öğretim üyesi silindi', 'success');
        await loadMuhTeachers();
    } else {
        showMessage(result?.message || 'Silme başarısız', 'error');
    }
}

async function loadMuhCourses() {
    const result = await apiCall('/muhendislik/dersler');
    if (!result?.data) return;
    
    const tbody = document.getElementById('muhCoursesTable');
    if (!tbody) return;
    
    tbody.innerHTML = result.data.map(c => `
        <tr style="border-bottom: 1px solid #e5e7eb;">
            <td style="padding: 12px;">${escapeHtml(c.name)}</td>
            <td style="padding: 12px;">${escapeHtml(c.department_name)}</td>
            <td style="padding: 12px;">${escapeHtml(c.teacher_name)}</td>
            <td style="padding: 12px;">${c.exam_duration} dk</td>
            <td style="padding: 12px;">${c.student_count}</td>
        </tr>
    `).join('') || '<tr><td colspan="5" style="padding: 12px; text-align: center; color: #9ca3af;">Veri bulunamadı</td></tr>';
}

async function loadMuhExams() {
    const result = await apiCall('/muhendislik/sinav-programi');
    if (!result?.data) return;
    
    const tbody = document.getElementById('muhExamsTable');
    if (!tbody) return;
    
    if (result.data.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" style="padding: 12px; text-align: center; color: #9ca3af;">Henüz sınav programı oluşturulmamıştır</td></tr>';
        return;
    }
    
    tbody.innerHTML = result.data.map(e => {
        const date = e.slot_start ? new Date(e.slot_start).toLocaleDateString('tr-TR') : '-';
        const time = e.slot_start ? new Date(e.slot_start).toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' }) : '-';
        return `
            <tr style="border-bottom: 1px solid #e5e7eb;">
                <td style="padding: 12px;">${escapeHtml(e.course_name)}</td>
                <td style="padding: 12px;">${escapeHtml(e.room_name)}</td>
                <td style="padding: 12px;">${date}</td>
                <td style="padding: 12px;">${time}</td>
                <td style="padding: 12px;">${escapeHtml(e.teacher_name)}</td>
            </tr>
        `;
    }).join('');
}

async function loadDeptTeachers() {
    const result = await apiCall('/teachers');
    
    if (!result?.data) return;
    
    console.log('📚 Tüm öğretim üyeleri yüklendi:', result.data.length, 'kişi');
    
    // Tüm öğretim üyelerini sakla
    window.allDeptTeachers = result.data;
    
    // Unique fakülteler/department'ler al
    const uniqueDepts = [...new Set(result.data.map(t => t.department_id))].filter(id => id);
    const deptNames = {};
    
    console.log('🏢 Unique department ID\'ler:', uniqueDepts);
    
    // Her department_id için fakülte adını al
    result.data.forEach(t => {
        if (t.department_id && !deptNames[t.department_id]) {
            deptNames[t.department_id] = t.faculty || `Fakülte ${t.department_id}`;
            console.log(`   Dept ${t.department_id}: ${deptNames[t.department_id]}`);
        }
    });
    
    // Fakülte select'ini doldur
    const select = document.getElementById('deptFacultyFilter');
    if (select) {
        const options = '<option value="">-- Fakülte Seç --</option>' +
            uniqueDepts
                .map(id => `<option value="${id}">${escapeHtml(deptNames[id] || `Fakülte ${id}`)}</option>`)
                .join('');
        select.innerHTML = options;
        
        console.log('✅ Dropdown dolduruldu, option sayısı:', uniqueDepts.length);
        
        // Change listener'ı ekle
        select.removeEventListener('change', loadDeptTeachersByFaculty);
        select.addEventListener('change', loadDeptTeachersByFaculty);
        console.log('🔗 Change listener eklendi');
    }
    
    // Başlangıçta tüm öğretim üyelerini göster
    displayDeptTeachers(result.data);
    
    // Arama input'u listener'ı ekle
    const searchInput = document.getElementById('deptTeachersSearch');
    if (searchInput) {
        searchInput.addEventListener('input', searchDeptTeachers);
    }
}

async function loadDeptTeachersByFaculty() {
    const facultyId = parseInt(document.getElementById('deptFacultyFilter')?.value) || null;
    
    console.log('Seçilen fakülte ID:', facultyId);
    console.log('Tüm öğretim üyeleri:', window.allDeptTeachers);
    
    if (!window.allDeptTeachers) return;
    
    let filtered = window.allDeptTeachers;
    
    // Fakülteye göre filtrele
    if (facultyId) {
        filtered = filtered.filter(t => t.department_id === facultyId);
        console.log('Filtrelenen öğretim üyeleri:', filtered);
    }
    
    // Arama input'unu sıfırla
    const searchInput = document.getElementById('deptTeachersSearch');
    if (searchInput) {
        searchInput.value = '';
    }
    
    displayDeptTeachers(filtered);
    
    // Dersler ve Sınavları da güncelle
    await loadDeptCourses();
    await loadDeptExams();
}

function searchDeptTeachers() {
    const searchTerm = document.getElementById('deptTeachersSearch')?.value.toLowerCase().trim() || '';
    const facultyId = parseInt(document.getElementById('deptFacultyFilter')?.value) || null;
    
    if (!window.allDeptTeachers) return;
    
    let filtered = window.allDeptTeachers;
    
    // Fakülteye göre filtrele
    if (facultyId) {
        filtered = filtered.filter(t => t.department_id === facultyId);
    }
    
    // Arama terimine göre filtrele
    if (searchTerm) {
        filtered = filtered.filter(t => {
            const name = (t.name || '').toLowerCase();
            const title = (t.title || '').toLowerCase();
            const faculty = (t.faculty || '').toLowerCase();
            
            return name.includes(searchTerm) || title.includes(searchTerm) || faculty.includes(searchTerm);
        });
    }
    
    console.log('🔍 Arama sonucu:', searchTerm, '→', filtered.length, 'öğretim üyesi');
    displayDeptTeachers(filtered);
}

function displayDeptTeachers(teachers) {
    const container = document.getElementById('deptTeachersList');
    if (!container) return;
    
    if (teachers.length === 0) {
        container.innerHTML = '<div class="empty-state" style="grid-column: 1/-1;">Seçilen kriterlere ait öğretim üyesi bulunamadı</div>';
        return;
    }
    
    // Admin panelindeki gibi kartlar
    container.innerHTML = teachers.map(t => `
        <div class="item-card" data-teacher-id="${t.id}">
            <div class="item-card-header">
                <div class="item-card-title">${escapeHtml(t.name)}</div>
            </div>
            <div class="item-card-body">
                ${t.faculty ? `<div class="item-card-meta"><strong>Fakülte:</strong> ${escapeHtml(t.faculty)}</div>` : ''}
                <div class="item-card-badge"><i class="fas fa-briefcase"></i> ${escapeHtml(t.title || 'Unvan belirtilmemiş')}</div>
                <div class="item-card-badge"><i class="fas fa-calendar"></i> Müsait: ${escapeHtml(t.available_days || 'Belirtilmemiş')}</div>
            </div>
            <div class="item-card-actions">
                <button class="btn-edit" data-action="edit" data-faculty="${escapeHtml(t.faculty || '')}" data-title="${escapeHtml(t.title || '')}" data-days="${escapeHtml(t.available_days || 'Mon,Tue,Wed,Thu,Fri')}" title="Düzenle">
                    <i class="fas fa-edit"></i> Düzenle
                </button>
                <button class="btn-delete" data-action="delete" title="Sil">
                    <i class="fas fa-trash"></i> Sil
                </button>
            </div>
        </div>
    `).join('');
    
    // Event listeners ekle
    container.querySelectorAll('.btn-edit').forEach(btn => {
        btn.addEventListener('click', function() {
            const card = this.closest('.item-card');
            const id = parseInt(card.dataset.teacherId);
            const name = card.querySelector('.item-card-title').textContent;
            const faculty = this.dataset.faculty;
            const title = this.dataset.title;
            const days = this.dataset.days;
            editDeptTeacher(id, name, faculty, title, days);
        });
    });
    
    container.querySelectorAll('.btn-delete').forEach(btn => {
        btn.addEventListener('click', function() {
            const card = this.closest('.item-card');
            const id = parseInt(card.dataset.teacherId);
            const name = card.querySelector('.item-card-title').textContent;
            deleteDeptTeacher(id, name);
        });
    });
}

async function editDeptTeacher(id, name, faculty, title, availableDays) {
    openEditDeptTeacherModal(id, name, faculty, title, availableDays);
}

function openEditDeptTeacherModal(id, name, faculty, title, availableDays) {
    document.getElementById('editDeptTeacherId').value = id;
    document.getElementById('editDeptTeacherName').value = name;
    document.getElementById('editDeptTeacherFaculty').value = faculty || '';
    document.getElementById('editDeptTeacherTitle').value = title || '';
    document.getElementById('editDeptTeacherDays').value = availableDays || 'Mon,Tue,Wed,Thu,Fri';
    document.getElementById('editDeptTeacherModal').style.display = 'flex';
}

function closeEditDeptTeacherModal() {
    document.getElementById('editDeptTeacherModal').style.display = 'none';
}

document.getElementById('editDeptTeacherForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const id = document.getElementById('editDeptTeacherId').value;
    const title = document.getElementById('editDeptTeacherTitle').value.trim();
    const availableDays = document.getElementById('editDeptTeacherDays').value.trim();
    
    const result = await apiCall(`/teachers/${id}`, 'PUT', {
        title: title,
        available_days: availableDays
    });
    
    if (result?.status === 'success') {
        showMessage('Öğretim üyesi güncellendi', 'success');
        closeEditDeptTeacherModal();
        await initDeptPanel();
    } else {
        showMessage(result?.message || 'Güncelleme başarısız', 'error');
    }
});

async function deleteDeptTeacher(id, name) {
    if (!confirm(`${name} adlı öğretim üyesini silmek istediğinize emin misiniz?`)) return;
    
    const result = await apiCall(`/teachers/${id}`, 'DELETE');
    
    if (result?.status === 'success') {
        showMessage('Öğretim üyesi silindi', 'success');
        await initDeptPanel();
    } else {
        showMessage(result?.message || 'Silme başarısız', 'error');
    }
}

async function loadDeptCourses() {
    const result = await apiCall(`/courses?department_id=${currentUser.department_id}`);
    
    if (!result?.data) return;
    
    // Seçili fakülteyi al
    const facultyId = parseInt(document.getElementById('deptFacultyFilter')?.value) || null;
    
    // Eğer fakülte seçiliyse, sadece o fakültenin derslerini göster
    let deptCourses = result.data;
    if (facultyId) {
        deptCourses = result.data.filter(c => c.department_id === facultyId);
    }
    
    const container = document.getElementById('deptCoursesList');
    if (!container) return;
    
    if (deptCourses.length === 0) {
        container.innerHTML = '<div class="empty-state">Bölüme ait ders yok</div>';
        return;
    }
    
    container.innerHTML = deptCourses.map(c => `
        <div class="course-item">
            <div class="course-info">
                <div class="course-name">${escapeHtml(c.name)} (${escapeHtml(c.code)})</div>
                <div class="course-detail">
                    👨‍🏫 ${escapeHtml(c.teacher_name || 'Atanmamış')} |
                    👥 ${c.student_count} öğrenci |
                    ⏱️ ${c.exam_duration} dk
                </div>
            </div>
        </div>
    `).join('');
}

async function loadDeptExams() {
    const result = await apiCall(`/exams`);
    
    if (!result?.data) return;
    
    // Seçili fakülteyi al
    const facultyId = parseInt(document.getElementById('deptFacultyFilter')?.value) || null;
    
    // Eğer fakülte seçiliyse, sadece o fakültenin sınavlarını göster
    let deptExams = result.data;
    if (facultyId) {
        deptExams = result.data.filter(e => e.department_id === facultyId);
    }
    
    const container = document.getElementById('deptExamsList');
    if (!container) return;
    
    if (deptExams.length === 0) {
        container.innerHTML = '<div class="empty-exams"><i class="fas fa-calendar-times"></i>Henüz sınav planı yok</div>';
        return;
    }
    
    const tableHTML = `
        <table class="exams-table">
            <thead>
                <tr>
                    <th>📅 Tarih</th>
                    <th>⏰ Saat</th>
                    <th>📚 Ders</th>
                    <th>👨‍🏫 Hoca</th>
                    <th>🚪 Derslik</th>
                    <th>⏱️ Süre</th>
                </tr>
            </thead>
            <tbody>
                ${deptExams.map(e => `
                    <tr>
                        <td class="exam-date">${e.slot_start?.substring(0,10) || 'N/A'}</td>
                        <td class="exam-time">${e.slot_start?.substring(11,16) || 'N/A'}</td>
                        <td class="exam-course">${escapeHtml(e.course_name)}</td>
                        <td class="exam-teacher">${escapeHtml(e.teacher_name)}</td>
                        <td><span class="exam-classroom">${escapeHtml(e.room_name)}</span></td>
                        <td class="exam-duration">${e.duration || 60} dk</td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
    
    container.innerHTML = tableHTML;
}

async function loadTeacherExams() {
    const result = await apiCall(`/exams?teacher_id=${currentUser.teacher_id}`);
    
    if (!result?.data) return;
    
    const container = document.getElementById('teacherExamsList');
    if (!container) return;
    
    if (result.data.length === 0) {
        container.innerHTML = '<div class="empty-exams"><i class="fas fa-calendar-times"></i>Henüz sınav planı yok</div>';
        return;
    }
    
    const tableHTML = `
        <table class="exams-table">
            <thead>
                <tr>
                    <th>📅 Tarih</th>
                    <th>⏰ Saat</th>
                    <th>📚 Ders</th>
                    <th>🚪 Derslik</th>
                    <th>⏱️ Süre</th>
                </tr>
            </thead>
            <tbody>
                ${result.data.map(e => `
                    <tr>
                        <td class="exam-date">${e.slot_start?.substring(0,10) || 'N/A'}</td>
                        <td class="exam-time">${e.slot_start?.substring(11,16) || 'N/A'}</td>
                        <td class="exam-course">${escapeHtml(e.course_name)}</td>
                        <td><span class="exam-classroom">${escapeHtml(e.room_name)}</span></td>
                        <td class="exam-duration">${e.duration || 60} dk</td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
    
    container.innerHTML = tableHTML;
}

// ==================== ÖĞRENCİ PANEL FONKSİYONLARI ====================

let allStudentExamsData = [];
let selectedStudentFacultyId = null;
let studentExamsRefreshInterval = null;

// Öğrenci sınav verilerini güncelle - admin/dept tarafından çağrıldığında
async function refreshStudentExamsData() {
    const result = await apiCall('/exams');
    if (result?.data) {
        // STEP 1: Her zaman global veriyi güncelle (önemli!)
        allStudentExamsData = result.data;
        
        // STEP 2: Eğer öğrenci paneli görünüyorsa UI'ı refresh et
        const studentPanel = document.getElementById('studentPanel');
        if (studentPanel && studentPanel.style.display !== 'none') {
            const container = document.getElementById('studentExamsList');
            if (container && container.style.display !== 'none') {
                // Öğrenci paneli açık, UI'ı güncelle
                if (selectedStudentFacultyId) {
                    displayStudentWeeklySchedule(selectedStudentFacultyId);
                } else {
                    if (allStudentExamsData.length === 0) {
                        const tabsContainer = document.getElementById('studentFacultyTabs');
                        if (tabsContainer) tabsContainer.innerHTML = '';
                        container.innerHTML = '<div class="empty-exams"><i class="fas fa-calendar-times"></i>Henüz planlanmış sınav yok</div>';
                    } else {
                        loadStudentFacultyTabs();
                    }
                }
            }
        }
    }
}

async function loadStudentExams() {
    const result = await apiCall('/exams');
    
    if (!result?.data) return;
    
    allStudentExamsData = result.data;
    
    const container = document.getElementById('studentExamsList');
    if (!container) return;
    
    if (allStudentExamsData.length === 0) {
        const tabsContainer = document.getElementById('studentFacultyTabs');
        if (tabsContainer) tabsContainer.innerHTML = '';
        container.innerHTML = '<div class="empty-exams"><i class="fas fa-calendar-times"></i>Henüz planlanmış sınav yok</div>';
        return;
    }
    
    // Sınavların department_id'si var mı kontrol et
    const hasValidDepartments = allStudentExamsData.some(exam => exam.department_id);
    
    if (!hasValidDepartments) {
        // Department_id yoksa basit tablo göster
        const tabsContainer = document.getElementById('studentFacultyTabs');
        if (tabsContainer) tabsContainer.innerHTML = '';
        displaySimpleStudentExamTable();
        return;
    }
    
    // Fakülte listesi oluştur
    await loadStudentFacultyTabs();
    
    // Periyodik yenileme başlat (her 15 saniyede bir)
    startStudentExamsRefresh();
}

function displaySimpleStudentExamTable() {
    const container = document.getElementById('studentExamsList');
    if (!container) return;
    
    const tableHTML = `
        <table class="exams-table">
            <thead>
                <tr>
                    <th>📅 Tarih</th>
                    <th>⏰ Saat</th>
                    <th>📚 Ders</th>
                    <th>👨‍🏫 Hoca</th>
                    <th>🚪 Derslik</th>
                    <th>⏱️ Süre</th>
                </tr>
            </thead>
            <tbody>
                ${allStudentExamsData.map(e => `
                    <tr>
                        <td class="exam-date">${e.slot_start?.substring(0,10) || 'N/A'}</td>
                        <td class="exam-time">${e.slot_start?.substring(11,16) || 'N/A'}</td>
                        <td class="exam-course">${escapeHtml(e.course_name)}</td>
                        <td class="exam-teacher">${escapeHtml(e.teacher_name || 'Atanmamış')}</td>
                        <td><span class="exam-classroom">${escapeHtml(e.room_name)}</span></td>
                        <td class="exam-duration">${e.duration || 60} dk</td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
    
    container.innerHTML = tableHTML;
}

async function loadStudentFacultyTabs() {
    const deptResult = await apiCall('/departments');
    if (!deptResult?.data) return;
    
    const faculties = deptResult.data.filter(d => d.name !== 'Bilgisayar Mühendisliği');
    
    const tabsContainer = document.getElementById('studentFacultyTabs');
    if (!tabsContainer) return;
    
    tabsContainer.innerHTML = faculties.map(faculty => `
        <button class="faculty-tab" data-faculty-id="${faculty.id}">
            ${escapeHtml(faculty.name)}
        </button>
    `).join('');
    
    // Tab tıklama olayları
    tabsContainer.querySelectorAll('.faculty-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            tabsContainer.querySelectorAll('.faculty-tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            selectedStudentFacultyId = parseInt(tab.dataset.facultyId);
            displayStudentWeeklySchedule(selectedStudentFacultyId);
        });
    });
    
    // İlk fakülteyi varsayılan olarak seç
    if (faculties.length > 0) {
        const firstTab = tabsContainer.querySelector('.faculty-tab');
        if (firstTab) firstTab.click();
    } else {
        // Hiç fakülte yoksa basit tablo göster
        displaySimpleStudentExamTable();
    }
}

function displayStudentWeeklySchedule(facultyId) {
    const container = document.getElementById('studentExamsList');
    if (!container) return;
    
    // Fakülte sınavlarını filtrele
    const facultyExams = allStudentExamsData.filter(exam => exam.department_id === facultyId);
    
    if (facultyExams.length === 0) {
        container.innerHTML = '<div class="empty-exams"><i class="fas fa-calendar-times"></i>Bu fakülte için henüz planlanmış sınav yok</div>';
        return;
    }
    
    // Sınavları tarihlere göre grupla
    const examsByDate = {};
    const timeSlots = new Set();
    
    facultyExams.forEach(exam => {
        const datetime = exam.slot_start || '';
        const date = datetime.substring(0, 10);
        const time = datetime.substring(11, 16);
        
        if (!examsByDate[date]) {
            examsByDate[date] = {};
        }
        
        if (!examsByDate[date][time]) {
            examsByDate[date][time] = [];
        }
        
        examsByDate[date][time].push(exam);
        timeSlots.add(time);
    });
    
    // Tarih ve saat dilimlerini sırala
    const sortedDates = Object.keys(examsByDate).sort();
    const sortedTimeSlots = Array.from(timeSlots).sort();
    
    // Haftaları böl (her hafta 5 gün)
    const weeks = [];
    for (let i = 0; i < sortedDates.length; i += 5) {
        weeks.push(sortedDates.slice(i, i + 5));
    }
    
    // Her hafta için tablo oluştur
    const weeklyHTML = weeks.map((weekDates, weekIndex) => {
        const weekNumber = weekIndex + 1;
        const firstDate = new Date(weekDates[0]);
        const lastDate = new Date(weekDates[weekDates.length - 1]);
        
        const weekTitle = `${weekNumber}. Hafta (${formatDate(firstDate)} - ${formatDate(lastDate)})`;
        
        const tableHTML = `
            <div class="week-schedule">
                <div class="week-title">${weekTitle}</div>
                <table class="schedule-table">
                    <thead>
                        <tr>
                            <th>Tarih / Saat</th>
                            ${sortedTimeSlots.map(time => `<th>${time}</th>`).join('')}
                        </tr>
                    </thead>
                    <tbody>
                        ${weekDates.map(date => {
                            const dateObj = new Date(date);
                            const dayName = getDayName(dateObj);
                            const formattedDate = formatDate(dateObj);
                            
                            return `
                                <tr>
                                    <td><strong>${dayName}</strong><br>${formattedDate}</td>
                                    ${sortedTimeSlots.map(time => {
                                        const exams = examsByDate[date]?.[time] || [];
                                        
                                        if (exams.length === 0) {
                                            return '<td class="empty-cell">-</td>';
                                        }
                                        
                                        return `
                                            <td>
                                                ${exams.map(exam => `
                                                    <div class="exam-cell">
                                                        <div class="exam-cell-title">${escapeHtml(exam.course_code || exam.course_name)}</div>
                                                        <div class="exam-cell-teacher">${escapeHtml(exam.teacher_name || 'Atanmamış')}</div>
                                                        <div class="exam-cell-room">📍 ${escapeHtml(exam.room_name)}</div>
                                                    </div>
                                                `).join('')}
                                            </td>
                                        `;
                                    }).join('')}
                                </tr>
                            `;
                        }).join('')}
                    </tbody>
                </table>
            </div>
        `;
        
        return tableHTML;
    }).join('');
    
    container.innerHTML = weeklyHTML;
}

// Öğrenci sınavlarının periyodik yenilenmesi
function startStudentExamsRefresh() {
    // Önceki interval'i temizle
    if (studentExamsRefreshInterval) {
        clearInterval(studentExamsRefreshInterval);
    }
    
    // Her 15 saniyede bir sınavları güncelle
    studentExamsRefreshInterval = setInterval(async () => {
        const result = await apiCall('/exams');
        
        if (result?.data) {
            const newData = JSON.stringify(result.data);
            const oldData = JSON.stringify(allStudentExamsData);
            
            // Veri değişmişse güncelle
            if (newData !== oldData) {
                allStudentExamsData = result.data;
                
                // Sadece öğrenci paneli görünüyorsa UI güncelle
                const studentPanel = document.getElementById('studentPanel');
                if (studentPanel && studentPanel.style.display !== 'none') {
                    const container = document.getElementById('studentExamsList');
                    if (container && container.style.display !== 'none') {
                        if (selectedStudentFacultyId) {
                            displayStudentWeeklySchedule(selectedStudentFacultyId);
                        } else {
                            loadStudentExams();
                        }
                    }
                }
            }
        }
    }, 15000);
}

function stopStudentExamsRefresh() {
    if (studentExamsRefreshInterval) {
        clearInterval(studentExamsRefreshInterval);
        studentExamsRefreshInterval = null;
    }
}

// ==================== EXCEL YÜKLEME ====================

document.getElementById('excelUploadForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const fileInput = document.getElementById('excelFile');
    const courseCode = document.getElementById('excelCourseCode').value.trim();
    
    if (!fileInput.files[0]) {
        showMessage('Dosya seçiniz', 'error');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    if (courseCode) formData.append('course_code', courseCode);
    
    try {
        const response = await fetch(`${API_BASE}/excel/upload-classlists`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${authToken}` },
            body: formData
        });
        
        const result = await response.json();
        
        if (result?.status === 'success') {
            showMessage(`${result.students_imported} öğrenci içe aktarıldı`, 'success');
            document.getElementById('excelUploadForm').reset();
            loadCourses();
        } else {
            showMessage(result?.message || 'Yükleme başarısız', 'error');
        }
    } catch (error) {
        showMessage('Yükleme hatası: ' + error.message, 'error');
    }
});

// Klasörden sınıf listeleri import
document.getElementById('importClasslistsBtn')?.addEventListener('click', async () => {
    const folderInput = document.getElementById('classlistFolderInput');
    if (!folderInput.files || folderInput.files.length === 0) {
        showMessage('Lütfen bir klasör seçin', 'error');
        return;
    }
    
    const formData = new FormData();
    for (let file of folderInput.files) {
        formData.append('files', file);
    }
    
    showMessage(`${folderInput.files.length} dosya yüklenip işleniyor...`, 'success', 8000);
    
    try {
        const response = await fetch(`${API_BASE}/excel/import-classlists`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${authToken}` },
            body: formData
        });
        
        const result = await response.json();
        
        if (result?.status === 'success') {
            const imported = result.import?.enrollments_created || 0;
            const processed = result.import?.files_processed || 0;
            const errors = result.import?.errors?.length || 0;
            showMessage(`İçe aktarma tamamlandı: ${processed} dosya işlendi, ${imported} kayıt eklendi${errors > 0 ? `, ${errors} hata` : ''}`, 'success');
            loadCourses();
        } else {
            showMessage(result?.message || 'İçe aktarma başarısız', 'error');
        }
    } catch (error) {
        showMessage('Yükleme hatası: ' + error.message, 'error');
    }
});

// Derslik yakınlık import
document.getElementById('importProximityBtn')?.addEventListener('click', async () => {
    const fileInput = document.getElementById('proximityFileInput');
    if (!fileInput.files || !fileInput.files[0]) {
        showMessage('Lütfen bir dosya seçin', 'error');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    
    showMessage('Derslik yakınlık içe aktarma başlatılıyor...', 'success', 6000);
    
    try {
        const response = await fetch(`${API_BASE}/excel/import-proximity`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${authToken}` },
            body: formData
        });
        
        const result = await response.json();
        
        if (result?.status === 'success') {
            showMessage(`Yakınlık kayıtları: ${result.total} (yeni: ${result.created}, güncellenen: ${result.updated})`, 'success');
        } else {
            showMessage(result?.message || 'İçe aktarma başarısız', 'error');
        }
    } catch (error) {
        showMessage('Yükleme hatası: ' + error.message, 'error');
    }
});

// Kapasite import
document.getElementById('importCapacityBtn')?.addEventListener('click', async () => {
    const fileInput = document.getElementById('capacityFileInput');
    if (!fileInput.files || !fileInput.files[0]) {
        showMessage('Lütfen bir dosya seçin', 'error');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    
    showMessage('Kapasite bilgileri içe aktarılıyor...', 'success', 6000);
    
    try {
        const response = await fetch(`${API_BASE}/excel/import-capacity`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${authToken}` },
            body: formData
        });
        
        const result = await response.json();
        
        if (result?.status === 'success' || result?.status === 'partial') {
            const msg = [];
            if (result.created_classrooms) msg.push(`${result.created_classrooms} derslik eklendi`);
            if (result.updated_classrooms) msg.push(`${result.updated_classrooms} derslik güncellendi`);
            if (result.created_courses) msg.push(`${result.created_courses} ders eklendi`);
            if (result.updated_courses) msg.push(`${result.updated_courses} ders güncellendi`);
            showMessage(`Kapasite içe aktarma tamamlandı: ${msg.join(', ')}`, result.status === 'partial' ? 'warning' : 'success');
            loadClassrooms();
            loadCourses();
        } else {
            showMessage(result?.message || 'İçe aktarma başarısız', 'error');
        }
    } catch (error) {
        showMessage('Yükleme hatası: ' + error.message, 'error');
    }
});

// Akademik Kadro Excel Import
document.getElementById('importTeachersBtn')?.addEventListener('click', async () => {
    const fileInput = document.getElementById('teachersFileInput');
    if (!fileInput.files || !fileInput.files[0]) {
        showMessage('Lütfen akademik_kadro.xlsx dosyasını seçin', 'error');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    
    const btn = document.getElementById('importTeachersBtn');
    const originalText = btn.innerHTML;
    
    try {
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> İşleniyor...';
        
        showMessage('Akademik kadro verisi işleniyor...', 'success', 8000);
        
        const response = await fetch(`${API_BASE}/excel/import-teachers`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${authToken}` },
            body: formData
        });
        
        const result = await response.json();
        
        if (result?.status === 'success') {
            const message = `✅ ${result.created_teachers} yeni hoca eklendi, ${result.updated_teachers} hoca güncellendi, ${result.created_faculties} fakülte oluşturuldu`;
            showMessage(message, 'success', 8000);
            fileInput.value = '';
            
            // Listeler yenileme
            setTimeout(() => {
                loadTeachers();
                loadCourses();
            }, 500);
        } else {
            showMessage(`❌ Hata: ${result?.message || 'İçe aktarma başarısız'}`, 'error', 6000);
        }
    } catch (error) {
        showMessage(`❌ Yükleme hatası: ${error.message}`, 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
});


// ==================== EVENT LİSTENERS ====================

document.getElementById('loginForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    await login();
});

document.getElementById('loginBtn')?.addEventListener('click', login);

document.getElementById('logoutBtn')?.addEventListener('click', () => {
    if (confirm('Çıkış yapılsın mı?')) {
        logout();
    }
});

// Enter tuşu ile login
document.getElementById('password')?.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') login();
});

// ==================== CRUD OPERATIONS ====================

// Teacher CRUD
function editTeacher(id, name, days) {
    document.getElementById('editTeacherId').value = id;
    document.getElementById('editTeacherName').value = name;
    document.getElementById('editTeacherDays').value = days;
    
    // Öğretim üyesini ara ve bölümünü set et
    const teacher = allTeachersData.find(t => t.id === id);
    if (teacher && teacher.department_id) {
        document.getElementById('editTeacherDepartment').value = teacher.department_id;
    } else {
        document.getElementById('editTeacherDepartment').value = '';
    }
    
    document.getElementById('editTeacherModal').style.display = 'flex';
}

function closeEditTeacherModal() {
    document.getElementById('editTeacherModal').style.display = 'none';
}

document.getElementById('editTeacherForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const id = document.getElementById('editTeacherId').value;
    const name = document.getElementById('editTeacherName').value.trim();
    const days = document.getElementById('editTeacherDays').value.trim();
    const departmentId = parseInt(document.getElementById('editTeacherDepartment').value) || null;
    
    const result = await apiCall(`/teachers/${id}`, 'PUT', { 
        name, 
        available_days: days,
        department_id: departmentId
    });
    
    if (result?.status === 'success') {
        showMessage('Öğretim üyesi güncellendi', 'success');
        closeEditTeacherModal();
        loadTeachers();
    } else {
        showMessage(result?.message || 'Güncelleme başarısız', 'error');
    }
});

async function deleteTeacher(id, name) {
    if (!confirm(`"${name}" adlı öğretim üyesini silmek istediğinize emin misiniz?`)) return;
    
    const result = await apiCall(`/teachers/${id}`, 'DELETE');
    
    if (result?.status === 'success') {
        showMessage('Öğretim üyesi silindi', 'success');
        loadTeachers();
    } else {
        showMessage(result?.message || 'Silme başarısız', 'error');
    }
}

// Classroom CRUD
function editClassroom(id, name, capacity) {
    document.getElementById('editClassroomId').value = id;
    document.getElementById('editClassroomName').value = name;
    document.getElementById('editClassroomCapacity').value = capacity;
    document.getElementById('editClassroomModal').style.display = 'flex';
}

function closeEditClassroomModal() {
    document.getElementById('editClassroomModal').style.display = 'none';
}

document.getElementById('editClassroomForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const id = document.getElementById('editClassroomId').value;
    const name = document.getElementById('editClassroomName').value.trim();
    const capacity = parseInt(document.getElementById('editClassroomCapacity').value) || 30;
    
    const result = await apiCall(`/classrooms/${id}`, 'PUT', { name, capacity });
    
    if (result?.status === 'success') {
        showMessage('Derslik güncellendi', 'success');
        closeEditClassroomModal();
        loadClassrooms();
    } else {
        showMessage(result?.message || 'Güncelleme başarısız', 'error');
    }
});

async function deleteClassroom(id, name) {
    if (!confirm(`"${name}" adlı dersliği silmek istediğinize emin misiniz?`)) return;
    
    const result = await apiCall(`/classrooms/${id}`, 'DELETE');
    
    if (result?.status === 'success') {
        showMessage('Derslik silindi', 'success');
        loadClassrooms();
    } else {
        showMessage(result?.message || 'Silme başarısız', 'error');
    }
}

// Course CRUD
async function editCourse(id) {
    // Dersi getir
    const result = await apiCall('/courses');
    if (!result?.data) return;
    
    const course = result.data.find(c => c.id === id);
    if (!course) return;
    
    document.getElementById('editCourseId').value = id;
    document.getElementById('editCourseName').value = course.name;
    document.getElementById('editCourseCode').value = course.code || '';
    document.getElementById('editCourseDepartment').value = course.department_id || '';
    document.getElementById('editCourseTeacher').value = course.teacher_id || '';
    document.getElementById('editCourseStudentCount').value = course.student_count || 0;
    document.getElementById('editCourseExamDuration').value = course.exam_duration || 60;
    document.getElementById('editCourseModal').style.display = 'flex';
}

function closeEditCourseModal() {
    document.getElementById('editCourseModal').style.display = 'none';
}

document.getElementById('editCourseForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const id = document.getElementById('editCourseId').value;
    const name = document.getElementById('editCourseName').value.trim();
    const code = document.getElementById('editCourseCode').value.trim();
    const departmentId = parseInt(document.getElementById('editCourseDepartment').value) || null;
    const teacherId = parseInt(document.getElementById('editCourseTeacher').value) || null;
    const studentCount = parseInt(document.getElementById('editCourseStudentCount').value) || 0;
    const examDuration = parseInt(document.getElementById('editCourseExamDuration').value) || 60;
    
    const result = await apiCall(`/courses/${id}`, 'PUT', {
        name,
        code,
        department_id: departmentId,
        teacher_id: teacherId,
        student_count: studentCount,
        exam_duration: examDuration
    });
    
    if (result?.status === 'success') {
        showMessage('Ders güncellendi', 'success');
        closeEditCourseModal();
        loadCourses();
    } else {
        showMessage(result?.message || 'Güncelleme başarısız', 'error');
    }
});

async function deleteCourse(id, name) {
    if (!confirm(`"${name}" adlı dersi silmek istediğinize emin misiniz?`)) return;
    
    const result = await apiCall(`/courses/${id}`, 'DELETE');
    
    if (result?.status === 'success') {
        showMessage('Ders silindi', 'success');
        loadCourses();
    } else {
        showMessage(result?.message || 'Silme başarısız', 'error');
    }
}

// ==================== SAYFAnın YÜKLENMESİ ====================

document.addEventListener('DOMContentLoaded', () => {
    createParticles();
    checkLogin();
});

function createParticles() {
    const container = document.getElementById('particles');
    if (!container) return;
    
    for (let i = 0; i < 50; i++) {
        const particle = document.createElement('div');
        particle.className = 'particle';
        particle.style.left = Math.random() * 100 + '%';
        particle.style.top = Math.random() * 100 + '%';
        particle.style.animationDelay = Math.random() * 6 + 's';
        particle.style.animationDuration = (Math.random() * 3 + 3) + 's';
        container.appendChild(particle);
    }
}
