(() => {
  const form = document.querySelector(".checkout-form[data-custom-validation='true']");

  if (!form) {
    return;
  }

  const cardField = form.querySelector("#numeroCartao");
  const expiryField = form.querySelector("#validade");
  const cvvField = form.querySelector("#cvv");

  if (!cardField || !expiryField || !cvvField) {
    return;
  }

  const digitsOnly = (value) => value.replace(/\D/g, "");

  const formatCardNumber = (value) => {
    const digits = digitsOnly(value).slice(0, 19);
    return digits.replace(/(\d{4})(?=\d)/g, "$1 ").trim();
  };

  const formatExpiry = (value) => {
    const digits = digitsOnly(value).slice(0, 4);

    if (!digits) {
      return "";
    }

    if (digits.length === 1) {
      return Number.parseInt(digits, 10) > 1 ? `0${digits}` : digits;
    }

    if (digits.length <= 2) {
      return digits;
    }

    return `${digits.slice(0, 2)}/${digits.slice(2)}`;
  };

  const setFieldState = (field, isValid) => {
    field.classList.toggle("is-invalid", !isValid);
    field.setAttribute("aria-invalid", String(!isValid));
  };

  const validateCardField = () => {
    const digits = digitsOnly(cardField.value);
    let message = "";

    if (digits && (digits.length < 12 || digits.length > 19)) {
      message = "Introduz um numero de cartao valido com 12 a 19 digitos.";
    }

    cardField.setCustomValidity(message);
    setFieldState(cardField, !message);
    return !message;
  };

  const validateExpiryField = () => {
    const value = expiryField.value.trim();
    let message = "";

    if (value) {
      const match = value.match(/^(\d{2})\/(\d{2})$/);

      if (!match) {
        message = "Introduz a validade no formato MM/AA.";
      } else {
        const month = Number.parseInt(match[1], 10);

        if (month < 1 || month > 12) {
          message = "Introduz um mes de validade entre 01 e 12.";
        }
      }
    }

    expiryField.setCustomValidity(message);
    setFieldState(expiryField, !message);
    return !message;
  };

  const validateCvvField = () => {
    const digits = digitsOnly(cvvField.value);
    let message = "";

    if (digits && !/^\d{3,4}$/.test(digits)) {
      message = "Introduz um CVV com 3 ou 4 digitos.";
    }

    cvvField.setCustomValidity(message);
    setFieldState(cvvField, !message);
    return !message;
  };

  cardField.addEventListener("input", () => {
    cardField.value = formatCardNumber(cardField.value);
    validateCardField();
  });

  expiryField.addEventListener("input", () => {
    expiryField.value = formatExpiry(expiryField.value);
    validateExpiryField();
  });

  cvvField.addEventListener("input", () => {
    cvvField.value = digitsOnly(cvvField.value).slice(0, 4);
    validateCvvField();
  });

  [cardField, expiryField, cvvField].forEach((field) => {
    field.addEventListener("blur", () => {
      if (field === cardField) {
        validateCardField();
      } else if (field === expiryField) {
        validateExpiryField();
      } else {
        validateCvvField();
      }
    });
  });

  form.addEventListener("submit", () => {
    validateCardField();
    validateExpiryField();
    validateCvvField();
  });
})();
