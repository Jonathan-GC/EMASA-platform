// 🚀 PRACTICAL EXAMPLES: How to actually use the API class in your Vue components
import API from '../api.js';

// =======================================================================
// 🔧 STEP 1: Setup (do this once when your app starts)
// =======================================================================

export function setupAPIInterceptors() {
    console.log('🔧 Setting up API interceptors...');

    // 🔑 Automatically add authentication token to every request
    API.addRequestInterceptor(async (config) => {
        const token = localStorage.getItem('authToken');
        if (token) {
            config.headers = {
                ...config.headers,
                'Authorization': `Bearer ${token}`
            };
            console.log('🔑 Added auth token to request');
        }
        return config;
    });

    // 🔄 Handle expired tokens automatically
    API.addResponseInterceptor(async (response) => {
        if (response.status === 401) {
            console.log('🔄 Token expired, redirecting to login...');
            localStorage.removeItem('authToken');
            window.location.href = '/login';
        }
        return response;
    });
}

// =======================================================================
// 📱 STEP 2: Use in your Vue components (real examples)
// =======================================================================

// Example: Load users in a Vue component
export function useUsers() {
    const users = ref([]);
    const loading = ref(false);
    const error = ref(null);

    const loadUsers = async () => {
        loading.value = true;
        error.value = null;

        try {
            // 🎯 This is all you need! The API class handles everything else
            users.value = await API.get(API.USER);
            console.log('✅ Users loaded successfully');
        } catch (err) {
            error.value = 'Could not load users. Please try again.';
            console.error('❌ Error loading users:', err.message);
        } finally {
            loading.value = false;
        }
    };

    return { users, loading, error, loadUsers };
}

// Example: Create a new device
export async function createDevice(deviceData) {
    try {
        // 🎯 Simple API call with timeout
        const newDevice = await API.post(API.DEVICE, deviceData, {}, { timeout: 10000 });

        console.log('✅ Device created:', newDevice);
        return { success: true, device: newDevice };

    } catch (error) {
        console.error('❌ Failed to create device:', error.message);

        // 🛡️ User-friendly error messages
        if (error.message.includes('422')) {
            return { success: false, message: 'Please check your device information' };
        } else if (error.message.includes('timeout')) {
            return { success: false, message: 'Request took too long. Please try again.' };
        } else {
            return { success: false, message: 'Could not create device. Please try again.' };
        }
    }
}

// Example: Get workspace data  
export async function getWorkspaceData(workspaceId) {
    try {
        const workspace = await API.get(`${API.WORKSPACE}${workspaceId}/`);
        return workspace;
    } catch (error) {
        if (error.message.includes('404')) {
            throw new Error('Workspace not found');
        } else if (error.message.includes('403')) {
            throw new Error('You do not have access to this workspace');
        }
        throw error;
    }
}

// =======================================================================
// 🎭 STEP 3: Use in a complete Vue component
// =======================================================================

export const DeviceListComponent = {
    setup() {
        const devices = ref([]);
        const loading = ref(false);
        const error = ref(null);

        // 📱 Load devices when component mounts
        const loadDevices = async () => {
            loading.value = true;
            error.value = null;

            try {
                // 🎯 One simple line to get all devices!
                devices.value = await API.get(API.DEVICE);

            } catch (err) {
                // 🛡️ Show user-friendly error message
                if (err.message.includes('403')) {
                    error.value = 'You do not have permission to view devices';
                } else if (err.message.includes('500')) {
                    error.value = 'Server error. Please contact support.';
                } else {
                    error.value = 'Could not load devices. Please try again.';
                }
            } finally {
                loading.value = false;
            }
        };

        // 🗑️ Delete a device
        const deleteDevice = async (deviceId) => {
            try {
                await API.delete(`${API.DEVICE}${deviceId}/`);
                // Remove from local list
                devices.value = devices.value.filter(d => d.id !== deviceId);
                console.log('✅ Device deleted successfully');

            } catch (error) {
                console.error('❌ Failed to delete device:', error.message);
                alert('Could not delete device. Please try again.');
            }
        };

        // Load devices when component mounts
        onMounted(() => {
            loadDevices();
        });

        return {
            devices,
            loading,
            error,
            loadDevices,
            deleteDevice
        };
    }
};

// =======================================================================
// 💡 SUMMARY: What you need to remember
// =======================================================================

/*
1. 🔧 Setup interceptors once when your app starts: setupAPIInterceptors()

2. 🎯 Use simple API calls in your components:
   - API.get(API.USER) → Get users
   - API.post(API.DEVICE, data) → Create device  
   - API.put(API.WORKSPACE + id, data) → Update workspace
   - API.delete(API.DEVICE + id) → Delete device

3. 🛡️ Handle errors with try/catch and show user-friendly messages

4. ⏰ Add timeout for slow requests: API.get(endpoint, {}, { timeout: 5000 })

That's it! The API class handles all the complex stuff automatically. 🎉
*/