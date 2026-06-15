const API_BASE = window.location.origin;

document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("loginForm");
    const emailInput = document.getElementById("email");
    const passwordInput = document.getElementById("password");
    const errorEl = document.getElementById("error");

    const chips = document.querySelectorAll(".chip");
    chips.forEach(chip => {
        chip.addEventListener("click", () => {
            emailInput.value = chip.dataset.email;
            passwordInput.value = chip.dataset.password;
            errorEl.textContent = "";
            emailInput.style.borderColor = "var(--accent)";
            passwordInput.style.borderColor = "var(--accent)";
            setTimeout(() => {
                emailInput.style.borderColor = "";
                passwordInput.style.borderColor = "";
            }, 600);
        });
    });

    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        errorEl.textContent = "";

        const email = emailInput.value.trim();
        const password = passwordInput.value.trim();

        if (!email || !password) {
            errorEl.textContent = "Please fill in all fields.";
            return;
        }

        const btn = form.querySelector(".btn-login");
        btn.textContent = "Logging in...";
        btn.disabled = true;

        try {
            const res = await fetch(`${API_BASE}/api/login`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, password }),
            });

            if (!res.ok) {
                let message = "Login failed.";
                try {
                    const data = await res.json();
                    message = data.detail || message;
                } catch {
                    message = `Server error (${res.status}). Try again in a moment.`;
                }
                errorEl.textContent = message;
                btn.textContent = "Login";
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
            btn.textContent = "Login";
            btn.disabled = false;
        }
    });
});
