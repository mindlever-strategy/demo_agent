const API_BASE = window.location.origin;

document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("signupForm");
    const nameInput = document.getElementById("name");
    const emailInput = document.getElementById("email");
    const passwordInput = document.getElementById("password");
    const confirmPasswordInput = document.getElementById("confirmPassword");
    const errorEl = document.getElementById("error");

    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        errorEl.textContent = "";

        const name = nameInput.value.trim();
        const email = emailInput.value.trim();
        const password = passwordInput.value.trim();
        const confirmPassword = confirmPasswordInput.value.trim();

        if (!name || !email || !password || !confirmPassword) {
            errorEl.textContent = "Please fill in all fields.";
            return;
        }

        if (password !== confirmPassword) {
            errorEl.textContent = "Passwords do not match.";
            return;
        }

        if (password.length < 4) {
            errorEl.textContent = "Password must be at least 4 characters.";
            return;
        }

        const btn = form.querySelector(".btn-login");
        btn.textContent = "Creating account...";
        btn.disabled = true;

        try {
            const res = await fetch(`${API_BASE}/api/signup`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ name, email, password }),
            });

            if (!res.ok) {
                const data = await res.json();
                errorEl.textContent = data.detail || "Signup failed.";
                btn.textContent = "Create Account";
                btn.disabled = false;
                return;
            }

            const data = await res.json();
            sessionStorage.setItem("user", JSON.stringify(data));
            btn.textContent = "Success!";
            setTimeout(() => {
                window.location.href = "chat.html";
            }, 300);
        } catch (err) {
            errorEl.textContent = "Connection error. Is the server running?";
            btn.textContent = "Create Account";
            btn.disabled = false;
        }
    });
});
