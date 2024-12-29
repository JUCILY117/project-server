// Login Form Submission
document.getElementById('login-form').addEventListener('submit', async function (event) {
    event.preventDefault();
  
    const credentials = {
      username: document.getElementById('username').value,
      password: document.getElementById('password').value,
    };
  
    try {
      const response = await fetch('http://localhost:5000/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(credentials),
      });
  
      const result = await response.json();
      const responseElement = document.getElementById('response');
  
      if (result.message) {
        localStorage.setItem('authToken', result.token); // Store token in localStorage
        document.getElementById('login-container').style.display = 'none';
        document.getElementById('project-container').style.display = 'block';
      } else {
        responseElement.textContent = result.error || 'Login failed.';
        responseElement.classList.add('error');
      }
    } catch (error) {
      console.error(error);
      const responseElement = document.getElementById('response');
      responseElement.textContent = 'An error occurred. Please try again.';
      responseElement.classList.add('error');
    }
  });
  
  // Add Project Form Submission
  document.getElementById('project-form').addEventListener('submit', async function (event) {
    event.preventDefault();
  
    const formData = new FormData();
    formData.append('title', document.getElementById('title').value);
    formData.append('description', document.getElementById('description').value);
    formData.append('github_url', document.getElementById('github_url').value);
    formData.append('website_url', document.getElementById('website_url').value);
    formData.append('image', document.getElementById('screenshot').files[0]);
  
    try {
      const token = localStorage.getItem('authToken');
      if (!token) {
        alert('You are not authenticated. Please log in again.');
        window.location.reload();
        return;
      }
  
      const response = await fetch('http://localhost:5000/add-project', {
        method: 'POST',
        headers: {
          Authorization: token, // Pass the token in the headers
        },
        body: formData,
      });
  
      const result = await response.json();
      const responseElement = document.getElementById('response');
  
      if (result.message) {
        responseElement.textContent = result.message;
        responseElement.classList.add('success');
        responseElement.classList.remove('error');
      } else if (result.error) {
        responseElement.textContent = result.error;
        responseElement.classList.add('error');
        responseElement.classList.remove('success');
      }
    } catch (error) {
      console.error(error);
      const responseElement = document.getElementById('response');
      responseElement.textContent = 'An error occurred. Please try again.';
      responseElement.classList.add('error');
      responseElement.classList.remove('success');
    }
  });
  
  // Check if Authenticated on Load
  document.addEventListener('DOMContentLoaded', () => {
    const token = localStorage.getItem('authToken');
    if (token) {
      document.getElementById('login-container').style.display = 'none';
      document.getElementById('project-container').style.display = 'block';
    } else {
      document.getElementById('login-container').style.display = 'block';
      document.getElementById('project-container').style.display = 'none';
    }
  });
  