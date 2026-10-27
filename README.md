# 🛡️ Secure AirShare LAN

A lightning-fast, 100% offline, and secure local file-sharing tool built with Python. Transfer files instantly between your PC and phone over Wi-Fi without any cables, internet, or third-party apps.

---

## ✨ Features

- **100% Offline & Independent:** Works entirely on your local Wi-Fi network. No internet connection required.
- **Cryptographic Token Security:** Protected by a secure dynamic URL token (`?auth_token`) to prevent unauthorized access from other devices on the same network.
- **Modern Glassmorphic UI:** Sleek, dark-themed responsive web interface with drag-and-drop file upload support.
- **Terminal QR Code:** Automatically generates an interactive QR code in your terminal for instant scanning and connection via phone.
- **Isolated Storage:** Restricts all operations strictly to the `shared_files` folder for absolute system privacy.
- **Zero Dependencies for Core Server:** Uses Python's standard library for the core HTTP server.