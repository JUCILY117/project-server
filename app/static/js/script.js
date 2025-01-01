function decodeToken(token) {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    return payload;
  } catch (error) {
    console.error("Failed to decode token:", error);
    return null;
  }
}

function isTokenExpired(token) {
  const decodedToken = decodeJwt(token);
  const currentTime = Date.now() / 1000;
  return decodedToken.exp < currentTime;
}

function decodeJwt(token) {
  const payload = token.split('.')[1];
  const decoded = atob(payload);
  return JSON.parse(decoded);
}


function logout() {
  localStorage.removeItem('authToken');
  alert('Your session has expired. Please log in again.');
  document.getElementById('project-container').style.display = 'none';
  document.getElementById('login-container').style.display = 'block';
}

document.addEventListener('DOMContentLoaded', () => {
  const token = localStorage.getItem('authToken');
  if (!token || isTokenExpired(token)) {
    logout();
  } else {
    document.getElementById('login-container').style.display = 'none';
    document.getElementById('project-container').style.display = 'block';
  }
});

document.getElementById('login-form').addEventListener('submit', async function (event) {
  event.preventDefault();

  const credentials = {
    username: document.getElementById('username').value,
    password: document.getElementById('password').value,
  };
  const baseURL = window.location.origin;

  try {
    const response = await fetch(`${baseURL}/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(credentials),
    });

    const result = await response.json();
    const responseElement = document.getElementById('login-response');

    if (result.token) {
      localStorage.setItem('authToken', result.token);

      responseElement.textContent = 'Login successful!';
      responseElement.classList.add('success');
      responseElement.classList.remove('error');

      document.getElementById('login-container').style.display = 'none';
      document.getElementById('project-container').style.display = 'block';
    } else {
      responseElement.textContent = result.error || 'Login failed.';
      responseElement.classList.add('error');
      responseElement.classList.remove('success');
    }
  } catch (error) {
    console.error(error);
    const responseElement = document.getElementById('login-response');
    responseElement.textContent = 'An error occurred. Please try again.';
    responseElement.classList.add('error');
    responseElement.classList.remove('success');
  }
});

document.getElementById('project-form').addEventListener('submit', async function (event) {
  event.preventDefault();

  const baseURL = window.location.origin;

  const formData = new FormData();
  formData.append('title', document.getElementById('title').value);
  formData.append('description', document.getElementById('description').value);
  formData.append('github_url', document.getElementById('github_url').value);
  formData.append('website_url', document.getElementById('website_url').value);
  formData.append('image', document.getElementById('screenshot').files[0]);

  try {
    const token = localStorage.getItem('authToken');
    if (!token || isTokenExpired(token)) {
      logout();
      return;
    }

    const response = await fetch(`${baseURL}/add-project`, {
      method: 'POST',
      headers: {
        Authorization: token,
      },
      body: formData,
    });

    const result = await response.json();
    const responseElement = document.getElementById('project-response');

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
    const responseElement = document.getElementById('project-response');
    responseElement.textContent = 'An error occurred. Please try again.';
    responseElement.classList.add('error');
    responseElement.classList.remove('success');
  }
});

document.getElementById('toggle-section').addEventListener('click', function () {
  const addProjectContainer = document.getElementById('project-container');
  const manageProjectsContainer = document.getElementById('manage-projects-container');
  const toggleButton = document.getElementById('toggle-section');

  if (addProjectContainer.style.display === 'none') {
    addProjectContainer.style.display = 'block';
    manageProjectsContainer.style.display = 'none';
    toggleButton.textContent = 'Switch to Manage Projects';
  } else {
    addProjectContainer.style.display = 'none';
    manageProjectsContainer.style.display = 'block';
    toggleButton.textContent = 'Switch to Add New Project';
    loadProjects();
  }
});

async function loadProjects() {
  const token = localStorage.getItem('authToken');
  if (!token || isTokenExpired(token)) {
    logout();
    return;
  }

  try {
    const baseURL = window.location.origin;
    const response = await fetch(`${baseURL}/projects`, {
      method: 'GET',
      headers: {
        Authorization: token,
      },
    });
    const result = await response.json();

    const projectList = document.getElementById('project-list');
    projectList.innerHTML = '';

    if (result.projects) {
      result.projects.forEach((project) => {
        const projectElement = document.createElement('div');
        projectElement.classList.add('project-item');
        projectElement.innerHTML = `
          <h3>${project.title}</h3>
          <p>${project.description}</p>
          <img src="${project.image_url}" alt="${project.title}" class="project-image">
          <a href="${project.github_url}" target="_blank">GitHub</a> | 
          <a href="${project.website_url}" target="_blank">Website</a>
          <button onclick="editProject('${project._id}')">Edit</button>
          <button onclick="deleteProject('${project._id}')">Delete</button>
        `;
        projectList.appendChild(projectElement);
      });
    }
  } catch (error) {
    console.error('Failed to load projects:', error);
  }
}

async function editProject(projectId) {
  const newTitle = prompt('Enter new title:');
  const newDescription = prompt('Enter new description:');
  const newGithubUrl = prompt('Enter new GitHub URL:');
  const newWebsiteUrl = prompt('Enter new Website URL:');
  const newImage = document.getElementById('screenshot').files[0];
  const token = localStorage.getItem('authToken');

  if (!newTitle && !newDescription && !newGithubUrl && !newWebsiteUrl && !newImage) {
    return alert('No changes detected.');
  }

  const formData = new FormData();

  if (newTitle) formData.append('title', newTitle);
  if (newDescription) formData.append('description', newDescription);
  if (newGithubUrl) formData.append('github_url', newGithubUrl);
  if (newWebsiteUrl) formData.append('website_url', newWebsiteUrl);
  if (newImage) {
    formData.append('image', newImage);
  }

  try {
    const baseURL = window.location.origin;
    const response = await fetch(`${baseURL}/update-project/${projectId}`, {
      method: 'PUT',
      headers: {
        'Authorization': token,
      },
      body: formData,
    });

    const result = await response.json();
    if (result.message) {
      alert(result.message);
      loadProjects();
    } else {
      alert(result.error || 'Failed to update project.');
    }
  } catch (error) {
    console.error('Failed to edit project:', error);
  }
}

async function deleteProject(projectId) {
  const token = localStorage.getItem('authToken');

  if (!confirm('Are you sure you want to delete this project?')) return;

  try {
    const baseURL = window.location.origin;
    const response = await fetch(`${baseURL}/delete-project/${projectId}`, {
      method: 'DELETE',
      headers: {
        Authorization: token,
      },
    });

    const result = await response.json();
    if (result.message) {
      alert(result.message);
      loadProjects();
    } else {
      alert(result.error || 'Failed to delete project.');
    }
  } catch (error) {
    console.error('Failed to delete project:', error);
  }
}
