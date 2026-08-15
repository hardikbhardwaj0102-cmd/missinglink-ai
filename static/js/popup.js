function showPopup(type, title, message) {

    const overlay = document.getElementById("popupOverlay");
    const icon = document.getElementById("popupIcon");
    const popupTitle = document.getElementById("popupTitle");
    const popupMessage = document.getElementById("popupMessage");

    popupTitle.innerText = title;
    popupMessage.innerText = message;

    if (type === "success") {
        icon.innerHTML = "✅";
        icon.style.color = "#22c55e";
    }
    else if (type === "warning") {
        icon.innerHTML = "⏳";
        icon.style.color = "#facc15";
    }
    else {
        icon.innerHTML = "❌";
        icon.style.color = "#ef4444";
    }

    overlay.classList.add("show");
}

function closePopup() {
    document.getElementById("popupOverlay").classList.remove("show");
}