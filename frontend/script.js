// ==========================================
// 1. HELPER FUNCTIONS
// ==========================================

function getTournamentIdFromUrl() {
    // Looks at the URL bar to find the ID (e.g. /bracket/123 -> returns 123)
    const pathSegments = window.location.pathname.split('/');
    return pathSegments[pathSegments.length - 1];
}

let countdownInterval;
function startTimer(endTimeStr) {
    clearInterval(countdownInterval);
    if (!endTimeStr) return;
    
    // Ensure UTC format to avoid timezone bugs
    if (!endTimeStr.endsWith('Z')) endTimeStr += 'Z';
    const endTime = new Date(endTimeStr).getTime();

    function update() {
        const now = new Date().getTime();
        const distance = endTime - now;
        const timerElement = document.getElementById('timer');
        
        if (!timerElement) return;

        if (distance < 0) {
            clearInterval(countdownInterval);
            timerElement.innerHTML = "Round Ended! Refreshing...";
            setTimeout(() => window.location.reload(), 2000);
            return;
        }

        const hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((distance % (1000 * 60)) / 1000);

        timerElement.innerHTML = `${hours}h ${minutes}m ${seconds}s remaining`;
    }

    update(); // Run immediately
    countdownInterval = setInterval(update, 1000);
}

// ==========================================
// 2. AUTHENTICATION (ADMIN)
// ==========================================

const AUTH_KEY = "lorian_admin_token";

function isLoggedIn() {
    return localStorage.getItem(AUTH_KEY) !== null;
}

async function loginAdmin() {
    const password = prompt("Enter Site Admin Password:");
    if (!password) return;

    try {
        const response = await fetch('/api/admin/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ password })
        });

        if (response.ok) {
            const data = await response.json();
            localStorage.setItem(AUTH_KEY, data.access_token);
            alert("Logged in successfully!");
            window.location.reload(); 
        } else {
            alert("Wrong password");
        }
    } catch (e) {
        console.error(e);
        alert("Login error");
    }
}

function logoutAdmin() {
    localStorage.removeItem(AUTH_KEY);
    window.location.href = "/";
}

// Wrapper for Fetch that adds the Admin Token automatically
async function authFetch(url, options = {}) {
    const token = localStorage.getItem(AUTH_KEY);
    if (!token) {
        alert("You must be logged in!");
        window.location.href = "/";
        return null;
    }

    if (!options.headers) options.headers = {};
    options.headers['Authorization'] = `Bearer ${token}`;
    options.headers['Content-Type'] = 'application/json';

    const response = await fetch(url, options);
    
    if (response.status === 401) {
        alert("Session expired. Please login again.");
        logoutAdmin();
        return null;
    }
    
    return response;
}

// ==========================================
// 3. VOTING LOGIC
// ==========================================

async function vote(matchId, option, btnElement) {
    const tournamentId = getTournamentIdFromUrl();
    
    try {
        const response = await fetch(`/api/vote/vote/${tournamentId}/${matchId}/${option}`, {
            method: 'POST'
        });
        
        if (!response.ok) {
            const err = await response.json();
            alert(err.detail || "Voting failed");
            window.location.reload();
        }
    } catch (error) {
        console.error('Error:', error);
    }
}