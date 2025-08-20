// 🎯 SIMPLE EXPLANATION: What this API class does and why you need it
// =======================================================================

/*
🤔 WHAT IS THIS CLASS?
Think of this API class like a "WAITER" in a restaurant:

1. 🏠 You (frontend) want to order food (data) from the kitchen (backend server)
2. 🚶‍♂️ The waiter (API class) takes your order and brings back the food
3. 🛡️ The waiter also handles problems (errors) and follows rules (authentication)

🎯 PURPOSE: 
- Make talking to your backend server EASY and CONSISTENT
- Handle errors automatically 
- Add authentication tokens automatically
- Organize all your server endpoints in one place

📍 BEHAVIOR:
- You call: API.get('users/') 
- It sends: GET request to http://localhost:8080/api/users/
- You get back: Clean data or clear error message
*/

import API from '../api.js';

// =======================================================================
// 📖 REAL WORLD EXAMPLES - How you actually use this class
// =======================================================================

// Example 1: Get a list of users (like getting a menu from waiter)
export async function getUsers() {
    try {
        const users = await API.get(API.USER); // API.USER = 'users/user/'
        console.log('Got users:', users);
        return users;
    } catch (error) {
        console.log('Error getting users:', error.message);
        return [];
    }
}

// Example 2: Create a new user (like ordering food)
export async function createUser(userData) {
    try {
        const newUser = await API.post(API.USER, {
            name: userData.name,
            email: userData.email
        });
        console.log('User created:', newUser);
        return newUser;
    } catch (error) {
        if (error.message.includes('422')) {
            console.log('Invalid user data - check your inputs');
        }
        throw error;
    }
}

// Example 3: Get devices from your infrastructure 
export async function getDevices() {
    try {
        const devices = await API.get(API.DEVICE); // API.DEVICE = 'infrastructure/device/'
        return devices;
    } catch (error) {
        console.log('Could not load devices:', error.message);
        return [];
    }
}

// =======================================================================
// 🔧 HOW IT WORKS UNDER THE HOOD (simplified)
// =======================================================================

/*
When you call: API.get('users/')

1. 🛠️ Builds full URL: 'http://localhost:8080/api/' + 'users/' = 'http://localhost:8080/api/users/'
2. 🔑 Adds authentication headers automatically (if you set them up)
3. 📡 Sends HTTP GET request to that URL
4. ⏰ Waits for response (with optional timeout)
5. ✅ If success (200): Returns clean data
6. ❌ If error (404, 500, etc): Throws clear error message
7. 🐛 Logs everything for debugging

WITHOUT this class, you'd have to write this EVERY TIME:
*/

// 😭 WITHOUT API class - you'd write this mess everywhere:
async function getUsersTheHardWay() {
    try {
        const response = await fetch('http://localhost:8080/api/users/', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + localStorage.getItem('token') // repetitive!
            }
        });

        if (!response.ok) {
            if (response.status === 404) {
                throw new Error('Users not found');
            } else if (response.status === 500) {
                throw new Error('Server error');
            }
            // ... handle every error code manually
        }

        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error:', error);
        throw error;
    }
}

// 😍 WITH API class - you write this:
async function getUsersTheEasyWay() {
    return await API.get(API.USER); // That's it! 🎉
}

// =======================================================================
// 🏗️ WHAT ARE THE ENDPOINTS FOR?
// =======================================================================

/*
The endpoints (USER, DEVICE, etc.) are like a PHONE BOOK for your backend:

API.USER = 'users/user/'           → Manage users
API.DEVICE = 'infrastructure/device/' → Manage IoT devices  
API.WORKSPACE = 'organizations/workspace/' → Manage workspaces
API.TOKEN = 'token/'               → Handle authentication

Instead of remembering URLs, you use clear names:
❌ Hard to remember: API.get('infrastructure/device/')
✅ Easy to remember: API.get(API.DEVICE)
*/

// =======================================================================
// 🎭 WHAT ARE INTERCEPTORS?
// =======================================================================

/*
Interceptors are like AUTOMATIC RULES that run before/after every request:

🔑 Request Interceptor: "Always add my authentication token"
🔄 Response Interceptor: "If token expired, refresh it automatically"

Think of it like:
- 🔑 Automatic ID check before entering a building
- 🔄 Automatic renewal of expired ID cards
*/

function setupAuthentication() {
    // This runs BEFORE every request automatically
    API.addRequestInterceptor(async (config) => {
        const token = localStorage.getItem('authToken');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    });

    // This runs AFTER every response automatically  
    API.addResponseInterceptor(async (response) => {
        if (response.status === 401) {
            console.log('Token expired - redirecting to login');
            window.location.href = '/login';
        }
        return response;
    });
}

// =======================================================================
// 🚀 SUMMARY: Why use this class?
// =======================================================================

/*
✅ BENEFITS:
1. 📝 Write less code (no repetitive fetch() calls)
2. 🛡️ Automatic error handling 
3. 🔑 Automatic authentication
4. 📍 Organized endpoints (like a phone book)
5. 🐛 Better debugging and logging
6. ⏰ Timeouts to prevent hanging requests
7. 🔄 Automatic token refresh

❌ WITHOUT this class:
- Repeat same fetch() code everywhere
- Handle errors manually every time  
- Remember complex URLs
- Add authentication headers manually
- Debug network issues manually

🎯 BOTTOM LINE:
This class makes talking to your backend server MUCH easier and more reliable!
*/

export default {
    getUsers,
    createUser,
    getDevices,
    setupAuthentication
};
