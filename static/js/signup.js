document.addEventListener("DOMContentLoaded", function () {
  const phoneInput = document.querySelector("#phone");
  const fullPhoneInput = document.querySelector("#full_phone");
  const form = document.querySelector(".login-form");
  const emailInput = document.querySelector("input[name='email']");
  const passwordInput = document.querySelector("input[name='password']");
  const confirmPasswordInput = document.querySelector("input[name='confirm_password']");

  // ===== Initialize intl-tel-input =====
  let iti = null;
  if (phoneInput && fullPhoneInput && form) {
    iti = window.intlTelInput(phoneInput, {
      initialCountry: "ng",
      separateDialCode: true,
      utilsScript:
        "https://cdnjs.cloudflare.com/ajax/libs/intl-tel-input/17.0.19/js/utils.js",
    });

    const updatePhoneValue = () => {
      fullPhoneInput.value = iti.getNumber();
      validatePhone(); // live validation
    };

    phoneInput.addEventListener("input", updatePhoneValue);
  }

  // ===== Utility: show / remove messages =====
  function showError(input, message) {
    removeMessage(input);
    const msg = document.createElement("small");
    msg.className = "text-danger d-block mt-1";
    msg.innerText = message;
    input.parentElement.appendChild(msg);
  }

  function showSuccess(input, message) {
    removeMessage(input);
    const msg = document.createElement("small");
    msg.className = "text-success d-block mt-1";
    msg.innerText = message;
    input.parentElement.appendChild(msg);
  }

  function removeMessage(input) {
    const existing = input.parentElement.querySelector("small");
    if (existing) existing.remove();
  }

  // ===== Validators =====
  function isValidEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  }

  function isValidPassword(password) {
    return /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&#^])[A-Za-z\d@$!%*?&#^]{8,}$/.test(password);
  }

  // ===== Real-time validation functions =====
  function validatePhone() {
    if (!iti) return;
    removeMessage(phoneInput);
    if (phoneInput.value.trim() === "") return;
    if (!iti.isValidNumber()) {
      showError(phoneInput, "❌ Invalid phone number or country code.");
    } else {
      showSuccess(phoneInput, "✅ Valid phone number");
    }
  }

  function validateEmail() {
    removeMessage(emailInput);
    const email = emailInput.value.trim();
    if (email === "") return;
    if (!isValidEmail(email)) {
      showError(emailInput, "❌ Invalid email format.");
    } else {
      showSuccess(emailInput, "✅ Valid email address");
    }
  }

  function validatePassword() {
    removeMessage(passwordInput);
    const password = passwordInput.value;
    if (password === "") return;
    if (!isValidPassword(password)) {
      showError(
        passwordInput,
        "❌ Must contain uppercase, lowercase, number, symbol & ≥8 chars."
      );
    } else {
      showSuccess(passwordInput, "✅ Strong password");
    }
  }

  function validateConfirmPassword() {
    removeMessage(confirmPasswordInput);
    if (confirmPasswordInput.value === "") return;
    if (confirmPasswordInput.value !== passwordInput.value) {
      showError(confirmPasswordInput, "❌ Passwords do not match.");
    } else {
      showSuccess(confirmPasswordInput, "✅ Passwords match");
    }
  }

  // ===== Attach real-time listeners =====
  if (phoneInput) phoneInput.addEventListener("input", validatePhone);
  if (emailInput) emailInput.addEventListener("input", validateEmail);
  if (passwordInput) passwordInput.addEventListener("input", () => {
    validatePassword();
    validateConfirmPassword(); // recheck confirm on password changes
  });
  if (confirmPasswordInput) confirmPasswordInput.addEventListener("input", validateConfirmPassword);

  // ===== PASSWORD VISIBILITY TOGGLE =====
  document.querySelectorAll(".toggle-password").forEach(icon => {
    icon.addEventListener("click", function () {
      const input = document.querySelector(this.getAttribute("toggle"));
      const iconElem = this.querySelector("i");

      if (input.type === "password") {
        input.type = "text";
        iconElem.classList.remove("mdi-eye-off-outline");
        iconElem.classList.add("mdi-eye-outline");
      } else {
        input.type = "password";
        iconElem.classList.remove("mdi-eye-outline");
        iconElem.classList.add("mdi-eye-off-outline");
      }
    });
  });

  // ===== Final Submit Check =====
  if (form) {
    form.addEventListener("submit", function (e) {
      let valid = true;

      // Phone
      if (iti) {
        if (!iti.isValidNumber()) {
          showError(phoneInput, "❌ Invalid phone number or country code.");
          valid = false;
        } else {
          fullPhoneInput.value = iti.getNumber();
        }
      }

      // Email
      if (!isValidEmail(emailInput.value.trim())) {
        showError(emailInput, "❌ Invalid email format.");
        valid = false;
      }

      // Password
      if (!isValidPassword(passwordInput.value)) {
        showError(
          passwordInput,
          "❌ Must contain uppercase, lowercase, number, symbol & ≥8 chars."
        );
        valid = false;
      }

      // Confirm Password
      if (confirmPasswordInput.value !== passwordInput.value) {
        showError(confirmPasswordInput, "❌ Passwords do not match.");
        valid = false;
      }

      if (!valid) e.preventDefault();
    });
  }
});
