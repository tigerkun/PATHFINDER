function submitForm(e) {
    e.preventDefault();

    const username = document.getElementById('username').value.trim();
    const cgpa = document.getElementById('cgpa').value;
    const tier = document.getElementById('tier').value;
    const target = document.getElementById('target').value;
    const status = document.getElementById('status').value;

    const err = document.getElementById('errorMsg');
    err.style.display = 'none';

    if (!username) {
        err.textContent = 'Please enter a GitHub username.';
        err.style.display = 'block';
        return;
    }

    if (cgpa < 0 || cgpa > 10) {
        err.textContent = 'CGPA must be between 0 and 10.';
        err.style.display = 'block';
        return;
    }

    const btn = document.getElementById('submitBtn');
    btn.disabled = true;
    btn.innerHTML = '<span>⏳ Redirecting...</span>';

    const params = new URLSearchParams({ username, cgpa, tier, target, status });
    window.location.href = `/result?${params.toString()}`;
}

const form = document.getElementById('form');
if (form) {
    form.addEventListener('submit', submitForm);
}
