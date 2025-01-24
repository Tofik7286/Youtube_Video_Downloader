window.onloadTurnstileCallback = function () {
    turnstile.render("#myWidget", {
      sitekey: "0x4AAAAAAA6H5LB8vMilaJ2I",
      callback: function (token) {
        console.log(`Challenge Success ${token}`);
        setTimeout(() => {
            document.querySelector(".captchaContainer").style.display = "flex";
            document.getElementById("myWidget").style.display = "none";
        }, 2000);
      },
    });
  };