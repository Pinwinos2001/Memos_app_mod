document.addEventListener("DOMContentLoaded", () => {
  // Smooth navigation to Memos App
  const ctaButtons = document.querySelectorAll(".cta-button")

  ctaButtons.forEach((button) => {
    button.addEventListener("click", (e) => {
      // Optional: Add analytics or other tracking here
      console.log("Navegando a Memos App")
    })
  })

  // Navbar brand click to home
  const navbarBrand = document.querySelector(".navbar-brand")
  navbarBrand.addEventListener("click", () => {
    window.location.href = "./"
  })

  // Footer links functionality
  const footerLinks = document.querySelectorAll(".footer-link")
  footerLinks.forEach((link) => {
    link.addEventListener("click", function (e) {
      if (this.getAttribute("href") === "#") {
        e.preventDefault()
        console.log("Enlace no disponible aún")
      }
    })
  })
})

// Agregar interactividad visual a botones
document.addEventListener("DOMContentLoaded", () => {
  const buttons = document.querySelectorAll(".cta-button")

  buttons.forEach((button) => {
    button.addEventListener("mouseenter", function () {
      this.style.transform = "translateY(-2px)"
    })

    button.addEventListener("mouseleave", function () {
      this.style.transform = "translateY(0)"
    })
  })
})
