(() => {
  const createValidationAlert = (form, message) => {
    const existing = form.parentElement?.querySelector("[data-validation-generated='true']");
    if (existing) {
      existing.remove();
    }

    const stack = document.createElement("div");
    stack.className = form.dataset.validationStackClass || "flash-stack";
    stack.dataset.validationGenerated = "true";

    const alert = document.createElement("div");
    alert.className = form.dataset.validationAlertClass || "flash-message";
    alert.dataset.flashMessage = "true";

    const text = document.createElement("span");
    text.className = "flash-message__text";
    text.textContent = message;

    const button = document.createElement("button");
    button.type = "button";
    button.className = "flash-message__close";
    button.setAttribute("aria-label", "Fechar notificação");
    button.dataset.flashClose = "true";
    button.innerHTML = "&times;";

    alert.appendChild(text);
    alert.appendChild(button);
    stack.appendChild(alert);
    form.insertAdjacentElement("beforebegin", stack);

    if (window.EasySportFlashMessages?.enhanceFlashMessage) {
      window.EasySportFlashMessages.enhanceFlashMessage(alert);
    }
  };

  document.querySelectorAll("form[data-custom-validation='true']").forEach((form) => {
    form.setAttribute("novalidate", "novalidate");

    form.addEventListener("submit", (event) => {
      const invalidField = form.querySelector(":invalid");

      if (!invalidField) {
        return;
      }

      event.preventDefault();
      createValidationAlert(form, invalidField.validationMessage);
      invalidField.focus();
    });

    form.querySelectorAll("input, select, textarea").forEach((field) => {
      field.addEventListener("input", () => {
        const generated = form.parentElement?.querySelector("[data-validation-generated='true']");
        if (generated && field.validity.valid) {
          generated.remove();
        }
      });
    });
  });
})();
