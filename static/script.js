// Check if user is logged in
const user = sessionStorage.getItem('user');
const role = sessionStorage.getItem('role');

if (!user) {
    window.location.href = '/';
}

// Display user info
document.getElementById('user-display').textContent = `${user} (${role})`;

// Show appropriate panel based on role
if (role === 'admin') {
    document.getElementById('admin-panel').style.display = 'block';
} else {
    document.getElementById('user-panel').style.display = 'block';
}

// Logout functionality
document.getElementById('logoutBtn').addEventListener('click', () => {
    sessionStorage.clear();
    window.location.href = '/';
});

// Load data info on page load
loadDataInfo();

// Admin: Upload CSV to S3
document.getElementById('uploadBtn')?.addEventListener('click', async () => {
    const fileInput = document.getElementById('csvFile');
    const file = fileInput.files[0];
    
    if (!file) {
        alert('Please select a CSV file');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    
    const statusSpan = document.getElementById('upload-status');
    statusSpan.textContent = 'Uploading...';
    
    try {
        const response = await fetch('/upload-csv', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok) {
            statusSpan.textContent = '✓ Uploaded successfully!';
            addSystemMessage(`Data loaded: ${data.rows} rows × ${data.columns} columns`);
            loadDataInfo();
            fileInput.value = '';
            
            setTimeout(() => {
                statusSpan.textContent = '';
            }, 3000);
        } else {
            statusSpan.textContent = '✗ Upload failed';
            alert(data.detail || 'Upload failed');
        }
    } catch (error) {
        statusSpan.textContent = '✗ Upload failed';
        alert('Upload failed: ' + error.message);
    }
});

// Admin: Load from URL
document.getElementById('loadS3Btn')?.addEventListener('click', async () => {
    await loadFromURL('s3Url');
});

// User: Load from URL
document.getElementById('userLoadS3Btn')?.addEventListener('click', async () => {
    await loadFromURL('userS3Url');
});

async function loadFromURL(inputId) {
    const urlInput = document.getElementById(inputId);
    const fileUrl = urlInput.value.trim();
    
    if (!fileUrl) {
        alert('Please enter a file URL');
        return;
    }
    
    try {
        addSystemMessage('Loading data from URL...');
        
        const response = await fetch('/load-from-url', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ file_url: fileUrl })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            addSystemMessage(`✓ Data loaded: ${data.rows} rows × ${data.columns} columns`);
            loadDataInfo();
            urlInput.value = '';
        } else {
            addSystemMessage('✗ Failed to load data from URL');
            alert(data.detail || 'Failed to load data');
        }
    } catch (error) {
        addSystemMessage('✗ Failed to load data from URL');
        alert('Error: ' + error.message);
    }
}

async function loadDataInfo() {
    try {
        const response = await fetch('/health');
        const data = await response.json();
        
        document.getElementById('data-info').textContent = data.data_shape;
    } catch (error) {
        console.error('Failed to load data info:', error);
    }
}

// Chat functionality
const chatMessages = document.getElementById('chatMessages');
const chatInput = document.getElementById('chatInput');
const sendBtn = document.getElementById('sendBtn');

chatInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

sendBtn.addEventListener('click', sendMessage);

async function sendMessage() {
    const question = chatInput.value.trim();
    
    if (!question) return;
    
    // Add user message
    addMessage(question, 'user');
    chatInput.value = '';
    
    // Disable input while processing
    sendBtn.disabled = true;
    chatInput.disabled = true;
    
    // Add loading message
    const loadingId = addLoadingMessage();
    
    try {
        const response = await fetch('/ask', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ question })
        });
        
        const data = await response.json();
        
        // Remove loading message
        removeLoadingMessage(loadingId);
        
        if (response.ok) {
            addMessage(data.answer, 'assistant');
        } else {
            addMessage(`Error: ${data.detail || 'Failed to get answer'}`, 'assistant');
        }
    } catch (error) {
        removeLoadingMessage(loadingId);
        addMessage(`Error: ${error.message}`, 'assistant');
    } finally {
        sendBtn.disabled = false;
        chatInput.disabled = false;
        chatInput.focus();
    }
}

function addMessage(text, type) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.textContent = text;
    
    messageDiv.appendChild(contentDiv);
    chatMessages.appendChild(messageDiv);
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function addSystemMessage(text) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'system-message';
    messageDiv.textContent = text;
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function addLoadingMessage() {
    const id = 'loading-' + Date.now();
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant loading';
    messageDiv.id = id;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.textContent = 'Thinking...';
    
    messageDiv.appendChild(contentDiv);
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    return id;
}

function removeLoadingMessage(id) {
    const loadingDiv = document.getElementById(id);
    if (loadingDiv) {
        loadingDiv.remove();
    }
}
