// Login form validation
document.addEventListener("DOMContentLoaded", function () {
  const loginForm = document.getElementById("loginForm");
  const userNameInput = document.getElementById("user-name");
  const passwordInput = document.getElementById("password");
  const userNameError = document.getElementById("user-name-error");
  const passwordError = document.getElementById("password-error");

  // Clear error messages when user starts typing
  userNameInput.addEventListener("input", function () {
    userNameError.textContent = "";
    userNameInput.classList.remove("is-invalid");
  });

  passwordInput.addEventListener("input", function () {
    passwordError.textContent = "";
    passwordInput.classList.remove("is-invalid");
  });

  // Form submission validation
  if (loginForm) {
    loginForm.addEventListener("submit", function (e) {
      let isValid = true;

      // Reset previous errors
      userNameError.textContent = "";
      passwordError.textContent = "";
      userNameInput.classList.remove("is-invalid");
      passwordInput.classList.remove("is-invalid");

      // Validate username
      const userName = userNameInput.value.trim();
      if (!userName) {
        userNameError.textContent = "Vui lòng nhập tên người dùng";
        userNameInput.classList.add("is-invalid");
        isValid = false;
      } 
      // else if (userName.length < 3) {
      //   userNameError.textContent = "Tên người dùng phải có ít nhất 3 ký tự";
      //   userNameInput.classList.add("is-invalid");
      //   isValid = false;
      // }

      // Validate password
      const password = passwordInput.value;
      if (!password) {
        passwordError.textContent = "Vui lòng nhập mật khẩu";
        passwordInput.classList.add("is-invalid");
        isValid = false;
      } 
      // else if (password.length < 6) {
      //   passwordError.textContent = "Mật khẩu phải có ít nhất 6 ký tự";
      //   passwordInput.classList.add("is-invalid");
      //   isValid = false;
      // }

      if (!isValid) {
        e.preventDefault();
      }
    });
  }
});
