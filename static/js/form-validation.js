(() => {
  const getFieldLabel = (field) => {
    const explicitLabel = field.dataset.label?.trim();
    if (explicitLabel) {
      return explicitLabel;
    }

    const wrapperLabel = field.closest("label");
    const wrapperText = wrapperLabel?.querySelector("span")?.textContent?.trim();
    if (wrapperText) {
      return wrapperText;
    }

    if (field.id) {
      const externalLabel = document.querySelector(`label[for="${field.id}"]`);
      const externalText = externalLabel?.textContent?.trim();
      if (externalText) {
        return externalText;
      }
    }

    return field.name || "campo";
  };

  const getValidationMessage = (field) => {
    const label = getFieldLabel(field);

    if (field.validity.customError && field.validationMessage) {
      return field.validationMessage;
    }

    if (field.validity.valueMissing) {
      return `Preenche o campo "${label}".`;
    }

    if (field.validity.typeMismatch) {
      if (field.type === "email") {
        return "Introduz um email valido.";
      }

      return `Verifica o campo "${label}".`;
    }

    if (field.validity.patternMismatch) {
      return `O valor introduzido em "${label}" nao e valido.`;
    }

    if (field.validity.tooShort || field.validity.tooLong) {
      return `O campo "${label}" nao tem o tamanho esperado.`;
    }

    if (field.validity.rangeUnderflow || field.validity.rangeOverflow) {
      return `O valor introduzido em "${label}" esta fora do intervalo permitido.`;
    }

    return `Verifica o campo "${label}".`;
  };

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
      createValidationAlert(form, getValidationMessage(invalidField));
      invalidField.focus();
    });

    form.querySelectorAll("input, select, textarea").forEach((field) => {
      field.addEventListener("input", () => {
        const generated = form.parentElement?.querySelector("[data-validation-generated='true']");
        if (generated && field.validity.valid) {
          generated.remove();
        }

        field.classList.toggle("is-invalid", !field.validity.valid);
        field.setAttribute("aria-invalid", String(!field.validity.valid));
      });
    });
  });
})();
